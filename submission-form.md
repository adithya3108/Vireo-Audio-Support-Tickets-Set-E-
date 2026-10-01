# Submission form: Task 1 V2, Vireo Audio (Set E)

- **Name:** Adithya
- **Email:** adithyapr3104@gmail.com
- **Time spent:** 4 hours

Answers below follow the form's questions in order, ready to paste. Items marked **[TO FILL]** still need you.

---

## What did you build, and what business outcome does it move? State the number and the money.

I built a tool that re-categorises every Vireo ticket by what the customer actually needed. It produces Priya's monthly charts by category and by team, and a workload-per-agent view. It also includes an "intake router" that predicts the right team from the customer's first message, to replace the chat bot's tag.

The finding: the bot routes **22% of tickets to the wrong team**, mostly "I paid but nothing arrived" tagged as Billing. **43% of Billing's queue is not Billing's work.** By true category, Logistics carries 41 tickets per agent per month, Returns Desk 34 and Billing 27. So the hires should not go to Billing.

**Goal:** cut misrouting from **22% to 5%** within a quarter of go-live. That is worth about **Rs 47,000 a quarter** (408 fewer misroutes × Rs 116 each, made up of transfers at Rs 305, SLA credits at Rs 350 and repeat contacts at Rs 290). It halves the breach rate on those tickets (18% → 9%) and points the Rs 9 lakh a year of hires at Logistics instead of Billing.

## What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the arithmetic. If you used no paid calls, say so.

**No paid calls were used.** The shipped classifier is rules plus a local scikit-learn model.

- **One run** (all 11,780 tickets): about 95 seconds on a laptop CPU. **Rs 0.**
- **A month at 650 tickets a week** ≈ 2,800 tickets: **Rs 0** in model cost, a few seconds of CPU.
- **Optional Claude step (`--llm`, built but never run, so this is an estimate).** It only sends low-confidence tickets, about 1% (119 of 11,641 here).
  - Per call: about 500 input tokens plus about 150 output tokens on claude-opus-5 at $5 / $25 per million tokens. That is 500 × $0.000005 + 150 × $0.000025 ≈ $0.006, or about **Rs 0.55** at Rs 88/$.
  - Per month: 1% × 2,800 = 28 calls × Rs 0.55 ≈ **Rs 15 a month**.
  - Sending *every* ticket to Claude: 2,800 × Rs 0.55 ≈ Rs 1,550 a month. That is the main reason I didn't design it that way.

## How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.

- **Held-out set:** 100 random tickets, labelled by hand from message + note *after* the code was frozen. Bot tag 66% correct, our classifier **99% (1 error)**, intake router (message only) 100%. The 95% interval is about 95–100%.
- **Development set:** 200 random tickets. Bot 72%, classifier 100%. This is optimistic, because I fixed two rules after reading errors here.
- **Independent check, no labels from me:** in 706 tickets that agents re-routed away from the bot's team, the team they sent it to matched our label **93%** of the time.
- **Error rate:** about 1 in 100 on this export. Expect worse on live text.
- **The kind of case it gets wrong:**
  - Tickets where the note has no diagnosis ("sorted", "closed", "see prev") and an incidental word in the message trips a rule. The held-out miss was "two entries … for one **pair** of earbuds", read as a Bluetooth pairing problem.
  - Before the v2 fix: notes where the *action* ("reverse pickup arranged", "fw update") outvoted the *complaint*.
  - Genuinely two-team tickets (paid twice *and* not delivered) get one label.

## Did you change, narrow, or push back on the client's ask? What, when, and why.

**Yes, three times.** All three came from the first hour, after reading the email thread and profiling the data.

1. **Changed what "most volume" means.** Priya said "whichever team has the most volume gets the hires." I measured **tickets per agent, by what the ticket was actually about, Tier 1 only**. Raw totals favour big teams (Chat has 15 agents), the bot's tag is wrong on about 30% of tickets, and policy §6 says Tier 2 must not be compared on volume.
2. **Pushed back on Billing.** Priya had "half-promised" the hires to Billing based on 22%. I reproduced her 22% exactly (it is the raw bot tag, including out-of-window 2024 rows), then showed that Billing's true share is 14% and its per-agent load is third. I recommend **not** hiring into Billing.
3. **Split the decision.** Arjun asked to fix a process before hiring into it. I recommend: hire 1 into Logistics now, fix the routing, then decide hire 2 (Logistics or Returns Desk) after about eight weeks on the corrected queues.

## What is wrong with what you are handing us? Be specific: bugs, shortcuts, things you know are off.

