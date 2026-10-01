"""Optional: ask Claude to label the tickets the rules and model are unsure about.

Only runs with --llm and an Anthropic credential. Results are cached in
outputs/llm_cache.json so re-runs cost nothing. Without a key the tool runs
exactly the same minus this step (about 1% of tickets are affected).
"""
import json
import os
from pathlib import Path

from .taxonomy import CATEGORIES

MODEL = os.environ.get("VIREO_LLM_MODEL", "claude-opus-5")

PROMPT = """You categorise customer-support tickets for Vireo Audio, a consumer audio and wearables brand.

Pick the ONE category that describes what the customer actually needed resolved. Use the agent's closing note as the strongest evidence of what the problem turned out to be; use the customer's message when the note is empty or generic ("closed", "sorted", "as discussed").

Rules that matter most:
- "I paid but the order hasn't arrived" is Delivery & Shipping, not Billing & Payments. Billing is only for money problems with no delivery question: double charges, payment taken but no order created, invoices/GST, coupons/discounts.
- Refund status, return pickups and cancellations are Returns & Refunds.
- Wrong item, damaged in transit and address changes are Delivery & Shipping.
- Repair/RMA status and physical faults such as straps, dead screens or no power are Warranty & Repair.
- A resolution action in the note (replacement, refund, firmware update) does not change the category; the problem does.

Categories: {cats}

Customer message:
<message>{msg}</message>

Agent closing note:
<note>{note}</note>"""

SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "reason": {"type": "string"},
    },
    "required": ["category", "reason"],
    "additionalProperties": False,
}


def relabel_low_confidence(df, threshold=0.6, cache_path=Path("outputs/llm_cache.json"), log=print):
    try:
        import anthropic
    except ImportError:
        log("LLM step skipped: `pip install anthropic` to enable.")
        return df
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = df[df.category_conf < threshold]
    log(f"LLM step: {len(todo)} low-confidence tickets (conf < {threshold}); {sum(t in cache for t in todo.ticket_id)} cached.")
    client = anthropic.Anthropic()
    for idx, r in todo.iterrows():
        if r.ticket_id not in cache:
            try:
                resp = client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
                    messages=[{"role": "user", "content": PROMPT.format(
                        cats=", ".join(CATEGORIES), msg=r.customer_message, note=r.agent_notes)}],
                )
            except anthropic.AuthenticationError:
                log("LLM step stopped: no valid Anthropic credential (set ANTHROPIC_API_KEY).")
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError) as e:
                log(f"LLM step stopped early ({type(e).__name__}); cached results kept, re-run to resume.")
                break
            except anthropic.APIStatusError as e:
                log(f"LLM call failed for {r.ticket_id}: {e.status_code}; ticket keeps its model label.")
                continue
            if resp.stop_reason == "refusal":
                continue
            text = next(b.text for b in resp.content if b.type == "text")
            cache[r.ticket_id] = json.loads(text)
            cache_path.parent.mkdir(exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=1))
        if r.ticket_id in cache:
            df.loc[idx, "category_ai"] = cache[r.ticket_id]["category"]
            df.loc[idx, "category_source"] = "llm"
    return df
