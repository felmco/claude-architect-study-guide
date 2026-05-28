"""
Task Statement 4.3: Enforce structured output using tool use and JSON schemas

Key concepts:
- tool_use with JSON schema = MOST RELIABLE structured output (eliminates syntax errors)
- tool_choice "any" → guarantee tool call when document type unknown
- tool_choice forced → run specific extraction before enrichment
- Optional (nullable) fields prevent hallucination of absent values
- Enum + "other" + detail string for extensible categories
- Strict mode eliminates SYNTAX errors but NOT semantic errors
- Semantic errors: line items don't sum to total, values in wrong fields
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv
import anthropic
from pydantic import BaseModel, Field, validator

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Schema design: nullable fields prevent hallucination ─────────────────────

INVOICE_EXTRACTION_TOOL = {
    "name": "extract_invoice",
    "description": (
        "Extract structured data from an invoice document. "
        "Use for documents that appear to be invoices with line items, totals, and vendor info. "
        "Return null for any field not present in the source document — do not invent values."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # Required fields (will be hallucinated if absent — use sparingly)
            "vendor_name": {
                "type": "string",
                "description": "Name of the company issuing the invoice",
            },
            "total_amount": {
                "type": "number",
                "description": "Final total amount due in the document's currency",
            },
            # Optional fields — model returns null if not present (no hallucination)
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice ID or number. Null if not found in document.",
            },
            "invoice_date": {
                "type": ["string", "null"],
                "description": "Date of invoice in ISO 8601 format (YYYY-MM-DD). Null if absent.",
            },
            "due_date": {
                "type": ["string", "null"],
                "description": "Payment due date. Null if not specified.",
            },
            "purchase_order_number": {
                "type": ["string", "null"],
                "description": "PO number if referenced. Null if not mentioned.",
            },
            # Extensible enum: "other" + detail prevents silent failures
            "payment_terms": {
                "type": ["string", "null"],
                "enum": ["net_30", "net_60", "net_90", "due_on_receipt", "other", None],
                "description": "Payment terms category. Use 'other' for non-standard terms.",
            },
            "payment_terms_detail": {
                "type": ["string", "null"],
                "description": "Required when payment_terms='other'. Describes the actual terms.",
            },
            # Semantic validation helper
            "line_items_subtotal": {
                "type": ["number", "null"],
                "description": (
                    "Sum of all line items before tax. Used to validate total_amount. "
                    "If line items are not itemized, return null."
                ),
            },
        },
        "required": ["vendor_name", "total_amount"],  # Only truly required fields
    },
}

RECEIPT_EXTRACTION_TOOL = {
    "name": "extract_receipt",
    "description": (
        "Extract data from a receipt (point-of-sale, retail, restaurant). "
        "Different from invoices: receipts are typically immediate payment, no PO numbers. "
        "Use when document is a sales receipt, till receipt, or transaction record."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "merchant_name": {"type": "string"},
            "transaction_amount": {"type": "number"},
            "transaction_date": {"type": ["string", "null"]},
            "payment_method": {
                "type": ["string", "null"],
                "enum": ["cash", "credit_card", "debit_card", "digital_wallet", "other", None],
            },
        },
        "required": ["merchant_name", "transaction_amount"],
    },
}


# ─── Demonstration functions ───────────────────────────────────────────────────

def extract_structured_output(document: str, verbose: bool = True) -> dict:
    """
    Extract structured data using tool_use.

    tool_choice "any" guarantees a tool call even when the model might prefer
    to respond in prose. Used when document type is unknown (could be invoice or receipt).
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[INVOICE_EXTRACTION_TOOL, RECEIPT_EXTRACTION_TOOL],
        tool_choice={"type": "any"},  # MUST call a tool — model chooses which
        messages=[{
            "role": "user",
            "content": f"Extract structured data from this document:\n\n{document}",
        }],
    )

    if verbose:
        print(f"stop_reason: {response.stop_reason}")

    for block in response.content:
        if block.type == "tool_use":
            if verbose:
                print(f"Tool called: {block.name}")
                print(f"Extracted data: {json.dumps(block.input, indent=2)}")
            return {"tool": block.name, "data": block.input}

    return {"error": "No tool called despite tool_choice='any'"}