- **One labeller.** All 300 gold labels were made in the same session that wrote the rules, so they may share blind spots. A second person should re-label the held-out set.
- **The development accuracy (100%) is tuned-on.** Only quote the held-out 99%. The "pair of earbuds" fix was made *after* scoring the held-out set, so re-running shows 100% there too. That figure is flattering.
- **The export's text is templated.** Real chat text will be messier and accuracy will drop.
- **The intake router is partly circular.** It learns from labels the rules made from the *same* tickets; cross-validation limits this but doesn't remove it. Its 100% says more about this dataset than about live use.
- **The money case is observational.** Misrouted tickets are compared with correctly routed ones, not tested in an experiment. Delivery tickets may be slower by nature, so Rs 116 per misroute is "about", and a pilot should confirm it.
- **Absolute volumes look low.** About 12–41 tickets per agent per month for 44 agents, so the export may be a sample. I only rely on *relative* load between teams.
- **Category forced to the helpdesk's 11 labels.** "Other" is never used, so genuinely ambiguous tickets are forced into a category.
- **Repeat contact = same customer + same *category* within 30 days.** That is coarser than policy's "same issue".
- **The refund+replacement check joins on order_id only.** Using the customer+SKU fallback finds 123 orders rather than 74. I reported the stricter 74.
- **The `--llm` path has never been run** (no key). It is written from the SDK docs but untested.
- **No unit tests.**
- **Runtime is wasteful.** About 90 of the 95 seconds is 5-fold cross-validation that could be cached.
- **One roster snapshot.** Headcount is taken as of 30 Jun 2026, and the roster has no mid-period changes, so I couldn't test that logic.

## What did you deliberately leave out, and why that rather than something else?

I cut anything that wouldn't change **which team gets the hires**.

- **Night-shift / hour-of-day staffing.** It matters for *when* a hire works, not *which team*. It is the natural next question, since Billing, Logistics and Returns have no night shift.
- **Per-agent performance.** Not asked, 3–5 agents per team is too few for a fair comparison, and it turns into blame.
- **Live helpdesk integration.** It needs Sameer's API access. `python run.py --route "…"` shows the interface.
- **Root cause of the refund+replacement double-dips.** Found and handed to Finance; diagnosing it is separate work.
- **Lot-code defect analysis.** Tried and dropped: 1–9 orders per lot is too few to conclude anything.
- **CSAT and customer (care_plus) segmentation.** No bearing on the hiring decision.

I chose to spend the time instead on the held-out set and the independent cross-check. A wrong categoriser would make every chart wrong, so proving it mattered more than any extra analysis.

## Anything you built or found that nobody asked for?

- **The intake router** (`--route`): predicts the right team from the customer's first message. This is the actual process fix Arjun asked about.
- **74 orders got both a refund AND a replacement,** which policy §5 forbids: Rs 2.5 lakh refunded plus Rs 1.4 lakh in replacements. Listed in `outputs/refund_and_replacement.csv` for Finance.
- **A timestamp bug in the export.** Legacy resolution times are in UTC while everything else is IST, so 2,335 tickets looked "resolved before created". Any resolution-time report built from this export is currently wrong.
- **About 400 avoidable transfers that routing won't fix.** Correctly routed tickets get passed to a team that doesn't own them (e.g. double charges sent from Billing to Returns Desk). That is a training issue, not a bot issue.
- **Billing's SLA problem is mostly not Billing's.** Its own tickets breach at 8.8%, a normal rate; the misrouted ones in its queue breach at 33%.

## What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you threw away. Link your three-minute screen recording here.

**Tools:** Claude Code in VS Code (Claude Opus 5.5), one session. The shipped classifier uses no AI service: it is rules plus scikit-learn. A Claude API step (claude-opus-5) is built in for low-confidence tickets but was not run.

**Where it helped:**
- Reading the whole pack and spotting the traps: the UTC timestamps, the out-of-window rows, blank ≠ zero, the shared agent name, Tier 2 not being comparable on volume.
- Profiling 11k tickets quickly.
- Writing the pipeline.
- Hand-labelling 300 gold tickets.
- Drafting the docs.

**Where it wasted time:**
- A validation check it designed favoured the bot (89% vs 78%) because it was biased. It had to be redesigned (agent re-routing → 93%).
- Two shell edits mangled code (a regex lost its backslash; a scripted file patch half-applied) and had to be redone.
- The tool's write-permission check failed repeatedly mid-session and stalled document writing.

**Thrown away:**
- A keyword classifier on messages only.
- Sending every ticket to an LLM.
- The biased validation check.
- The lot-code analysis.
- An 11-colour stacked chart.

**AI cost:** Claude Code [TO FILL]. API spend Rs 0.

**Recording:** https://drive.google.com/file/d/11pp3aRal142B_P8Ql0NVDHPycQfWNo7u/view?usp=sharing

## Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. **Run it:** `pip install -r requirements.txt && python run.py` (about 95 seconds, no key). Everything lands in `outputs/report.html`. Categories and owning teams live in `vireo/taxonomy.py`; that is where to change a routing rule. Then run `python -m eval.evaluate` to see whether accuracy still holds.
2. **Trust the held-out 99%, not the 100%.** The labels are one person's. Before anyone quotes accuracy to the client, have a second person re-label `eval/holdout_labels.csv`, and re-label 100 fresh tickets every month once it's live.
3. **The recommendation and its open decision:** no hires to Billing; hire 1 to Logistics now; switch routing to the intake router (needs Sameer for the helpdesk hook); decide hire 2 between Logistics and Returns Desk in about eight weeks on corrected numbers. Separately, the 74 refund+replacement orders are with Arjun/Finance.
