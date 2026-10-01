"""Vireo ticket categorisation - one command end to end.

  python run.py                   # clean -> categorise -> analyse -> evaluate -> report
  python run.py --llm             # also send low-confidence tickets to Claude (needs ANTHROPIC_API_KEY)
  python run.py --route "paid on 3 May, still nothing at my door"   # try the intake router on one message
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from eval.evaluate import evaluate
from vireo import analyse, report
from vireo.classify import categorise
from vireo.clean import load
from vireo.taxonomy import owner_team


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data", help="folder with the export (default: data/)")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--llm", action="store_true", help="re-label low-confidence tickets with Claude")
    ap.add_argument("--route", nargs="+", help="classify customer message(s) with the intake router and exit")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    t0 = time.time()
    say = lambda m: print(f"[{time.time() - t0:5.1f}s] {m}", flush=True)

    t, agents, orders, products, log = load(a.data)
    for line in log:
        say(line)
    raw = pd.read_csv(sorted(Path(a.data).glob("*tickets.csv"))[0], dtype=str, keep_default_na=False)

    say("Categorising (rules on agent notes -> rules on text -> char n-gram model)...")
    t, intake = categorise(t)
    if a.route:
        for msg in a.route:
            p = intake.predict_proba([msg])[0]
            cat = intake.classes_[p.argmax()]
            print(f"\n  \"{msg}\"\n  -> {cat}  (confidence {p.max():.0%})  ->  route to {owner_team(cat, 'chat')}")
        return
    if a.llm:
        from vireo.llm import relabel_low_confidence
        t = relabel_low_confidence(t, cache_path=out / "llm_cache.json", log=say)
    say("Sources of the final label: " + ", ".join(f"{k} {v:,}" for k, v in t.category_source.value_counts().items()))

    t = analyse.enrich(t)
    bc = analyse.business_case(t, agents)
    eff = analyse.misroute_effect(t)
    wl = bc["workload"]
    both = analyse.refund_and_replacement(t, products)
    priya = analyse.priya_numbers(raw)

    say("Writing tables...")
    keep = ["ticket_id", "created_at", "month", "channel", "status", "source_system", "category", "category_ai",
            "category_source", "category_conf", "intake_pred", "assigned_team", "owner_team", "resolver_team",
            "misrouted", "transfers_n", "breach", "resolve_h", "csat", "refund", "attended", "customer_message", "agent_notes"]
    t[keep].to_csv(out / "tickets_categorised.csv", index=False)
    analyse.monthly(t, "category_ai").to_csv(out / "monthly_by_category_actual.csv")
    analyse.monthly(t, "category").to_csv(out / "monthly_by_category_bot_tag.csv")
    analyse.monthly(t, "owner_team").to_csv(out / "monthly_by_team_actual.csv")
    analyse.monthly(t, "assigned_team").to_csv(out / "monthly_by_team_bot_tag.csv")
    wl.round(2).to_csv(out / "workload_by_team.csv")
    eff.round(3).to_csv(out / "misroute_effect.csv")
    both.to_csv(out / "refund_and_replacement.csv")

    say("Evaluating against hand-labelled gold sets...")
    tt = t.copy()
    tt["resolver_team"] = tt.resolver_team.fillna("")
    ev = evaluate(tt)
    (out / "evaluation.md").write_text(ev, encoding="utf-8")

    say("Drawing charts and report...")
    report.chart_category(t, out / "chart_category_monthly.png")
    report.chart_team(t, out / "chart_team_monthly.png")
    report.chart_load(wl, out / "chart_workload_per_agent.png")
    report.write_html(out, bc, eff.round(3), wl.round(2), log, ev, both, priya)

    print(f"""
==== Summary (Jan-Jun 2026 run-rate) ====
Misrouted by the chat bot: {bc['misroute_rate']:.1%}  ({bc['misrouted_per_quarter']:,.0f} tickets/quarter)
Billing share  bot tag {wl.loc['Billing', 'share_bot_tag']:.1%}  ->  actual {wl.loc['Billing', 'share_actual']:.1%}
Logistics share bot tag {wl.loc['Logistics', 'share_bot_tag']:.1%}  ->  actual {wl.loc['Logistics', 'share_actual']:.1%}
Tickets/agent/month (actual): """ + ", ".join(f"{k} {v:.0f}" for k, v in wl.drop(index='Escalations & Warranty').per_agent_actual.items()) + f"""
Cost per misroute: Rs {bc['cost_per_misroute']:,.0f}; cutting to {bc['target']:.0%} saves ~Rs {bc['saving_total_q']:,.0f}/quarter
Refund AND replacement on same order: {len(both)} orders, Rs {both.refund.sum():,.0f} refunded
Open {out / 'report.html'}""")


if __name__ == "__main__":
    sys.exit(main())
