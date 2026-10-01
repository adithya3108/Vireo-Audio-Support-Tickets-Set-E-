"""Charts (PNG) and a single self-contained HTML report."""
import base64
import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .taxonomy import CATEGORIES  # noqa: E402

ACTUAL = "#2a78d6"   # categorical slot 1 (blue)
BOT = "#8a8984"      # neutral: the bot tag is the reference, not a series of its own
HILITE = "#eb6834"   # slot 2 (orange), used only to call out the recommended team
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def _small_multiples(actual, bot, order, title, path, ncols=4):
    n = len(order)
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.1 * ncols, 2.2 * nrows), sharex=True, sharey=True)
    axes = axes.ravel()
    x = range(len(actual.index))
    for ax, key in zip(axes, order):
        a = actual.get(key, 0 * actual.iloc[:, 0])
        b = bot.get(key, 0 * actual.iloc[:, 0])
        ax.plot(x, b, color=BOT, lw=1.5, ls=(0, (3, 2)), label="Chat-bot tag")
        ax.plot(x, a, color=ACTUAL, lw=2, label="Actual (classified)")
        ax.set_title(f"{key}\n{int(a.sum()):,} actual vs {int(b.sum()):,} tagged", fontsize=8.5, color=INK, loc="left")
        ax.set_xticks([0, 6, 12, 17])
        ax.set_xticklabels([actual.index[i][2:].replace("-", "/") for i in [0, 6, 12, 17]])
    for ax in axes[n:]:
        ax.axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=2, frameon=False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def chart_category(t, path):
    a = t.pivot_table(index="month", columns="category_ai", values="ticket_id", aggfunc="count", fill_value=0)
    b = t.pivot_table(index="month", columns="category", values="ticket_id", aggfunc="count", fill_value=0).reindex(a.index, fill_value=0)
    order = sorted(set(CATEGORIES) & (set(a.columns) | set(b.columns)), key=lambda c: -a.get(c, b.get(c)).sum())
    _small_multiples(a, b, order, "Tickets per month by category - what the ticket was actually about vs the bot's tag", path)


def chart_team(t, path):
    a = t.pivot_table(index="month", columns="owner_team", values="ticket_id", aggfunc="count", fill_value=0)
    b = t.pivot_table(index="month", columns="assigned_team", values="ticket_id", aggfunc="count", fill_value=0).reindex(a.index, fill_value=0)
    order = list(a.sum().sort_values(ascending=False).index)
    _small_multiples(a, b, order, "Tickets per month by owning team - team that owns the problem vs team the bot routed to", path)


