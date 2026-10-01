**To:** Priya Raman, Head of Customer Experience
**Cc:** Arjun Mehta, Neha Kulkarni, Sameer Qureshi
**From:** Kabir Nanda
**Re:** Where the next two hires should go

---

**Short answer: not Billing. Put the first hire in Logistics now. Fix the chat bot's routing, then place the second hire once the queues show their true size.**

**Why the 22% is misleading.** Your 22% for Billing and 16% for Logistics match the export exactly, but they count the chat bot's tag. The bot picks the tag from its opening question, so "I paid and my order hasn't arrived" gets tagged *Billing* because the customer mentioned paying. We re-read all 11,641 tickets from Jan 2025 to Jun 2026 and categorised each one by what the customer actually needed and what the agent actually fixed. For January to June 2026:

| Team | Share by bot tag | Share by what the ticket was about | Tickets per agent per month |
|---|---|---|---|
| Logistics (5 agents) | 16% | **27%** | **41** |
| Returns Desk (3) | 8% | 13% | 34 |
| Billing (4) | 19% | 14% | 27 |

**43% of Billing's queue is not Billing's work**, about 64 tickets a month. Most of it is delivery problems. Billing's complaint was right, and so was Neha's: Logistics is the team under the most pressure.

**What wrong routing costs.** More than one ticket in five (22%) starts with the wrong team. Compared with tickets that start in the right place, those tickets:
- miss the first-response target twice as often (18% vs 9%). Each miss automatically costs a Rs 350 store credit;
- take nearly three times as long to resolve (median 4.7 hours vs 1.7);
- are transferred three times as often, at Rs 305 per transfer;
- get lower satisfaction scores (3.1 vs 3.5 out of 5).

Billing's own tickets meet the response target as well as any team's. Its poor record comes from the delivery tickets parked in its queue.

**The goal we propose:** *cut tickets routed to the wrong team from 22% to 5% within a quarter of switching the routing on.* That saves about **Rs 47,000 a quarter** in transfers, response credits and repeat contacts. Billing's queue shrinks by about 60 tickets a month, and roughly one customer in five gets an answer hours sooner. The direct saving is modest. The larger gain is putting Rs 9 lakh a year of salary where the work actually is, which answers Arjun's question about fixing process before hiring.

**How.** The tool reads the customer's first message and predicts the right team. On 100 tickets we checked by hand, it matched the correct team 100% of the time, against 66% for today's bot. Sameer's team would call it at ticket creation in place of the bot's tag.

**Recommendation.**
1. **Hire 1 → Logistics, now.** It has the highest load per agent and resolves in a day or more.
2. **Switch routing to the new classifier.** About six weeks, with a weekly accuracy check.
3. **Hire 2 → decide in about eight weeks**, between Logistics and Returns Desk, using the corrected queues. Returns Desk is close behind Logistics.

**One more thing for Arjun.** 74 orders received both a refund *and* a replacement, which the policy does not allow: Rs 2.5 lakh refunded and Rs 1.4 lakh in replacements. The list is attached for Finance to review.

**What we did not look at:** night-shift cover, per-agent performance, and whether the product defects behind the hardware tickets are concentrated in particular manufacturing lots. We can do these next if they would help.
