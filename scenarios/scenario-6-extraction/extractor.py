"""
Scenario 6: Structured Data Extraction

Demonstrates Tasks 4.3, 4.4, 4.5, 5.5 in an integrated pipeline.
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")

EXTRACT_TOOL = {
    "name": "extract_invoice",
    "description": "Extract invoice data. Return null for absent fields — do not invent values.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "total_amount": {"type": "number"},
            "invoice_number": {"type": ["string", "null"]},
            "invoice_date": {"type": ["string", "null"]},
            "overall_confidence": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Confidence 0-1 for the extraction overall",
            },
        },
        "required": ["vendor_name", "total_amount", "overall_confidence"],
    },
}


def extract(document: str) -> Optional[dict]:
    """Extract invoice data with confidence score."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_invoice"},
        messages=[{"role": "user", "content": f"Extract:\n\n{document}"}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return None


def route(extraction: dict) -> str:
    """Route based on confidence."""
    conf = extraction.get("overall_confidence", 0)
    if conf >= 0.90:
        return "auto_process"
    elif conf >= 0.70:
        return "human_review_low_priority"
    else:
        return "human_review_urgent"


def main():
    docs = [
        "INVOICE #INV-001\nAcme Corp\nTotal Due: $500.00\nDate: 2025-05-28",
        "reciept\namount = approx $45\n(no vendor info)",
    ]

    print("=" * 60)
    print("Scenario 6: Structured Extraction Pipeline")
    print("=" * 60)

    for i, doc in enumerate(docs, 1):
        print(f"\nDocument {i}: {doc[:50]}...")
        result = extract(doc)
        if result:
            routing = route(result)
            print(f"  Confidence: {result.get('overall_confidence', 'N/A'):.2f}")
            print(f"  Routing: {routing}")
            print(f"  Vendor: {result.get('vendor_name', 'N/A')}")
            print(f"  Total: ${result.get('total_amount', 'N/A')}")
            print(f"  Invoice #: {result.get('invoice_number', None)} (null if absent)")


if __name__ == "__main__":
    main()
