# Prompts and AI use

## Tools used

| Tool | Used for |
|---|---|
| **Claude Code** (VS Code extension, model Claude Opus 5.5) | Reading the pack, exploring the data, writing all the code, hand-labelling the gold sets, drafting the docs. One session. |
| **scikit-learn** (TF-IDF + logistic regression) | The classifier that ships. Local, free. |
| **Claude API** (`claude-opus-5`, optional `--llm` path) | Wired in for low-confidence tickets. Not run: no API key in the window. |

## Prompts to the coding assistant

The first prompt, verbatim apart from the pasted brief:

> *[the full Task 1 V2 brief pasted]* — "check all the supporting files and implement whatever is needed"

After it paused, the follow-up prompt:

> "1. continue  2. you draft one [the submission form]  3. do it [clean-machine test]  4. we'll do this [recording] after everything else is done"

Everything else was the assistant working from the pack. The instructions that shaped the work came from the pack itself: the email thread, policy §3–§10, and the README column notes.

## The ticket-labelling prompt (ships in `vireo/llm.py`)

```
You categorise customer-support tickets for Vireo Audio, a consumer audio and wearables brand.

Pick the ONE category that describes what the customer actually needed resolved. Use the
agent's closing note as the strongest evidence of what the problem turned out to be; use the
customer's message when the note is empty or generic ("closed", "sorted", "as discussed").

Rules that matter most:
- "I paid but the order hasn't arrived" is Delivery & Shipping, not Billing & Payments. Billing
  is only for money problems with no delivery question: double charges, payment taken but no
  order created, invoices/GST, coupons/discounts.
- Refund status, return pickups and cancellations are Returns & Refunds.
- Wrong item, damaged in transit and address changes are Delivery & Shipping.
- Repair/RMA status and physical faults such as straps, dead screens or no power are
  Warranty & Repair.
- A resolution action in the note (replacement, refund, firmware update) does not change the
  category; the problem does.

Categories: …11 names…
Customer message: <message>…</message>
Agent closing note: <note>…</note>
```

The output is forced to `{"category": <one of 11>, "reason": str}` with a JSON schema, so the answer is always a valid label.

**Why the prompt says what it says.** Each rule is there because of a real failure mode in the data. The first rule is the bot's own mistake. The last rule is the v1 rules-classifier mistake (see `decisions.md`).

## Versions

| Version | Change | Dev set | Held-out |
|---|---|---|---|
| v1 | Note rules → note-weighted vote → n-gram model | 98.5% | – |
| v2 | Customer message weighted above note actions in the vote | 99.5% | 99% (frozen, then scored) |
| v2.1 | "pair of earbuds" no longer matches the pairing rule | 100% | 100% (not quoted; tuned after seeing) |

## Thrown away

- A plain keyword classifier on customer messages, which was too brittle for the misspellings and Hinglish.
- An LLM-on-everything design: cost and a network dependency for about 1% more coverage.
- A "resolver team = owner team" validation check that turned out to be biased towards the bot.
- A lot-code defect analysis, where the samples per lot were too small.
- A stacked 11-colour monthly chart, replaced by small multiples.

## Cost

- **Claude Code usage:** covered by a Claude Pro subscription (flat monthly fee); this task used about 23% of the weekly allowance.
- **API spend:** Rs 0. The `--llm` path was not run.
- **The shipped tool costs nothing to run.**
