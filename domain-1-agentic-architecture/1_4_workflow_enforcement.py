"""
Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns

Key concepts:
- Programmatic prerequisites BLOCK downstream tool calls until prerequisites complete
- Prompt-only enforcement has non-zero failure rate (insufficient for financial operations)
- Structured handoff: customer_id, root_cause, refund_amount, recommended_action
- Parallel investigation of multi-concern requests → unified resolution

THIS IS THE MOST EXAM-CRITICAL CONCEPT IN DOMAIN 1.
Sample Question 1: programmatic prerequisite vs prompt-only enforcement.
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Simulated backend state ───────────────────────────────────────────────────

class WorkflowState:
    """Tracks which prerequisites have been satisfied."""

    def __init__(self):
        self._verified_customer_id: Optional[str] = None
        self._lookup_order_id: Optional[str] = None

    def set_verified_customer(self, customer_id: str):
        self._verified_customer_id = customer_id

    def get_verified_customer_id(self) -> Optional[str]:
        return self._verified_customer_id

    def set_looked_up_order(self, order_id: str):
        self._lookup_order_id = order_id

    def get_looked_up_order_id(self) -> Optional[str]:
        return self._lookup_order_id


state = WorkflowState()


# ─── Tool implementations with programmatic prerequisites ──────────────────────

def get_customer(email: str) -> dict:
    """Step 1: Verify customer identity. Returns verified customer_id."""
    # Simulate customer lookup
    if "@" not in email:
        return {"isError": True, "errorCategory": "validation", "message": "Invalid email format"}

    customer_id = f"CUST-{hash(email) % 10000:04d}"
    state.set_verified_customer(customer_id)
    return {
        "customer_id": customer_id,
        "email": email,
        "name": "Jane Smith",
        "account_status": "active",
    }


def lookup_order(order_number: str) -> dict:
    """Step 2: Look up order details. BLOCKS if customer not verified."""
    # PROGRAMMATIC PREREQUISITE: Cannot proceed without verified customer
    verified_id = state.get_verified_customer_id()
    if verified_id is None:
        return {
            "isError": True,
            "errorCategory": "business",
            "isRetryable": False,
            "message": (
                "Customer identity must be verified via get_customer before "
                "looking up orders. Call get_customer first."
            ),
        }

    # Simulate order lookup
    state.set_looked_up_order(order_number)
    return {
        "order_id": order_number,
        "customer_id": verified_id,  # Confirms ownership
        "items": [{"sku": "WIDGET-A", "qty": 2, "price": 12.50}],
        "total": 25.00,
        "status": "delivered",
        "delivery_date": "2025-05-20",
    }


def process_refund(order_id: str, amount: float, reason: str) -> dict:
    """Step 3: Process refund. BLOCKS until BOTH get_customer AND lookup_order complete."""
    # PROGRAMMATIC PREREQUISITE: Must have verified customer AND looked up order
    verified_id = state.get_verified_customer_id()
    looked_up_order = state.get_looked_up_order_id()

    if verified_id is None:
        return {
            "isError": True,
            "errorCategory": "business",
            "isRetryable": False,
            "message": "Cannot process refund: customer identity not verified. Call get_customer first.",
        }

    if looked_up_order is None:
        return {
            "isError": True,
            "errorCategory": "business",
            "isRetryable": False,
            "message": "Cannot process refund: order not verified. Call lookup_order first.",
        }

    if looked_up_order != order_id:
        return {
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"Order {order_id} was not verified. Verified order is {looked_up_order}.",
        }

    return {
        "refund_id": f"REF-{hash(order_id) % 10000:04d}",
        "order_id": order_id,
        "customer_id": verified_id,
        "amount": amount,
        "status": "approved",
    }


def escalate_to_human(customer_id: str, root_cause: str, refund_amount: float, recommended_action: str) -> dict:
    """Escalate to human agent with structured handoff."""
    # Structured handoff — human agents don't have access to conversation transcript
    handoff = {
        "escalation_id": f"ESC-{hash(customer_id) % 10000:04d}",
        "customer_id": customer_id,
        "root_cause": root_cause,
        "refund_amount_requested": refund_amount,
        "recommended_action": recommended_action,
        "priority": "high" if refund_amount > 100 else "normal",
    }
    print(f"\n[ESCALATION] Human handoff created: {json.dumps(handoff, indent=2)}")
    return handoff


# ─── Agent with programmatic enforcement ───────────────────────────────────────

TOOLS_WITH_ENFORCEMENT = [
    {
        "name": "get_customer",
        "description": (
            "REQUIRED FIRST STEP. Verify a customer's identity using their email address. "
            "Returns a verified customer_id. This MUST be called before lookup_order or "
            "process_refund — those tools will return an error if called first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email address"},
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Look up an order by order number. Requires get_customer to have been called first "
            "to verify customer identity. Returns order details including items, total, and status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {"type": "string", "description": "Order number, e.g. 'ORD-1234'"},
            },
            "required": ["order_number"],
        },
    },
    {
        "name": "process_refund",
        "description": (
            "Process a refund for a specific order. Requires BOTH get_customer AND lookup_order "
            "to have been called successfully first. Returns refund confirmation ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number", "description": "Refund amount in USD"},
                "reason": {"type": "string", "description": "Reason for refund"},
            },
            "required": ["order_id", "amount", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalate a case to a human agent with a structured handoff. Include all context "
            "the human agent needs since they cannot see the conversation transcript. "
            "Use when: policy exceptions required, customer explicitly requests human, "
            "or agent cannot make progress."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "root_cause": {"type": "string", "description": "Why the customer needs help"},
                "refund_amount": {"type": "number"},
                "recommended_action": {"type": "string"},
            },
            "required": ["customer_id", "root_cause", "refund_amount", "recommended_action"],
        },
    },
]

TOOL_DISPATCH = {
    "get_customer": lambda inp: get_customer(inp["email"]),
    "lookup_order": lambda inp: lookup_order(inp["order_number"]),
    "process_refund": lambda inp: process_refund(inp["order_id"], inp["amount"], inp["reason"]),
    "escalate_to_human": lambda inp: escalate_to_human(
        inp["customer_id"], inp["root_cause"], inp["refund_amount"], inp["recommended_action"]
    ),
}


def run_support_agent(request: str) -> str:
    """Run the customer support agent with programmatic workflow enforcement."""
    # Reset state for each new request
    global state
    state = WorkflowState()

    messages = [{"role": "user", "content": request}]
    system = (
        "You are a customer support agent. Always verify customer identity first, "
        "then look up their order, then process any refund. "
        "For escalations, include the customer_id, root_cause, refund_amount, and recommended_action."
    )

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=TOOLS_WITH_ENFORCEMENT,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return " ".join(b.text for b in response.content if hasattr(b, "text"))

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"  Tool: {block.name}({block.input})")
                    fn = TOOL_DISPATCH.get(block.name)
                    result = fn(block.input) if fn else {"error": "unknown tool"}
                    print(f"  Result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})

    return ""


# ─── Demonstrate prompt-only (insufficient) ────────────────────────────────────

def demonstrate_prompt_only_failure():
    """
    Shows why prompt-only enforcement fails ~12% of the time.

    From the exam: "Production data shows that in 12% of cases, your agent
    skips get_customer entirely and calls lookup_order using only the customer's
    stated name, occasionally leading to misidentified accounts."

    Correct answer: programmatic prerequisite (A), NOT prompt instructions (B).
    """
    print("\nPROMPT-ONLY approach (insufficient for financial operations):")
    print("System: 'Always call get_customer before lookup_order'")
    print("Problem: LLM compliance is probabilistic, not deterministic.")
    print("12% failure rate → wrong accounts → incorrect refunds")
    print()
    print("PROGRAMMATIC approach (exam correct answer):")
    print("lookup_order() checks state.get_verified_customer_id() — blocks if None")
    print("This gives DETERMINISTIC guarantees regardless of LLM behavior.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.4: Workflow Enforcement & Structured Handoffs")
    print("=" * 60)

    demonstrate_prompt_only_failure()

    print("\n--- Running agent with programmatic enforcement ---")
    request = (
        "My email is jane@example.com. I need a refund for order ORD-5678. "
        "It was damaged in shipping. The order total was $25."
    )
    print(f"User: {request}")
    result = run_support_agent(request)
    print(f"\nAgent: {result}")

    print("\n" + "=" * 60)
    print("Key: Programmatic prerequisites = deterministic enforcement.")
    print("Prompt-only = probabilistic, insufficient for financial operations.")


if __name__ == "__main__":
    main()
