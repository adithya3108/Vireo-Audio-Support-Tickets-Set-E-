"""Volumes, workload and the business case. All money figures use the policy's
FY26 cost standards (support-policy.pdf s3-s5)."""
import numpy as np
import pandas as pd

from .taxonomy import owner_team

COST = dict(transfer=305, breach_credit=350, blended_contact=290, agent_hour=165, hire_year=450_000)
BACK_OFFICE = ["Logistics", "Returns Desk", "Billing"]
TARGET_MISROUTE = 0.05


def _frontline(s):
    return s.where(~s.str.contains("Frontline"), "Frontline")


def enrich(t):
    t = t.copy()
    t["owner_team"] = [owner_team(c, ch) for c, ch in zip(t.category_ai, t.channel)]
    # Misrouted = the bot's routing sent it to a team that does not own the problem.
    # Frontline teams are treated as one (they split work by channel, not by topic).
    t["misrouted"] = _frontline(t.assigned_team) != _frontline(t.owner_team)
    # Repeat contact (policy s10): same customer, same category, new ticket within 30 days of resolution.
    t = t.sort_values("created_at")
    nxt = t.groupby(["customer_id", "category_ai"]).created_at.shift(-1)
    gap = nxt - t.resolved_at
    t["repeat_followed"] = gap.notna() & (gap > pd.Timedelta(0)) & (gap <= pd.Timedelta(days=30))
    return t


def monthly(t, col):
    return t.pivot_table(index="month", columns=col, values="ticket_id", aggfunc="count", fill_value=0)


def headcount(agents, on="2026-06-30"):
    d = pd.Timestamp(on)
    live = agents[(agents.from_date <= d) & (agents.to_date > d)].drop_duplicates("agent_id", keep="last")
    return live.team.value_counts()


def workload(t, agents, since="2026-01-01"):
    r = t[t.created_at >= since]
    months = r.month.nunique()
    hc = headcount(agents)
    w = pd.DataFrame({
        "agents": hc,
        "tickets_per_month_bot_tag": r.assigned_team.value_counts() / months,
        "tickets_per_month_actual": r.owner_team.value_counts() / months,
        "median_hours_to_resolve": t.groupby("owner_team").resolve_h.median(),
        "sla_breach_rate": r.groupby("assigned_team").breach.mean(),
    }).fillna(0)
    w["per_agent_bot_tag"] = w.tickets_per_month_bot_tag / w.agents
    w["per_agent_actual"] = w.tickets_per_month_actual / w.agents
    w["share_bot_tag"] = w.tickets_per_month_bot_tag / w.tickets_per_month_bot_tag.sum()
    w["share_actual"] = w.tickets_per_month_actual / w.tickets_per_month_actual.sum()
    return w.sort_values("per_agent_actual", ascending=False)


def misroute_effect(t):
    """Compare misrouted vs correctly routed tickets. Transfers only exist in the
    current helpdesk, so that comparison is restricted to helpdesk rows."""
    h = t[t.source_system == "helpdesk"]
    att = t[t.attended]
    g = pd.DataFrame({
        "tickets": t.groupby("misrouted").size(),
        "transfers_per_ticket (helpdesk only)": h.groupby("misrouted").transfers_n.mean(),
        "sla_breach_rate": t.groupby("misrouted").breach.mean(),
        "median_hours_to_resolve": t.groupby("misrouted").resolve_h.median(),
        "repeat_contact_rate_30d": att.groupby("misrouted").repeat_followed.mean(),
        "avg_csat (responders only)": t.groupby("misrouted").csat.mean(),
    })
    g.index = g.index.map({False: "Routed correctly", True: "Misrouted"})
    return g


def business_case(t, agents, since="2026-01-01"):
    r = t[t.created_at >= since]
    quarters = r.month.nunique() / 3
    per_q = len(r) / quarters
    mis_rate = r.misrouted.mean()
    eff = misroute_effect(t)
    ok, bad = eff.loc["Routed correctly"], eff.loc["Misrouted"]
    per_ticket = {
        "extra transfers": (bad["transfers_per_ticket (helpdesk only)"] - ok["transfers_per_ticket (helpdesk only)"]) * COST["transfer"],
        "extra SLA breach credits": (bad.sla_breach_rate - ok.sla_breach_rate) * COST["breach_credit"],
        "extra repeat contacts": (bad.repeat_contact_rate_30d - ok.repeat_contact_rate_30d) * COST["blended_contact"],
    }
    avoided_per_q = (mis_rate - TARGET_MISROUTE) * per_q
    saving_q = {k: v * avoided_per_q for k, v in per_ticket.items()}
    wl = workload(t, agents, since)
    billing_inflow = (r[(r.assigned_team == "Billing") & (r.owner_team != "Billing")].shape[0]) / r.month.nunique()
    return dict(
        since=since, tickets_per_quarter=per_q, misroute_rate=mis_rate, target=TARGET_MISROUTE,
        misrouted_per_quarter=mis_rate * per_q, avoided_per_quarter=avoided_per_q,
        cost_per_misroute=sum(per_ticket.values()), per_ticket=per_ticket,
        saving_per_quarter=saving_q, saving_total_q=sum(saving_q.values()),
        billing_not_theirs_per_month=billing_inflow, workload=wl,
        breach_credits_per_quarter=r.breach.sum() / quarters * COST["breach_credit"],
        misrouted_share_of_breaches=r[r.misrouted].breach.sum() / max(r.breach.sum(), 1),
    )


def refund_and_replacement(t, products):
    """Policy s5: never both a refund and a replacement on one order."""
    unit = products.set_index("sku").unit_cost_inr.astype(float)
    x = t[t.order_id != ""].copy()
    x["repl_cost"] = np.where(x.replacement_issued == "Y", x.product_sku.map(unit) + 340, 0)
    g = x.groupby("order_id").agg(refund=("refund", "sum"), repl_cost=("repl_cost", "sum"),
                                  tickets=("ticket_id", "size"), agents=("agent_id", lambda s: ", ".join(sorted(set(s)))))
    both = g[(g.refund > 0) & (g.repl_cost > 0)].sort_values("refund", ascending=False)
    return both


def priya_numbers(raw_tickets):
    """Reproduce the 22% / 16% quoted in the email thread, to show where they came from."""
    s = raw_tickets.category.value_counts(normalize=True)
    return s.get("Billing & Payments", 0), s.get("Delivery & Shipping", 0), len(raw_tickets)
