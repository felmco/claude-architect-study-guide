"""
Task Statement 5.1: Manage conversation context to preserve critical information

Key concepts:
- Progressive summarization risk: loses numerical values, dates, specific facts
- "Lost in the middle" effect: models miss information in middle of long inputs
- Tool results accumulate and consume tokens disproportionately
- Case facts block: extracted transactional facts persisted outside summarized history
- Trimming verbose tool outputs (40+ fields → 5 relevant fields)
- Key findings at beginning of aggregated inputs + explicit section headers
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Case facts block pattern ──────────────────────────────────────────────────

class CaseFacts:
    """
    Persistent store of transactional facts extracted from tool results.

    These are included in EVERY prompt regardless of conversation summary.
    This prevents loss of critical values (amounts, dates, IDs) during summarization.
    """

    def __init__(self):
        self._facts: dict = {}

    def update(self, new_facts: dict):
        """Update facts, never deleting — only updating."""
        self._facts.update(new_facts)

    def as_context_block(self) -> str:
        """Format for inclusion at the TOP of each prompt."""
        if not self._facts:
            return ""
        return f"""
=== CASE FACTS (verified, do not override with summaries) ===
{json.dumps(self._facts, indent=2)}
=== END CASE FACTS ===
"""

    def get(self, key: str, default=None):
        return self._facts.get(key, default)


# ─── Tool output trimming ──────────────────────────────────────────────────────

def trim_order_lookup_result(full_result: dict, relevant_fields: list[str]) -> dict:
    """
    Trim verbose tool outputs before they accumulate in conversation context.

    Example: order lookup returns 40+ fields but only 5 are relevant to the current case.
    Including all 40 fields wastes context tokens and dilutes important information.
    """
    return {k: v for k, v in full_result.items() if k in relevant_fields}


# ─── Demonstrate context preservation ─────────────────────────────────────────

def demonstrate_context_strategies():
    """Shows correct vs incorrect approaches to long-conversation context."""

    print("=== Context Preservation Strategies ===\n")

    # Simulated verbose tool result (typical order lookup — 40+ fields)
    verbose_order_result = {
        "order_id": "ORD-5678",
        "customer_id": "CUST-1234",
        "total": 125.00,
        "subtotal": 100.00,
        "tax": 25.00,
        "shipping": 0.00,
        "status": "delivered",
        "delivery_date": "2025-05-20",
        "return_deadline": "2025-06-19",
        "payment_method": "credit_card",
        "payment_last_four": "4242",
        "payment_brand": "Visa",
        "shipping_address": "123 Main St",
        "shipping_city": "Springfield",
        "shipping_state": "IL",
        "shipping_zip": "62701",
        "billing_address": "123 Main St",
        "items": [{"sku": "WIDGET-A", "qty": 2, "price": 50.00}],
        "item_count": 1,
        "warehouse_id": "WH-MIDWEST-2",
        "carrier": "UPS",
        "tracking_number": "1Z999AA1234567890",
        "weight_lbs": 2.3,
        "created_at": "2025-05-10T14:23:00Z",
        "updated_at": "2025-05-20T09:15:00Z",
        "internal_notes": "Picked by employee #4521",
        "seller_id": "SELLER-ACME",
        # ... 15 more fields ...
    }

    print("VERBOSE tool result (40+ fields, accumulates in context):")
    print(f"  {len(verbose_order_result)} fields, {len(json.dumps(verbose_order_result))} bytes")
    print()

    # Only keep return-relevant fields for a refund case
    relevant_fields = ["order_id", "customer_id", "total", "status", "delivery_date", "return_deadline", "items"]
    trimmed = trim_order_lookup_result(verbose_order_result, relevant_fields)

    print("TRIMMED result (only return-relevant fields):")
    print(json.dumps(trimmed, indent=2))
    print(f"  {len(trimmed)} fields, {len(json.dumps(trimmed))} bytes")
    print()

    # Extract to case facts
    case_facts = CaseFacts()
    case_facts.update({
        "order_id": trimmed["order_id"],
        "order_total": trimmed["total"],
        "return_deadline": trimmed["return_deadline"],
        "order_status": trimmed["status"],
    })

    print("Case facts block (included in every subsequent prompt):")
    print(case_facts.as_context_block())


# ─── Demonstrate "lost in the middle" mitigation ──────────────────────────────

def demonstrate_position_effects():
    """
    "Lost in the middle" effect: models reliably process the beginning
    and end of long contexts but may miss content in the middle.

    Mitigation:
    1. Put key findings at the BEGINNING of aggregated inputs
    2. Use explicit section headers
    3. Keep numerical facts in case facts block (not summarized away)
    """
    print("\n=== Lost in the Middle Effect — Mitigation ===\n")

    print("WRONG: Key findings buried in the middle of a long aggregated input")
    wrong_structure = """
    Research findings from agent 1: [3000 words of background context]

    ** CRITICAL FINDING: The refund amount is $125.00 **  ← buried in middle

    Additional research from agent 2: [2000 words of follow-up]
    Summary and recommendations: [500 words]
    """
    print("  Critical facts can be missed when buried in middle of long context")
    print()

    print("CORRECT: Key findings at BEGINNING + explicit section headers")
    correct_structure = """
    === KEY FINDINGS (READ FIRST) ===
    - Customer verified: CUST-1234 (Jane Smith, Gold tier)
    - Order verified: ORD-5678, total $125.00, delivered 2025-05-20
    - Return window: expires 2025-06-19 (still eligible)
    - Refund requested: $125.00 for defective item

    === DETAILED RESEARCH FROM AGENT 1 ===
    [3000 words of background context]

    === DETAILED RESEARCH FROM AGENT 2 ===
    [2000 words of follow-up]

    === RECOMMENDATIONS ===
    [500 words]
    """
    print("  Key facts at beginning → reliably processed")
    print("  Section headers → model can navigate long inputs")
    print()
    print("For multi-agent synthesis: require agents to include structured")
    print("metadata (dates, sources, relevance scores) as separate fields,")
    print("not embedded in prose where they get lost during summarization.")


# ─── Subagent structured outputs ──────────────────────────────────────────────

def demonstrate_structured_subagent_output():
    """
    Subagents should return structured outputs that preserve metadata,
    not just prose summaries. This enables accurate downstream synthesis.
    """
    print("\n=== Structured Subagent Outputs ===\n")

    bad_subagent_output = """
    Based on my research, AI adoption in creative industries has been growing
    rapidly since 2021. Several studies from 2023 showed 40% increase in
    AI tool usage among graphic designers...
    """

    good_subagent_output = {
        "summary": "AI adoption in creative industries grew 40% from 2021-2023",
        "claims": [
            {
                "claim": "40% increase in AI tool usage among graphic designers",
                "source_url": "https://example.com/report-2023",
                "source_title": "Creative Industry AI Survey 2023",
                "publication_date": "2023-06-15",  # Required — temporal context
                "evidence_excerpt": "Our survey of 500 designers found 40% adoption rate",
                "confidence": 0.9,
            }
        ],
        "gaps": ["music industry", "film post-production"],
        "collection_date": "2025-05-28",
    }

    print("BAD: Prose summary (source attribution lost in prose)")
    print(f"  {bad_subagent_output[:100]}...")
    print()
    print("GOOD: Structured with preserved metadata")
    print(json.dumps(good_subagent_output, indent=2))
    print()
    print("Key: publication_date is REQUIRED in structured outputs.")
    print("Without it, a 2019 stat and a 2024 stat look identical to the synthesis agent.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.1: Context Preservation for Long Interactions")
    print("=" * 60)

    demonstrate_context_strategies()
    demonstrate_position_effects()
    demonstrate_structured_subagent_output()

    print("\n" + "=" * 60)
    print("Case facts block: extract transactional facts OUTSIDE summarized history")
    print("Trim verbose outputs: 40+ fields → 5 relevant fields")
    print("Key findings at START of long inputs, not buried in middle")


if __name__ == "__main__":
    main()
