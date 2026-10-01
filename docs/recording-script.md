# Screen recording: 3-minute script

This is a guide for whoever records it; say it in your own words. No slides. Show the editor, the terminal and `outputs/report.html`. The timings add up to 2:50.

**0:00–0:20 The question.**
Open `inst.txt` at the email thread. "Priya wants two hires to go to the biggest team and thinks it's Billing at 22%. Neha thinks Logistics. Arjun wants a process fix before any hire."

**0:20–0:50 The prompts.**
Open `docs/prompts-and-ai-use.md`. "I gave Claude Code the brief and pack and said: check the supporting files and implement what's needed." Scroll to the labelling prompt in `vireo/llm.py`. "Every rule in this prompt maps to a failure I found in the data. The first one is the bot's mistake: *I paid but nothing arrived* is a delivery problem, not billing."

**0:50–1:30 What I changed between versions.**
In `vireo/classify.py`, show the comment above the vote. "v1 let actions in the agent's note, like 'reverse pickup arranged', outvote what the customer actually complained about. The gold set caught it, and v2 flips the weights." Then open `eval/evaluate.py` at the cross-check. "My first validation check favoured the bot 89 to 78. It was biased, because the resolving team mostly just echoes the bot's routing. I replaced it with: when an agent re-routes a ticket, where do they send it? That matches us 93% of the time."

**1:30–2:00 What I threw away.**
Open `docs/decisions.md` → "What I threw away". Cover these points: an LLM on every ticket (cost for 1% gain), the lot-code analysis (samples too small), and the 11-colour stacked chart.

**2:00–2:40 It runs, and here's the answer.**
Run `python run.py --route "paid on 3 May, nothing at my door yet"`. It prints Delivery & Shipping → Logistics. Open `outputs/report.html`: the team chart (Billing tagged 2,425 vs actual 1,630; Logistics 1,905 vs 3,349), then the workload bars (Logistics 41 per agent vs Billing 27).

**2:40–2:50 Close.**
"Held-out accuracy is 99% against 66% for the bot. The recommendation is first hire to Logistics, fix the routing, and decide the second hire in eight weeks."
