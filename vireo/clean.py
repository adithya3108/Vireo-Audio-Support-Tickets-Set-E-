"""Load the export and fix the known problems before anything is counted.

Every fix here is written down in the data log so a reader can check it.
"""
from pathlib import Path

import pandas as pd

WINDOW_START, WINDOW_END = "2025-01-01", "2026-07-01"  # brief: Jan 2025 - Jun 2026
GO_LIVE = pd.Timestamp("2025-09-14")                    # policy s9
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)
SLA_HOURS = {"chat": 0.25, "voice": 2, "social": 4, "email": 8}  # policy s3


def _find(data_dir, name):
    """Accept either clean names (tickets.csv) or the pack's uuid-prefixed ones."""
    p = Path(data_dir)
    hits = sorted(p.glob(name)) or sorted(p.glob(f"*-{name}"))
    if not hits:
        raise FileNotFoundError(f"{name} not found in {p.resolve()}")
    return hits[0]


def load(data_dir="data"):
    log = []
    read = lambda n: pd.read_csv(_find(data_dir, n), dtype=str, keep_default_na=False)
    t, agents, orders, products = read("tickets.csv"), read("agents.csv"), read("orders.csv"), read("products.csv")
    log.append(f"Loaded {len(t):,} ticket rows.")

    for c in ["created_at", "first_response_at", "resolved_at"]:
        t[c] = pd.to_datetime(t[c].replace("", None))

    # 1. Window. The export contains tickets from mid-2024 that are outside the brief.
    out = (t.created_at < WINDOW_START) | (t.created_at >= WINDOW_END)
    log.append(f"Dropped {out.sum():,} tickets created outside Jan 2025-Jun 2026.")
    t = t[~out].copy()

    # 2. Legacy resolution times were rebuilt from a UTC event log (policy s9);
    #    everything else is IST. Shift legacy resolved_at to IST.
    legacy = t.source_system == "legacy_fd"
    neg_before = ((t.resolved_at < t.created_at) & legacy).sum()
    t.loc[legacy, "resolved_at"] = t.loc[legacy, "resolved_at"] + IST_OFFSET
    neg_after = (t.resolved_at < t.created_at).sum()
    log.append(f"Legacy resolved_at shifted UTC->IST: tickets 'resolved before created' {neg_before:,} -> {neg_after:,}.")

    # 3. Re-imported legacy tickets can appear under both systems (policy s9).
    #    A re-import keeps customer, product and message; its timestamp may be off by
    #    the UTC/IST offset, so allow 6 hours. Same message months apart is a repeat
    #    contact, not a duplicate, and is kept.
    key = ["customer_id", "product_sku", "customer_message"]
    t = t.sort_values("created_at")
    gap = t.groupby(key).created_at.diff().abs()
    dup = gap.notna() & (gap <= pd.Timedelta(hours=6)) & t.customer_message.ne("")
    log.append(f"Cross-system duplicates (same customer, product, message within 6h): {dup.sum():,} removed.")
    t = t[~dup].copy()

    # 4. Blanks are blanks: transfers blank on legacy rows is 'unknown', not 0; CSAT blank = no response.
    t["transfers_n"] = pd.to_numeric(t.transfers.replace("", None))
    t["csat"] = pd.to_numeric(t.csat_score.replace("", None))
    t["refund"] = pd.to_numeric(t.refund_amount_inr.replace("", None))

    # 5. Resolving agent's team by agent_id (two agents share a display name) and
    #    by the roster row valid on the ticket date.
    agents["from_date"] = pd.to_datetime(agents.from_date)
    agents["to_date"] = pd.to_datetime(agents.to_date.replace("", None)).fillna(pd.Timestamp("2100-01-01"))
    m = t[["ticket_id", "agent_id", "created_at"]].merge(agents, on="agent_id", how="left")
    m = m[(m.created_at >= m.from_date) & (m.created_at < m.to_date) | m.from_date.isna()]
    m = m.sort_values("from_date").drop_duplicates("ticket_id", keep="last")
    t = t.merge(m[["ticket_id", "team", "shift", "tier"]].rename(columns={"team": "resolver_team"}), on="ticket_id", how="left")
    fallback = agents.sort_values("from_date").drop_duplicates("agent_id", keep="last").set_index("agent_id").team
    t["resolver_team"] = t.resolver_team.fillna(t.agent_id.map(fallback))

    # Derived measures
    t["month"] = t.created_at.dt.to_period("M").astype(str)
    t["first_resp_h"] = (t.first_response_at - t.created_at).dt.total_seconds() / 3600
    t["resolve_h"] = (t.resolved_at - t.created_at).dt.total_seconds() / 3600
    t["breach"] = t.first_resp_h > t.channel.map(SLA_HOURS)
    t["attended"] = t.status.isin(["resolved", "closed"])
    t["handoff"] = t.assigned_team != t.resolver_team

    # Order join: order_id, else customer + sku (README fallback)
    orders = orders.rename(columns={"sku": "order_sku"})
    by_id = t.merge(orders[["order_id", "order_value_inr", "lot_code"]], on="order_id", how="left")
    t = by_id
    log.append(f"Final analysis set: {len(t):,} tickets.")
    return t, agents, orders, products, log
