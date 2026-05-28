"""
Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries

Key concepts:
- Tool descriptions are the PRIMARY mechanism LLMs use for tool selection
- Minimal descriptions → unreliable selection between similar tools
- Include: purpose, inputs, outputs, edge cases, when-to-use, when-NOT-to-use
- Ambiguous/overlapping descriptions cause misrouting
- System prompt keywords can create unintended tool associations
- input_examples field (2026): provide concrete examples of valid inputs

Exam Q2: Production logs show get_customer called for order queries.
Root cause: minimal descriptions ("Retrieves customer info" / "Retrieves order details")
Fix: Expand descriptions to include input formats, example queries, and boundaries.
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── BAD descriptions (causes misrouting) ─────────────────────────────────────

BAD_TOOLS = [
    {
        "name": "get_customer",
        "description": "Retrieves customer information.",  # WAY too minimal
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Retrieves order details.",  # WAY too minimal
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"],
        },
    },
    # Even worse: both accept "identifier" — no way to tell which to call
]


# ─── GOOD descriptions (reliable selection) ────────────────────────────────────

GOOD_TOOLS = [
    {
        "name": "get_customer",
        "description": (
            "Verify and retrieve customer account information using their EMAIL ADDRESS. "
            "Returns: customer_id, name, account tier (standard/gold/platinum), "
            "account status (active/suspended), and membership start date. "
            "Use this when: the user provides their email, wants to know their account status, "
            "or you need a verified customer_id before performing order operations. "
            "Do NOT use this for order lookups — use lookup_order for order-specific queries. "
            "Input: email address (e.g., 'jane@example.com'). "
            "Returns error if email not found in system."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer email address, e.g. 'jane@example.com'",
                }
            },
            "required": ["email"],
        },
        # 2026 addition: input_examples for complex/ambiguous tools
        "input_examples": [
            {"email": "jane@example.com"},
            {"email": "bob.smith@company.org"},
        ],
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieve ORDER details using an ORDER NUMBER (format: 'ORD-XXXX'). "
            "Returns: ordered items with quantities and prices, order total, "
            "delivery status (pending/shipped/delivered), delivery date, and return eligibility. "
            "Use this when: customer asks about a specific order, wants to return an item, "
            "or you need to verify an order before processing a refund. "
            "Do NOT use this for customer account information — use get_customer for customer data. "
            "Input: order number starting with 'ORD-', NOT customer email or customer ID. "
            "Returns 'found: false' (not an error) if order number doesn't exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "Order number in format 'ORD-XXXX', e.g. 'ORD-5678'",
                }
            },
            "required": ["order_number"],
        },
        "input_examples": [
            {"order_number": "ORD-5678"},
            {"order_number": "ORD-9999"},
        ],
    },
]


# ─── Before/after comparison ───────────────────────────────────────────────────

def test_tool_selection(query: str, tools: list, label: str) -> str:
    """Test which tool Claude selects for a given query."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=tools,
        tool_choice={"type": "any"},  # Force tool use for testing
        messages=[{"role": "user", "content": query}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return f"[{label}] Query: '{query}' → Selected: {block.name}({block.input})"
    return f"[{label}] No tool selected"


# ─── Demonstrate: ambiguous descriptions cause misrouting ─────────────────────

def demonstrate_description_impact():
    test_queries = [
        "Check my order #ORD-5678",          # Should → lookup_order
        "What's my account status?",           # Should → get_customer (if email provided)
        "I placed order #ORD-1234 yesterday",  # Should → lookup_order
    ]

    print("=== Tool Selection: BAD descriptions vs GOOD descriptions ===\n")

    for query in test_queries:
        bad_result = test_tool_selection(query, BAD_TOOLS, "BAD")
        good_result = test_tool_selection(query, GOOD_TOOLS, "GOOD")
        print(f"BAD:  {bad_result}")
        print(f"GOOD: {good_result}")
        print()


# ─── Splitting generic tools into purpose-specific tools ──────────────────────

def demonstrate_tool_splitting():
    """
    Anti-pattern: generic 'analyze_document' tool that does everything.
    Fix: split into extract_data_points, summarize_content, verify_claim_against_source.
    """
    print("=== Tool Splitting for Clear Boundaries ===\n")

    bad_generic = {
        "name": "analyze_document",
        "description": "Analyzes a document and returns information about it.",
        # Problem: what kind of analysis? extraction? summarization? verification?
        # Model can't tell which use case applies
    }

    good_split = [
        {
            "name": "extract_data_points",
            "description": (
                "Extract specific structured data points from a document: "
                "dates, amounts, names, addresses, and numeric values. "
                "Use when: you need to pull out specific fields for downstream processing. "
                "Returns: structured JSON with extracted fields."
            ),
        },
        {
            "name": "summarize_content",
            "description": (
                "Generate a concise summary of a document's main points and key arguments. "
                "Use when: the user needs an overview or wants to understand the document's "
                "main thesis without reading the full text. "
                "Returns: 2-3 paragraph prose summary."
            ),
        },
        {
            "name": "verify_claim_against_source",
            "description": (
                "Check whether a specific claim is supported, contradicted, or not addressed "
                "by the source document. Use when: validating extracted data or checking "
                "accuracy of a statement. Returns: supported/contradicted/not_found + evidence."
            ),
        },
    ]

    print("BAD: generic analyze_document → model can't determine correct use case")
    print(f"Description: '{bad_generic['description']}'")
    print()
    print("GOOD: three purpose-specific tools with clear boundaries:")
    for tool in good_split:
        print(f"  {tool['name']}: {tool['description'][:80]}...")
    print()


# ─── Renaming to eliminate ambiguity ─────────────────────────────────────────

def demonstrate_renaming():
    """
    analyze_content and analyze_document with near-identical descriptions
    cause constant misrouting. Fix: rename + update descriptions.
    """
    print("=== Tool Renaming to Eliminate Ambiguity ===\n")

    before = [
        {"name": "analyze_content", "description": "Analyzes content from various sources."},
        {"name": "analyze_document", "description": "Analyzes document content."},
        # These are functionally indistinguishable to the model
    ]

    after = [
        {
            "name": "extract_web_results",
            "description": (
                "Parse and extract structured data from web search results, web pages, "
                "or HTML content. Handles: article headlines, metadata, search snippets, "
                "and web-specific formats. Input: raw HTML or search result JSON. "
                "Do NOT use for local files or PDF documents."
            ),
        },
        {
            "name": "extract_document_data",
            "description": (
                "Extract structured data from local documents: PDFs, Word files, text files. "
                "Handles: tables, headers, footers, multi-column layouts. "
                "Input: file path or base64-encoded document content. "
                "Do NOT use for web pages or API responses."
            ),
        },
    ]

    print("BEFORE (ambiguous):")
    for t in before:
        print(f"  {t['name']}: {t['description']}")
    print()
    print("AFTER (clear boundaries):")
    for t in after:
        print(f"  {t['name']}: {t['description'][:90]}...")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 2.1: Effective Tool Descriptions")
    print("=" * 60)

    demonstrate_tool_splitting()
    demonstrate_renaming()
    demonstrate_description_impact()

    print("\n" + "=" * 60)
    print("Key rule: Tool descriptions are the PRIMARY selection mechanism.")
    print("Minimal descriptions → unreliable selection → wrong tool calls.")
    print("Fix: Add purpose, inputs, outputs, when-to-use, when-NOT-to-use.")


if __name__ == "__main__":
    main()
