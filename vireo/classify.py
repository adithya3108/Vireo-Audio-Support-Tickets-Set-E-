"""Ticket categorisation.

Three layers, cheapest first:
  1. Rules on the agent's closing note: the note records what the agent actually
     fixed ("issue: shipment not received"), so it is the best evidence of what
     the ticket was about.
  2. Rules on the customer message (+ note) when the note has no issue phrase.
  3. A character n-gram model (TF-IDF + logistic regression) trained on the
     tickets that layers 1-2 label with confidence. It fills the gaps and is
     robust to the heavy misspelling in the text. Optional: Claude re-labels
     whatever is still low-confidence (see llm.py).

The same model is also trained on the customer message ONLY. That is the
'intake router': what could be predicted at ticket creation, before any agent
touches it, which is what a better bot would do.
"""
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import make_pipeline

from .taxonomy import match_intents

# Phrases that introduce the agent's diagnosis in the closing note.
_ISSUE_PATTERNS = [
    r"issue:\s*([^.|\n]+)", r"^re:\s*([^|]+)\|", r"^cx:\s*([^|]+)\|", r"reported:\s*([^.|\n]+)",
    r"(?:cx|customer|cust|cuust) (?:says|states|sates|reported|rpeorted|reached out -|contacted re)\s*([^.|\n]+)",
    r"ticket raised for\s*([^.|\n]+)", r"contact re\s*([^.|\n]+)", r"^1\.\s*([^/\n]+)",
]
_ISSUE_RX = [re.compile(p, re.I | re.M) for p in _ISSUE_PATTERNS]


def note_issue(note):
    for rx in _ISSUE_RX:
        m = rx.search(note or "")
        if m:
            return m.group(1).strip()
    return ""


def _vote(hits):
    cats = Counter(c for _, c in hits)
    if not cats:
        return None, 0
    top = cats.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None, 0  # ambiguous
    return top[0][0], top[0][1]


def rule_label(message, note):
    """Return (category, source, confidence) from rules, or (None, 'none', 0)."""
    issue = note_issue(note)
    if issue:
        cat, _ = _vote(match_intents(issue))
        if cat:
            return cat, "note_issue", 0.95
    # No clean diagnosis: vote over message (weight 2) and note (weight 1).
    # v1 weighted the note higher; that let resolution actions in the note
    # ("reverse pkp arranged", "fw update resolved") outvote the actual complaint.
    votes = Counter()
    for _, c in match_intents(message):
        votes[c] += 2
    for _, c in match_intents(note):
        votes[c] += 1
    if votes:
        top = votes.most_common()
        if len(top) == 1 or top[0][1] > top[1][1]:
            conf = 0.8 if top[0][1] >= 2 else 0.6
            return top[0][0], "text_rules", conf
    return None, "none", 0.0


def _model():
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True, lowercase=True),
        LogisticRegression(max_iter=2000, C=4.0),
    )


def categorise(df, seed=0):
    """Add category_ai, category_source, category_conf and intake_pred columns."""
    df = df.copy()
    msg = df["customer_message"].fillna("")
    note = df["agent_notes"].fillna("")
    full = msg + " || " + note

    labels = [rule_label(m, n) for m, n in zip(msg, note)]
    df["rule_cat"] = [l[0] for l in labels]
    df["category_source"] = [l[1] for l in labels]
    df["category_conf"] = [l[2] for l in labels]

    train = df["rule_cat"].notna() & (df["category_conf"] >= 0.8)

    # Full-ticket model: fills tickets rules could not label.
    m_full = _model().fit(full[train], df.loc[train, "rule_cat"])
    proba = m_full.predict_proba(full)
    pred = m_full.classes_[proba.argmax(1)]
    use_model = df["rule_cat"].isna() | (df["category_conf"] < 0.8)
    model_better = use_model & (proba.max(1) > df["category_conf"])
    df["category_ai"] = np.where(model_better, pred, df["rule_cat"])
    df.loc[model_better, "category_source"] = "model"
    df.loc[model_better, "category_conf"] = proba.max(1)[model_better]
    df["category_ai"] = df["category_ai"].fillna("Other")

    # Intake router: customer message only. Out-of-fold predictions so the
    # accuracy we report is not measured on its own training data.
    y = df["category_ai"]
    df["intake_pred"] = cross_val_predict(_model(), msg, y, cv=5)
    m_intake = _model().fit(msg, y)
    return df, m_intake
