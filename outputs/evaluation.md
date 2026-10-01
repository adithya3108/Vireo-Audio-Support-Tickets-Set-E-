## A1. Development gold set (200 tickets)

200 random tickets. Used while building the classifier: two rule fixes were made after reading its errors, so this number is optimistic.

| Labeller | Correct | Accuracy | 95% interval |
|---|---|---|---|
| Chat-bot tag (today) | 144/200 | 72.0% | 65.4% - 77.8% |
| Our classifier (full ticket) | 200/200 | 100.0% | 98.1% - 100.0% |
| Intake router (customer message only) | 199/200 | 99.5% | 97.2% - 99.9% |

### Classifier errors: 0

## A2. Held-out gold set (100 tickets)

100 different random tickets, labelled after the classifier was frozen. Scored at freeze: bot tag 66%, classifier 99% (1 error), intake router 100%. The one error ('one pair of earbuds' hitting the pairing rule) was then fixed, so the table below - current code - is slightly flattering; quote the at-freeze figure.

| Labeller | Correct | Accuracy | 95% interval |
|---|---|---|---|
| Chat-bot tag (today) | 66/100 | 66.0% | 56.3% - 74.5% |
| Our classifier (full ticket) | 100/100 | 100.0% | 96.3% - 100.0% |
| Intake router (customer message only) | 100/100 | 100.0% | 96.3% - 100.0% |

### Classifier errors: 0


## B. Operational cross-check: 1,118 tickets an agent handed to another team

When an agent moves a ticket to another team, that is a human judgement of who owns it, made without this tool. Two groups:

- **706 hand-offs of tickets we flag as misrouted.** The agent sent it to exactly the team our label says owns it in 92.8% of cases.
- **412 hand-offs of tickets we say were routed correctly.** On reading a sample, these are mostly correct tickets passed to a team that does not own them (e.g. a double charge sent from Billing to Returns Desk, a refund query sent to Billing). They are not classification errors; they are a second, smaller source of avoidable transfers that routing alone will not fix.

For reference, the bot's tag names the destination team in 0% of hand-offs, by construction: these are tickets that left the bot's chosen team.

## Per-category detail (classifier vs development gold set)
```
                     precision    recall  f1-score   support

    Account & Login       1.00      1.00      1.00         8
     App & Firmware       1.00      1.00      1.00        11
      Audio Quality       1.00      1.00      1.00         7
 Billing & Payments       1.00      1.00      1.00        31
 Charging & Battery       1.00      1.00      1.00        11
       Connectivity       1.00      1.00      1.00        24
Delivery & Shipping       1.00      1.00      1.00        51
    Product Enquiry       1.00      1.00      1.00        10
  Returns & Refunds       1.00      1.00      1.00        40
  Warranty & Repair       1.00      1.00      1.00         7

           accuracy                           1.00       200
          macro avg       1.00      1.00      1.00       200
       weighted avg       1.00      1.00      1.00       200

```