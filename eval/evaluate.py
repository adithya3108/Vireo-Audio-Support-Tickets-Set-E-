"""How often is the categorisation wrong?

A. Hand-labelled gold sets. Tickets drawn at random from the analysis window and
   labelled from message + note without looking at any model output.
     - gold_labels.csv   (200) development set: errors here were read and fixed.
     - holdout_labels.csv (100) labelled after the classifier was frozen.
   Reported for the bot tag, our classifier and the intake router, with a 95%
   Wilson interval.
B. Operational cross-check on ALL attended tickets: does the team that owns our
   predicted category match the team whose agent actually closed the ticket?

Run:  python -m eval.evaluate   (after python run.py has written outputs/)
"""
import math
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vireo.taxonomy import owner_team  # noqa: E402

SETS = [
    ("A1. Development gold set", ROOT / "eval" / "gold_labels.csv",
     "200 random tickets. Used while building the classifier: two rule fixes were made after reading its "
     "errors, so this number is optimistic."),
    ("A2. Held-out gold set", ROOT / "eval" / "holdout_labels.csv",
     "100 different random tickets, labelled after the classifier was frozen. Scored at freeze: bot tag 66%, "
     "classifier 99% (1 error), intake router 100%. The one error ('one pair of earbuds' hitting the pairing "
     "rule) was then fixed, so the table below - current code - is slightly flattering; quote the at-freeze figure."),
]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def _score_set(tickets, title, path, blurb):
    out = []
    gold = pd.read_csv(path)[["ticket_id", "gold_category"]]
    x = gold.merge(tickets, on="ticket_id", how="inner")
    out.append(f"## {title} ({len(x)} tickets)\n")
    out.append(blurb + "\n")
    out.append("| Labeller | Correct | Accuracy | 95% interval |\n|---|---|---|---|")
    for col, name in [("category", "Chat-bot tag (today)"), ("category_ai", "Our classifier (full ticket)"),
                      ("intake_pred", "Intake router (customer message only)")]:
        k = int((x[col] == x.gold_category).sum())
        lo, hi = wilson(k, len(x))
        out.append(f"| {name} | {k}/{len(x)} | {k/len(x):.1%} | {lo:.1%} - {hi:.1%} |")
    bad = x[x.category_ai != x.gold_category]
    out.append(f"\n### Classifier errors: {len(bad)}\n")
    for _, r in bad.iterrows():
        out.append(f"- {r.ticket_id}: gold {r.gold_category}, predicted {r.category_ai} (via {r.category_source}). "
                   f"Message: {str(r.customer_message)[:110]}")
    return out


def _crosscheck(tickets):
    t = tickets[(tickets.resolver_team.fillna("") != "") & tickets.attended].copy()
    t = t[t.resolver_team != "Escalations & Warranty"]  # Tier 2 takes escalations from every category
    grp = lambda s: s.where(~s.str.contains("Frontline"), "Frontline")
    pred = grp(pd.Series([owner_team(c, ch) for c, ch in zip(t.category_ai, t.channel)], index=t.index))
    bot = grp(pd.Series([owner_team(c, ch) for c, ch in zip(t.category, t.channel)], index=t.index))
    res = grp(t.resolver_team)
    # Only hand-offs are informative: an agent looked at the ticket and moved it to another team.
    # (Tickets closed by the first-assigned team mostly echo the bot's routing, so they would favour the bot.)
    moved = grp(t.assigned_team) != res
    flagged = pred != grp(t.assigned_team)          # we say the bot routed it to the wrong team
    a, b = moved & flagged, moved & ~flagged
    return [
        f"\n## B. Operational cross-check: {int(moved.sum()):,} tickets an agent handed to another team\n",
        "When an agent moves a ticket to another team, that is a human judgement of who owns it, made "
        "without this tool. Two groups:\n",
        f"- **{int(a.sum()):,} hand-offs of tickets we flag as misrouted.** The agent sent it to exactly the team "
        f"our label says owns it in {(pred[a] == res[a]).mean():.1%} of cases.",
        f"- **{int(b.sum()):,} hand-offs of tickets we say were routed correctly.** On reading a sample, these are "
        "mostly correct tickets passed to a team that does not own them (e.g. a double charge sent from Billing to "
        "Returns Desk, a refund query sent to Billing). They are not classification errors; they are a second, "
        "smaller source of avoidable transfers that routing alone will not fix.",
        f"\nFor reference, the bot's tag names the destination team in {(bot[moved] == res[moved]).mean():.0%} of hand-offs, "
        "by construction: these are tickets that left the bot's chosen team.",
        "\n## Per-category detail (classifier vs development gold set)\n```",
        classification_report(*_dev_pairs(tickets), zero_division=0),
        "```",
    ]


def _dev_pairs(tickets):
    x = pd.read_csv(SETS[0][1]).merge(tickets, on="ticket_id")
    return x.gold_category, x.category_ai


def evaluate(tickets):
    out = []
    for title, path, blurb in SETS:
        out += _score_set(tickets, title, path, blurb)
    out += _crosscheck(tickets)
    return "\n".join(out)


if __name__ == "__main__":
    t = pd.read_csv(ROOT / "outputs" / "tickets_categorised.csv", dtype=str, keep_default_na=False)
    t["attended"] = t.attended == "True"
    report = evaluate(t)
    (ROOT / "outputs" / "evaluation.md").write_text(report, encoding="utf-8")
    print(report)