def force_prerequisite_extraction(document: str) -> dict:
    """
    Use forced tool_choice to ensure extract_metadata runs FIRST
    before any enrichment steps.

    Pattern: Force step 1 in turn 1 → follow-up turns use "auto" for remaining steps.
    """
    # Turn 1: Force metadata extraction (prerequisite)
    metadata_response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=[INVOICE_EXTRACTION_TOOL, RECEIPT_EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_invoice"},  # FORCED
        messages=[{
            "role": "user",
            "content": f"Process this financial document:\n\n{document}",
        }],
    )

    metadata = None
    for block in metadata_response.content:
        if block.type == "tool_use":
            metadata = block.input
            print(f"Step 1 (forced): extract_invoice → {metadata}")

    return metadata or {}


def demonstrate_nullable_prevents_hallucination(verbose: bool = True) -> None:
    """
    Show that nullable fields prevent hallucination when data is absent.
    """
    # Document with minimal information
    sparse_document = """
    INVOICE
    Vendor: Acme Corp
    Total: $1,250.00
    """

    print("\n=== Nullable Fields Prevent Hallucination ===\n")
    print(f"Document:\n{sparse_document}")
    print()
    print("With nullable fields, absent data returns null (not invented values):")

    result = extract_structured_output(sparse_document, verbose=verbose)
    data = result.get("data", {})

    absent_fields = [k for k, v in data.items() if v is None]
    present_fields = [k for k, v in data.items() if v is not None]

    print(f"\nPresent fields: {present_fields}")
    print(f"Absent fields (null, not hallucinated): {absent_fields}")

    # Verify: invoice_date, invoice_number, due_date should be null (not invented)
    if data.get("invoice_number") is None:
        print("\n✓ CORRECT: invoice_number is null (not hallucinated)")
    else:
        print(f"\n⚠ WARNING: invoice_number was hallucinated as: {data.get('invoice_number')}")


def demonstrate_semantic_validation() -> None:
    """
    Show that strict tool_use eliminates SYNTAX errors but NOT semantic errors.
    Semantic errors require programmatic post-extraction validation.
    """
    print("\n=== Semantic Validation Required Even With tool_use ===\n")

    document = """
    Invoice #INV-001
    Line 1: Widget A × 10 = $120.00
    Line 2: Widget B × 5 = $75.00
    Subtotal: $195.00
    Tax: $14.63
    Total: $220.00  ← WRONG (should be $209.63)
    """

    result = extract_structured_output(document, verbose=False)
    data = result.get("data", {})

    total = data.get("total_amount")
    subtotal = data.get("line_items_subtotal")

    print(f"Extracted total: ${total}")
    print(f"Extracted subtotal: ${subtotal}")

    if total and subtotal:
        expected_with_tax = subtotal * 1.075  # ~7.5% tax
        discrepancy = abs(total - expected_with_tax) > 1.0

        if discrepancy:
            print(f"\n⚠ SEMANTIC ERROR DETECTED: Total ${total} does not match subtotal × (1 + tax)")
            print("  → Requires retry with error feedback or human review")
        else:
            print(f"\n✓ Totals are consistent")

    print("\nKey insight: tool_use eliminates JSON syntax errors,")
    print("but semantic validation requires separate programmatic checks.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 4.3: Structured Output via tool_use + JSON Schemas")
    print("=" * 60)

    # Test 1: tool_choice "any" for unknown document type
    print("\n--- Test 1: tool_choice 'any' — model selects appropriate schema ---")
    invoice_doc = """
    INVOICE #INV-2025-001
    From: Acme Corporation
    To: Client Corp
    Date: 2025-05-28
    Payment Terms: Net 30

    Total Amount Due: $2,500.00
    """
    result = extract_structured_output(invoice_doc)
    print(f"\nResult: {json.dumps(result, indent=2)[:300]}")

    # Test 2: Nullable fields
    demonstrate_nullable_prevents_hallucination(verbose=False)

    # Test 3: Semantic validation needed even with tool_use
    demonstrate_semantic_validation()

    # Test 4: Forced prerequisite
    print("\n--- Test 4: Forced tool_choice for prerequisite step ---")
    metadata = force_prerequisite_extraction(invoice_doc)
    print(f"\nMetadata extracted (forced first step): {list(metadata.keys())}")


if __name__ == "__main__":
    main()
