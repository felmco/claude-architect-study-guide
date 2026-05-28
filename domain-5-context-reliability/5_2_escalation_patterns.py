"""
Task Statement 5.2: Design effective escalation and ambiguity resolution patterns

Key concepts:
- Escalate when: customer explicitly requests human, policy gap/exception, no progress
- Honor explicit "I want a human" requests IMMEDIATELY — no negotiation
- Sentiment-based escalation is unreliable (frustration ≠ complexity)
- Multiple matches → request additional identifier, don't heuristic-select
- Policy gap: escalate when policy is silent on the specific case

Exam Q3: Agent escalates easy cases (standard replacements) and handles complex ones.
Root cause: Unclear escalation decision boundaries.
Fix: Explicit criteria + few-shot examples.
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Escalation system prompt with explicit criteria ───────────────────────────

ESCALATION_SYSTEM_PROMPT = """You are a customer support agent.

ESCALATION CRITERIA (specific trigger conditions, not sentiment):

ALWAYS ESCALATE IMMEDIATELY:
1. Customer EXPLICITLY requests a human agent — "I want to speak to a person",
   "Transfer me to a manager", "I need a real human" → escalate WITHOUT attempting resolution
2. Refund amount exceeds $500 → requires human approval
3. Policy gap — situation your policy doesn't address (see Policy Gap examples below)
4. Unable to make meaningful progress after 2 attempts

POLICY GAP EXAMPLES (escalate these):
- Customer asks for competitor price match: policy only covers own-site adjustments
- Customer requests refund on digital download: policy doesn't address digital goods
- Customer requests loyalty points as refund: not mentioned in standard policy
- Customer claims allergic reaction to product: safety/liability issue exceeds agent scope

DO NOT ESCALATE based on:
- Customer frustration, anger, or negative language alone
- Issue "seeming complex" without a specific escalation trigger
- Your uncertainty about the outcome (if you can attempt resolution, try first)

WHEN CASE IS AMBIGUOUS (multiple matching customers):
- Ask for an additional identifier: "Can you provide your order number or phone number?"
- Do NOT guess based on name similarity or most recent activity
- Never select a customer account based on heuristics

FEW-SHOT EXAMPLES:

ESCALATE:
  "I want to speak with a manager right now!" → Escalate immediately, no negotiation
  "My refund request is for $750" → Exceeds $500 limit, escalate
  "I want to return this digital course" → Policy gap (digital goods not covered)

DO NOT ESCALATE (resolve it):
  "This is absolutely ridiculous! I need a refund for my broken widget" → Resolve: standard damage case
  "I've been waiting 3 weeks for this order!" → Resolve: check tracking, offer expedite/refund
  "Nobody seems to care about my problem" → Acknowledge frustration, then resolve underlying issue
"""

ESCALATION_TOOLS = [
    {
        "name": "resolve_autonomously",
        "description": "Resolve the issue without human escalation (issue is within policy and agent capability)",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_taken": {"type": "string"},
                "resolution": {"type": "string"},
            },
            "required": ["action_taken", "resolution"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Transfer to human agent. Use ONLY when: (1) customer requests human, (2) >$500 refund, (3) policy gap, (4) no progress after 2 attempts",
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {
                    "type": "string",
                    "enum": ["customer_requested", "amount_exceeded", "policy_gap", "no_progress"],
                    "description": "Why escalation is needed",
                },
                "summary": {"type": "string", "description": "Case summary for human agent"},
                "recommended_action": {"type": "string"},
            },
            "required": ["trigger", "summary", "recommended_action"],
        },
    },
    {
        "name": "request_clarification",
        "description": "Ask customer for additional information (e.g., order number when multiple accounts match)",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "What to ask the customer"},
                "reason": {"type": "string", "description": "Why this info is needed"},
            },
            "required": ["question"],
        },
    },
]


def evaluate_escalation_decision(customer_request: str) -> dict:
    """
    Evaluate whether a customer request should be escalated or resolved autonomously.
    Returns the tool called and its inputs.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=ESCALATION_SYSTEM_PROMPT,
        tools=ESCALATION_TOOLS,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": customer_request}],
    )

    for block in response.content:
        if block.type == "tool_use":
            return {"decision": block.name, "input": block.input}

    return {"decision": "text_response", "input": {"text": " ".join(
        b.text for b in response.content if hasattr(b, "text")
    )}}


def demonstrate_escalation_scenarios():
    """
    Test various scenarios to verify escalation criteria work correctly.
    """
    test_cases = [
        # Should ESCALATE (customer requested human)
        ("I want to speak to a manager RIGHT NOW", "customer_requested"),

        # Should ESCALATE (policy gap — competitor price match)
        ("I found the same product on Amazon for $20 less. Can you match that price?", "policy_gap"),

        # Should NOT escalate (emotional but resolvable)
        ("This is absolutely unacceptable! I need a refund for my broken widget that arrived damaged.", "should_resolve"),

        # Should request clarification (ambiguous customer match)
        ("My name is John Smith, I need help with my order", "should_clarify"),
    ]

    print("=== Escalation Decision Evaluation ===\n")
    for request, expected_type in test_cases:
        result = evaluate_escalation_decision(request)
        print(f"Request: '{request[:80]}...'")
        print(f"Expected: {expected_type}")
        print(f"Decision: {result['decision']} → {str(result['input'])[:150]}")
        print()


# ─── Anti-patterns ────────────────────────────────────────────────────────────

def demonstrate_bad_escalation_patterns():
    """Shows escalation anti-patterns to avoid."""

    print("=== Escalation Anti-Patterns ===\n")

    print("ANTI-PATTERN 1: Sentiment-based escalation")
    print("  Agent escalates when 'negative sentiment exceeds threshold'")
    print("  Problem: Frustrated customers with SIMPLE issues get escalated unnecessarily")
    print("  This is why Exam Q3 Agent achieves only 55% first-contact resolution")
    print("  Fix: Escalate on specific CRITERIA, not emotion level")
    print()

    print("ANTI-PATTERN 2: Confidence-based escalation")
    print("  Agent self-reports confidence 1-10 and escalates if < 7")
    print("  Problem: LLM confidence scores are poorly calibrated")
    print("  The agent is incorrectly confident on hard cases and uncertain on easy ones")
    print("  Fix: Explicit categorical criteria (see escalation system prompt above)")
    print()

    print("ANTI-PATTERN 3: Trying to negotiate before honoring human request")
    print("  Customer: 'I want to speak to a person'")
    print("  Agent: 'I can help you with that! Let me first try to resolve...'")
    print("  WRONG: Honor the request IMMEDIATELY, no negotiation")
    print("  Correct: Escalate instantly when customer explicitly requests human")
    print()

    print("ANTI-PATTERN 4: Heuristic customer selection")
    print("  2 accounts match 'John Smith'")
    print("  Agent picks the one with most recent activity — WRONG")
    print("  Correct: Request additional identifier (order number, phone, email)")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.2: Escalation Patterns and Ambiguity Resolution")
    print("=" * 60)

    demonstrate_escalation_scenarios()
    demonstrate_bad_escalation_patterns()

    print("\n" + "=" * 60)
    print("Escalation triggers: explicit request / >$500 / policy gap / no progress")
    print("NOT based on: sentiment, confidence scores, or issue complexity alone")


if __name__ == "__main__":
    main()
