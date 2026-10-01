# Decisions, and what I left out

The brief says: decide, write it down, explain why. These are the decisions.

## Reading the brief

| Question | Decision | Why |
|---|---|---|
| "Whichever team has the most volume gets the hires": what does *volume* mean? | **Tickets per agent on each team, counted by what the ticket was about**, for Tier 1 teams only. | Raw team totals favour big teams: Chat Frontline has 15 agents. Policy §6 says Tier 2 is measured in days and must not be compared on volume. The bot tag is wrong on about 30% of tickets. |
| Which period decides the hire? | **Jan–Jun 2026** (latest six months, all on the current helpdesk). The 18-month view is in the charts. | Volume rose sharply after the Pulse 2 launch in Jul 2025. A hire should match the current run-rate. |
| Which categories? | **The helpdesk's own 11.** | The output then compares directly with today's tags, and Priya's team already knows these names. |
| Who owns a category? | Policy §6. Wrong item, transit damage and address changes → Logistics. Cancellations → Returns Desk. Repair/RMA status and physical faults → Escalations & Warranty. Product, app, account and enquiry → the frontline for that channel. | Written down in `vireo/taxonomy.py` so it can be argued with. Wrong-item could reasonably belong to Returns Desk; it is a small slice of Delivery and would not change which team comes out on top. |
| What counts as "misrouted"? | The bot's first-assigned team ≠ the team owning the classified category, with **the three frontline teams treated as one**. | The frontline teams split work by channel, not topic. A chat ticket answered by Email Frontline is not a routing error. |
| What to do with Priya's pre-commitment to Billing? | **Show where her 22% comes from** (it reproduces exactly from the raw bot tag, including 2024 rows), then show the corrected view. No hedging. | She asked us to "do it properly". Neha and Arjun are cc'd and each asked a question the data answers. |
| `submission-form.md` was not in the pack we received | Drafted one from the brief's requirements. | An unfilled form is an incomplete submission. If the real form turns up, the answers copy across. |

## Data problems found and fixed (all logged in the report)

- **Out-of-window rows.** The export includes 139 tickets from Jun–Dec 2024. These are dropped.
- **Legacy timestamps.** Legacy `resolved_at` is in UTC; everything else is IST (policy §9). 2,335 tickets "resolved before they were created". Shifting legacy resolved times by +5:30 brings that to 0.
- **Duplicate re-imports** (policy §9). I looked for them in several ways (same id, same customer+time, same customer+message within 6 hours, same note) and found none in this set. The check stays in the pipeline.
- **Blank ≠ zero.** Blank transfers on legacy rows are treated as unknown and excluded, never counted as 0. Blank CSAT is no response and is excluded from averages (policy §8).
- **Agent identity.** Agents are joined by id, never by name (two are called Om Sharma), using the roster row valid on the ticket date.
- **SLA breach attribution.** Policy §3 says breaches are reported against the *resolving* agent. That would blame Logistics for response times on tickets that sat in Billing's queue, so I attribute breaches to the first-assigned team.
- **Refund units.** Policy §9 warns legacy money may be in a "native unit". I compared refund-to-order-value ratios by system and found them identical, with no refund above order value. No conversion was applied, and the check is noted.

## Choices in the tool

- **Agent notes over customer messages.** The note records the diagnosis, and the message is often vague ("pls reply"). Labels come from notes first. The *intake router* is trained separately on messages only, because routing has to happen before any agent has written a note.
- **Rules + small model, LLM optional.** The rules and the n-gram model reach 99% on held-out tickets, run in 90 seconds and cost nothing. An LLM on all 11,641 tickets would cost money and add a network dependency for about 1% more coverage. Claude is wired in for the ~120 low-confidence tickets only, behind `--llm`. That path has not been run: no API key was available in the window.
- **A held-out set.** After I fixed errors seen on the 200-ticket development set, that number could no longer be trusted, so I labelled 100 fresh tickets and froze the code before scoring them.

## What I changed between versions

1. **v1** used a note-weighted vote when the note had no clear diagnosis. On the dev set, resolution actions in the note ("reverse pkp arranged", "fw update resolved") outvoted the actual complaint. **v2** weights the customer message higher. Dev accuracy went from 98.5% to 99.5%.
2. The held-out set (99% at freeze) exposed "one **pair** of earbuds" matching the pairing rule. The regex was fixed. The held-out number is reported *as measured before that fix*.
3. The first operational cross-check (does our owner team = resolving team?) **favoured the bot** (89% vs 78%). The resolving team mostly echoes the bot's routing, because Billing agents close many delivery tickets themselves, so the check was biased. It was replaced with: *when an agent re-routes a ticket, does the destination match our label?* The answer is 93%.

## What I threw away

- **A pure keyword taxonomy on customer messages.** Too brittle for this text: misspellings everywhere ("waiitng", "dlvry"), Hinglish, and templated phrases that mention payment in delivery complaints.
- **Headcount by raw team totals.** Replaced by per-agent load; see above.
- **Lot-code defect analysis.** I checked whether hardware tickets cluster in manufacturing lots. The per-lot counts (1–9 orders) were too small to say anything, so I dropped it rather than chart noise.
- **Stacked monthly area chart of 11 categories.** Eleven colours can't be told apart. Replaced by small multiples with actual vs bot tag on each panel, which also shows the tagging gap directly.

## Left out on purpose (the five-hour cap)

| Not done | Why it can wait |
|---|---|
| Night-shift / hour-of-day staffing model | Relevant to *when* a hire works, not *which team*. Billing, Logistics and Returns have no night shift, so it is the natural next question. |
| Per-agent performance | Not asked. It risks becoming a blame exercise, and the roster is too thin (3–5 per team) for fair comparison. |
| Live integration with the helpdesk | Needs Sameer's API access. `--route` shows the interface. |
| Second labeller for the gold sets | No one else in the window. This is the main weakness of the accuracy claim, and it is flagged everywhere the number appears. |
| Root cause of refund + replacement double-dips | Found and listed for Finance. Diagnosing it (agent, reason code, timing) is a separate piece of work. |
| CSAT deep-dive, customers.csv (care_plus) segmentation | No bearing on the hiring decision. |
