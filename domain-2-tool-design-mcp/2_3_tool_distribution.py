"""
Task Statement 2.3: Distribute tools appropriately across agents and configure tool_choice

Key concepts:
- Too many tools (18 vs 4-5) degrades tool selection reliability
- Agents with tools outside their specialization tend to misuse them
- Scoped tool access: agents get only what they need for their role
- tool_choice options: "auto", "any", {"type": "tool", "name": "..."}
- Forced tool selection to ensure prerequisite tools run first
- Scoped cross-role tools for high-frequency needs (e.g., verify_fact for synthesis)

Exam Q9: Synthesis agent needs simple fact verification (85% of cases).
Fix: Give synthesis agent a scoped verify_fact tool; complex cases still route through coordinator.
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Tool sets per agent role ──────────────────────────────────────────────────

# ANTI-PATTERN: All 18 tools given to every agent
OVERPROVISION_TOOLS = [
    "web_search", "fetch_url", "read_file", "write_file", "execute_code",
    "get_customer", "lookup_order", "process_refund", "escalate_to_human",
    "create_issue", "update_issue", "send_email", "post_slack",
    "query_database", "generate_report", "translate_text",
    "extract_entities", "summarize_document",
    # 18 tools — model struggles to select the right one
]

# CORRECT: Scoped tool sets per role
SEARCH_AGENT_TOOLS = ["web_search", "fetch_url"]  # Only what search needs
ANALYSIS_AGENT_TOOLS = ["read_file", "extract_entities", "summarize_document"]  # Only analysis
SYNTHESIS_AGENT_TOOLS = [
    "verify_fact",    # Scoped cross-role tool for high-frequency need (85% of verifications)
    # Complex verifications still route through coordinator
]
COORDINATOR_TOOLS = ["Task", "web_search", "get_customer"]  # Task tool for spawning subagents


# ─── Demonstrate tool_choice options ──────────────────────────────────────────

def demonstrate_tool_choice_auto():
    """
    tool_choice: "auto" — model decides whether to call a tool or respond in text.
    Use when: you're OK with the model answering conversationally if it has enough info.
    """
    tools = [
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }
    ]

    print("=== tool_choice: 'auto' ===")
    # Model may or may not call the tool
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=tools,
        tool_choice={"type": "auto"},  # default when tools are provided
        messages=[{"role": "user", "content": "What's 2 + 2?"}],  # No tool needed
    )
    print(f"stop_reason: {response.stop_reason}")
    print(f"Called tool: {any(b.type == 'tool_use' for b in response.content)}")
    print()


def demonstrate_tool_choice_any():
    """
    tool_choice: "any" — model MUST call a tool, but can choose which one.
    Use when: you need structured output and don't care which extraction schema is used.
    Guarantees tool call even when model might prefer text response.
    """
    extraction_tools = [
        {
            "name": "extract_invoice",
            "description": "Extract data from invoice documents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "total": {"type": "number"},
                    "vendor": {"type": "string"},
                },
            },
        },
        {
            "name": "extract_receipt",
            "description": "Extract data from receipt documents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "merchant": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                },
            },
        },
    ]

    print("=== tool_choice: 'any' — guarantees structured output ===")
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=extraction_tools,
        tool_choice={"type": "any"},  # MUST call a tool — but model chooses which
        messages=[{"role": "user", "content": "Document: RECEIPT from Starbucks, $5.75, 2025-05-28"}],
    )
    print(f"stop_reason: {response.stop_reason}")
    for block in response.content:
        if block.type == "tool_use":
            print(f"Tool chosen: {block.name}")
            print(f"Input: {block.input}")
    print()


def demonstrate_tool_choice_forced():
    """
    tool_choice: {"type": "tool", "name": "..."} — forces a SPECIFIC tool.
    Use when: a prerequisite tool must run first (extract_metadata before enrichment).
    """
    tools = [
        {
            "name": "extract_metadata",
            "description": "Extract document metadata: title, author, date, document_type",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                    "date": {"type": "string"},
                    "document_type": {"type": "string", "enum": ["invoice", "contract", "report", "other"]},
                },
            },
        },
        {
            "name": "enrich_document",
            "description": "Enrich document data with additional context",
            "input_schema": {
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
            },
        },
    ]

    print("=== tool_choice: forced — must call 'extract_metadata' first ===")
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=tools,
        tool_choice={"type": "tool", "name": "extract_metadata"},  # FORCED
        messages=[{"role": "user", "content": "Process this document: Annual Report Q4 2024 by Acme Corp"}],
    )
    print(f"stop_reason: {response.stop_reason}")
    for block in response.content:
        if block.type == "tool_use":
            print(f"Tool called: {block.name} (was forced)")
            print(f"Input: {block.input}")
    print()
    print("After getting metadata, subsequent turn uses 'auto' for enrichment.")


# ─── Scoped cross-role tool (Exam Q9 pattern) ─────────────────────────────────

def demonstrate_scoped_cross_role_tool():
    """
    Exam Q9: Synthesis agent needs verification 85% of the time for simple facts.
    Wrong: Give synthesis agent all web search tools (over-provisions, violates separation)
    Wrong: Route ALL verifications through coordinator (40% latency increase)
    Correct: Give synthesis agent a SCOPED verify_fact tool for simple lookups

    Complex verifications (15%) still route through coordinator → web search agent.
    """
    synthesis_verify_tool = {
        "name": "verify_fact",
        "description": (
            "Quickly verify a simple factual claim: a date, a statistic, a name, "
            "or a publicly known fact. Returns: supported/contradicted/uncertain + source. "
            "Use for simple verifications that don't require full web research. "
            "For complex multi-step verification, return a 'needs_coordinator_verification' "
            "signal instead of attempting it yourself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "The specific claim to verify"},
                "context": {"type": "string", "description": "Supporting context for the claim"},
            },
            "required": ["claim"],
        },
    }

    print("=== Scoped Cross-Role Tool: verify_fact for Synthesis Agent ===")
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=[synthesis_verify_tool],
        tool_choice={"type": "any"},
        messages=[{
            "role": "user",
            "content": (
                "I'm writing a synthesis report. Verify this claim from a source: "
                "'The Eiffel Tower was completed in 1889.'"
            )
        }],
    )
    for block in response.content:
        if block.type == "tool_use":
            print(f"verify_fact called: {block.input}")
    print("Simple facts handled locally — no coordinator round-trip needed.")
    print("Complex verifications would be flagged for coordinator → search agent routing.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 2.3: Tool Distribution and tool_choice Configuration")
    print("=" * 60)

    print(f"\nOVERPROVISIONING anti-pattern: {len(OVERPROVISION_TOOLS)} tools per agent")
    print(f"CORRECT: Search={len(SEARCH_AGENT_TOOLS)}, Analysis={len(ANALYSIS_AGENT_TOOLS)}, Synthesis={len(SYNTHESIS_AGENT_TOOLS)} tools")

    demonstrate_tool_choice_auto()
    demonstrate_tool_choice_any()
    demonstrate_tool_choice_forced()
    demonstrate_scoped_cross_role_tool()

    print("\n" + "=" * 60)
    print("tool_choice summary:")
    print("  'auto'  → model chooses whether to call a tool")
    print("  'any'   → model must call a tool (guarantees structured output)")
    print("  forced  → model must call this specific tool (prerequisites)")
    print("  'none'  → model cannot call any tool")


if __name__ == "__main__":
    main()
