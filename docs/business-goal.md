# Business goal

> **Cut tickets the chat bot routes to the wrong team from 22% to 5% within one quarter of go-live. That is worth about Rs 47,000 a quarter directly, halves the SLA breach rate on the affected tickets (18% → 9%), and removes about 60 tickets a month from Billing's queue that are not Billing's work. Doing this first means the two hires (Rs 9 lakh a year) go to Logistics and Returns Desk, where the load per agent is highest, not to Billing.**

## Where the numbers come from

All figures are measured on Jan–Jun 2026 unless stated. Costs are from support-policy.pdf §3–4. Run `python run.py` to regenerate them.

| Input | Value | Source |
|---|---|---|
| Tickets per quarter | 2,345 | H1 2026 run-rate |
| Misrouted today | 22.4% (525 a quarter) | bot's assigned team ≠ team that owns the classified category (frontline teams treated as one) |
| Misroutes avoided at 5% target | 408 a quarter | (22.4% − 5%) × 2,345 |
| Extra transfers per misroute | 0.26 × Rs 305 = **Rs 79** | helpdesk rows only; transfers are blank on legacy rows |
| Extra breach credits per misroute | 0.095 × Rs 350 = **Rs 33** | 18.3% vs 8.8% breach rate |
| Extra repeat contacts per misroute | 0.015 × Rs 290 = **Rs 4** | same customer and category within 30 days (policy §10) |
| **Cost per misroute** | **≈ Rs 116** | |
| **Saving per quarter** | **≈ Rs 47,000** | 408 × Rs 116 |

## Why 5% and not 0%

The held-out accuracy is 99% on a sample of 100. Live text will be messier than this export, some tickets really do span two teams, and agents also bounce about 400 correctly-routed tickets for other reasons. A target of 5% leaves room for all of that.

## What this number does not include (so it is conservative)

- Billing agent time spent on tickets that are not theirs before they transfer them. The policy's Rs 305 per transfer is meant to cover that re-handling, so it is not added again.
- The customer-experience effect: resolution is 3 hours faster at the median and CSAT is 0.4 points higher.
- The cost of hiring into the wrong team, which is the decision this whole piece exists to support.

## Caveat

The misrouted-vs-correct differences are observational. Misrouted tickets may differ in other ways too; for example, delivery tickets are slower by nature. The number should be read as "about", and the pilot (switch routing on, measure for six weeks) is how to confirm it.
