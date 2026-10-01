# Vireo Audio: ticket categorisation and headcount check

Auto-categorises 18 months of Vireo support tickets from what the ticket was actually about. It then produces the monthly charts by category and by team that Priya asked for, and the workload-per-agent view the hiring decision needs. It also measures how often the categorisation is wrong.

## Run it (clean machine, Python 3.10+)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

It takes about 90 seconds and needs no API key. Open `outputs/report.html`.

*Clean-machine check:* tested in a fresh venv with only `requirements.txt` installed (Python 3.12, pandas 3.0.6, scikit-learn 1.9.1, matplotlib 3.11.2). It gave the same results as the development environment (pandas 2.2, scikit-learn 1.6).

The export must be in `data/`: `tickets.csv`, `agents.csv`, `orders.csv`, `products.csv`, `customers.csv`. The uuid-prefixed filenames from the pack also work, and you can point elsewhere with `--data <folder>`.

Other commands:

| Command | What it does |
|---|---|
| `python run.py --route "paid on 3 May, nothing at my door"` | Runs the intake router on a message and prints the category and team it would route to. This is the proposed fix, in miniature. |
| `python run.py --llm` | Also sends the ~1% of low-confidence tickets to Claude. Needs `ANTHROPIC_API_KEY`; results are cached in `outputs/llm_cache.json`. The model is set by `VIREO_LLM_MODEL` (default `claude-opus-5`). |
| `python -m eval.evaluate` | Re-scores the classifier against the hand-labelled gold sets. |

## What it does

```
data/ ──► clean.py ──► classify.py ──► analyse.py ──► report.py ──► outputs/
          fixes         3 layers        volumes,       charts +
          (below)       + intake        workload,      report.html
                        router          cost case
                                  └──► eval/evaluate.py (gold sets + cross-check)
```

**Cleaning** (every fix is logged in the report):
- Drops the 139 tickets from 2024 that are outside the Jan 2025 – Jun 2026 window.
- Shifts legacy `resolved_at` from UTC to IST (policy §9). Before the fix, 2,335 tickets "resolved before they were created"; after it, none do.
- Checks for legacy tickets re-imported under both systems. None were found in this set.
- Treats blank `transfers` and `csat` as unknown, not zero.
- Joins agents by `agent_id` and by the roster row valid on the ticket date. Two agents share the name "Om Sharma".

**Categorisation**, cheapest first:
1. **Rules on the agent's closing note.** Notes record the diagnosis ("issue: shipment not received"), which is the best evidence of what the ticket was really about. This labels 80% of tickets.
2. **Rules on the message and note** when the note has no clear diagnosis (14%).
3. **A character n-gram model** (TF-IDF + logistic regression) trained on the confident labels from layers 1–2. It fills the rest (6%) and copes with the heavy misspelling in the text.
4. *Optional:* Claude re-labels whatever is still low-confidence (`--llm`).

The same model is also trained on the **customer message only**. That is the **intake router**: what could be predicted when the ticket is created, before any agent touches it. It is the proposed replacement for the chat-bot's opening question.

The categories are the helpdesk's own 11, so the output lines up with the bot tag. Each category maps to the team that owns it under policy §6.

## Outputs (`outputs/`)

| File | Contents |
|---|---|
| `report.html` | Everything below in one page |
| `chart_category_monthly.png`, `chart_team_monthly.png` | Monthly volume by category and by team: actual vs bot tag |
| `chart_workload_per_agent.png` | Tickets per agent per month, Tier 1 teams |
| `monthly_by_{category,team}_{actual,bot_tag}.csv` | The chart data as tables |
| `workload_by_team.csv`, `misroute_effect.csv` | Workload and what misrouting costs |
| `tickets_categorised.csv` | Every ticket with bot tag, our category, label source, confidence, owning team, misrouted flag |
| `evaluation.md` | Accuracy against the gold sets and the operational cross-check |
| `refund_and_replacement.csv` | 74 orders that got both, which policy §5 forbids |

## How we know it works

See `outputs/evaluation.md`, and `docs/decisions.md` for the reasoning.

| | Development set (200) | Held-out set (100, labelled after freeze) |
|---|---|---|
| Chat-bot tag (today) | 72% | 66% |
| Our classifier | 100%* | 99% |
| Intake router (message only) | 99.5% | 100% |

\*Two rule fixes were made after reading errors on this set, so it is optimistic. The held-out figure is the honest one; its 95% interval is roughly 95–100%.

**Independent check.** When an agent moves a misrouted ticket to another team, they send it to the team our label predicts **93%** of the time (706 hand-offs). Agents made those decisions without this tool.

**Limits.** The gold labels were made by one labeller, so a second person should spot-check them (`eval/*.csv`). The ticket text in this export is fairly templated, so accuracy on live free text will be lower. Re-label 100 fresh tickets a month and watch the number.

## Repository map

```
run.py                  entry point
vireo/clean.py          loading + data fixes
vireo/taxonomy.py       categories, owner teams, intent patterns
vireo/classify.py       rules + model + intake router
vireo/llm.py            optional Claude step (prompt is in this file)
vireo/analyse.py        volumes, workload, business case, refund check
vireo/report.py         charts + HTML
eval/                   gold labels, held-out labels, evaluate.py
docs/                   memo, business goal, decisions, recording script, prompts
submission-form.md
```