def chart_load(wl, path, recommend="Logistics"):
    d = wl.drop(index="Escalations & Warranty", errors="ignore").sort_values("per_agent_actual")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = range(len(d))
    colors = [HILITE if i == recommend else ACTUAL for i in d.index]
    ax.barh(y, d.per_agent_actual, color=colors, height=0.55)
    ax.scatter(d.per_agent_bot_tag, y, marker="|", s=260, color=INK, linewidths=2, label="What the bot tag suggests", zorder=3)
    for i, (v, b, n) in enumerate(zip(d.per_agent_actual, d.per_agent_bot_tag, d.agents)):
        ax.text(max(v, b) + 0.8, i, f"{v:.0f}  ({int(n)} agents)", va="center", color=INK2, fontsize=8.5)
    ax.set_xlim(0, d[["per_agent_actual", "per_agent_bot_tag"]].max().max() * 1.25)
    ax.set_yticks(list(y))
    ax.set_yticklabels(d.index)
    ax.set_xlabel("Tickets per agent per month, Jan-Jun 2026")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title("Workload per agent (Tier 1 teams; Tier 2 is measured in days, not volume - policy s6)",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _img(path):
    return f'<img alt="{html.escape(Path(path).stem)}" src="data:image/png;base64,{base64.b64encode(Path(path).read_bytes()).decode()}">'


def _table(df, fmt=None):
    return df.to_html(classes="t", float_format=fmt or (lambda v: f"{v:,.2f}"), border=0)


def write_html(out_dir, bc, eff, wl, log, evaluation_md, both, priya):
    out = Path(out_dir)
    rs = lambda v: f"Rs {v:,.0f}"
    wl_show = wl[["agents", "tickets_per_month_bot_tag", "tickets_per_month_actual", "per_agent_bot_tag",
                  "per_agent_actual", "median_hours_to_resolve", "share_bot_tag", "share_actual"]].copy()
    for c in ["share_bot_tag", "share_actual"]:
        wl_show[c] = (wl_show[c] * 100).round(1).astype(str) + "%"
    saving_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{rs(bc['per_ticket'][k])}</td><td>{rs(v)}</td></tr>"
                          for k, v in bc["saving_per_quarter"].items())
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vireo Ticket Categorisation</title>
<style>
:root{{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;--accent:#2a78d6}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#383835}} img{{background:#fff;border-radius:6px}}}}
body{{background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,sans-serif;max-width:1100px;margin:0 auto;padding:24px 16px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{margin-top:40px;border-top:1px solid var(--line);padding-top:20px}}
.kpis{{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}} .k{{flex:1 1 200px;border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.k b{{display:block;font-size:26px}} .k span{{color:var(--ink2);font-size:13px}}
img{{max-width:100%;height:auto}} table.t{{border-collapse:collapse;font-size:13px;margin:8px 0;display:block;overflow-x:auto}}
table.t th,table.t td{{padding:4px 10px;border-bottom:1px solid var(--line);text-align:right}} table.t th:first-child,table.t td:first-child{{text-align:left}}
pre{{white-space:pre-wrap;font-size:12px;background:rgba(127,127,127,.08);padding:10px;border-radius:6px}} .muted{{color:var(--ink2)}}
</style></head><body>
<h1>Vireo Audio - where the ticket volume really is</h1>
<p class="muted">Jan 2025 - Jun 2026 · {len(log) and log[-1]} Generated by <code>python run.py</code>.</p>
<div class="kpis">
<div class="k"><b>{bc['misroute_rate']:.0%}</b><span>of tickets (Jan-Jun 2026) are routed by the chat bot to a team that does not own the problem</span></div>
<div class="k"><b>{wl.loc['Billing','share_bot_tag']:.0%} → {wl.loc['Billing','share_actual']:.0%}</b><span>Billing's share of volume: bot tag vs what the tickets are about</span></div>
<div class="k"><b>{wl.loc['Logistics','per_agent_actual']:.0f} vs {wl.loc['Billing','per_agent_actual']:.0f}</b><span>tickets per agent per month, Logistics vs Billing</span></div>
<div class="k"><b>{rs(bc['saving_total_q'])}</b><span>per quarter saved by cutting misrouting to {bc['target']:.0%} (transfers, SLA credits, repeat contacts)</span></div>
</div>
<h2>1. Monthly volume by category</h2>{_img(out/'chart_category_monthly.png')}
<h2>2. Monthly volume by team</h2>{_img(out/'chart_team_monthly.png')}
<h2>3. Workload per agent</h2>{_img(out/'chart_workload_per_agent.png')}
{_table(wl_show)}
<h2>4. What misrouting costs</h2>
<p>Priya's figures (Billing {priya[0]:.0%}, Logistics {priya[1]:.0%}) reproduce exactly from the raw bot tag over all {priya[2]:,} exported rows. The bot sets the tag from its opening question; customers who say "I paid but nothing arrived" get tagged Billing.</p>
{_table(eff)}
<table class="t"><tr><th>Per avoided misroute</th><th>Cost each</th><th>Per quarter at target</th></tr>{saving_rows}
<tr><td><b>Total</b></td><td><b>{rs(bc['cost_per_misroute'])}</b></td><td><b>{rs(bc['saving_total_q'])}</b></td></tr></table>
<p class="muted">Basis: {bc['tickets_per_quarter']:,.0f} tickets/quarter (H1 2026 run-rate); misrouting {bc['misroute_rate']:.1%} → {bc['target']:.0%} avoids {bc['avoided_per_quarter']:,.0f} misroutes/quarter. Costs from support-policy.pdf s3-s4. Differences are observational (misrouted vs correctly routed tickets), not a controlled experiment.</p>
<h2>5. Also found: refund <i>and</i> replacement on the same order ({len(both)} orders)</h2>
<p>Policy s5 forbids this. Refunded {rs(both.refund.sum())} plus {rs(both.repl_cost.sum())} replacement cost on these orders. Full list in <code>refund_and_replacement.csv</code>.</p>
<h2>6. How reliable is the categorisation?</h2><div>{_md(evaluation_md)}</div>
<h2>7. Data fixes applied</h2><ul>{''.join(f'<li>{html.escape(l)}</li>' for l in log)}</ul>
</body></html>"""
    (out / "report.html").write_text(page, encoding="utf-8")


def _md(md):
    """Tiny markdown -> html for the evaluation block (tables, headers, pre)."""
    out, in_pre, rows = [], False, []

    def flush():
        if rows:
            hdr, *body = [r for r in rows if not set(r.replace("|", "").strip()) <= set("-: ")]
            cells = lambda r, tag: "".join(f"<{tag}>{html.escape(c.strip())}</{tag}>" for c in r.strip("|").split("|"))
            out.append('<table class="t"><tr>' + cells(hdr, "th") + "</tr>" + "".join(f"<tr>{cells(r, 'td')}</tr>" for r in body) + "</table>")
            rows.clear()
    for line in md.splitlines():
        if line.startswith("```"):
            flush(); out.append("</pre>" if in_pre else "<pre>"); in_pre = not in_pre; continue
        if in_pre:
            out.append(html.escape(line)); continue
        if line.startswith("|"):
            rows.append(line); continue
        flush()
        if line.startswith("#"):
            lvl = min(len(line) - len(line.lstrip("#")) + 1, 4)
            out.append(f"<h{lvl}>{html.escape(line.lstrip('# '))}</h{lvl}>")
        elif line.strip():
            out.append(f"<p>{html.escape(line.lstrip('- '))}</p>")
    flush()
    return "\n".join(out)
