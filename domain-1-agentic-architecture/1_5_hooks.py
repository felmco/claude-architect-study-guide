"""
Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization

Key concepts:
- PostToolUse hooks: transform tool results BEFORE the model processes them
- PreToolUse hooks: intercept outgoing tool calls to enforce compliance rules
- Hooks provide DETERMINISTIC guarantees vs prompt-based PROBABILISTIC compliance
- Use hooks for: data normalization, policy enforcement, logging, circuit breakers

Note: The Agent SDK hook API (PreToolUse/PostToolUse) runs at the SDK level.
This file simulates hook behavior using Python wrapper patterns.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")

REFUND_LIMIT_USD = 500.0  # Business rule: refunds > $500 require human approval


# ─── Hook system implementation ────────────────────────────────────────────────

class HookResult:
    """Result from a hook — can block, modify, or pass through."""

    def __init__(self, allow: bool, modified_result: Optional[Any] = None, reason: str = ""):
        self.allow = allow
        self.modified_result = modified_result
        self.reason = reason


# Pre-tool hooks: intercept BEFORE execution
pre_tool_hooks: dict[str, Callable] = {}
# Post-tool hooks: transform results AFTER execution
post_tool_hooks: dict[str, Callable] = {}


def pre_tool_hook(tool_name: str):
    """Decorator to register a pre-tool hook."""
    def decorator(fn):
        pre_tool_hooks[tool_name] = fn
        return fn
    return decorator


def post_tool_hook(tool_name: str):
    """Decorator to register a post-tool hook."""
    def decorator(fn):
        post_tool_hooks[tool_name] = fn
        return fn
    return decorator


# ─── Hook implementations ──────────────────────────────────────────────────────

@pre_tool_hook("process_refund")
def enforce_refund_limit(tool_input: dict) -> HookResult:
    """
    PRE-TOOL HOOK: Block refunds exceeding the business limit.

    This is DETERMINISTIC — no LLM can bypass it via clever prompting.
    Compare to prompt-only: "Only approve refunds under $500" — probabilistic.
    """
    amount = tool_input.get("amount", 0)

    if amount > REFUND_LIMIT_USD:
        print(f"  [HOOK] process_refund BLOCKED: ${amount} > ${REFUND_LIMIT_USD} limit")
        return HookResult(
            allow=False,
            modified_result={
                "isError": True,
                "errorCategory": "business",
                "isRetryable": False,
                "message": (
                    f"Refund of ${amount} exceeds the ${REFUND_LIMIT_USD} autonomous limit. "
                    "Escalation to human agent required."
                ),
                "redirect_to": "escalate_to_human",
            },
            reason=f"Refund amount ${amount} exceeds limit",
        )

    print(f"  [HOOK] process_refund ALLOWED: ${amount}")
    return HookResult(allow=True)


@post_tool_hook("lookup_order")
def normalize_order_data(raw_result: dict) -> dict:
    """
    POST-TOOL HOOK: Normalize heterogeneous data formats before model processes them.

    Real MCP tools return data in inconsistent formats:
    - Timestamps: Unix epoch, ISO 8601, "2025-05-28"
    - Status codes: 0/1 integers, "active"/"inactive", "delivered"/"in_transit"

    The hook normalizes ALL tools to a consistent format the model can reason about.
    """
    if raw_result.get("isError"):
        return raw_result

    normalized = dict(raw_result)

    # Normalize Unix timestamps → ISO 8601
    if "created_ts" in normalized:
        ts = normalized.pop("created_ts")
        normalized["created_at"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    if "delivery_ts" in normalized:
        ts = normalized.pop("delivery_ts")
        normalized["delivered_at"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    # Normalize numeric status codes → human-readable strings
    status_map = {0: "pending", 1: "processing", 2: "shipped", 3: "delivered", 4: "cancelled"}
    if "status_code" in normalized:
        code = normalized.pop("status_code")
        normalized["status"] = status_map.get(code, f"unknown({code})")

    # Normalize boolean integers
    if "is_returnable" in normalized:
        normalized["is_returnable"] = bool(normalized["is_returnable"])

    print(f"  [HOOK] Normalized order data: removed raw ts/codes, added ISO dates/strings")
    return normalized


@post_tool_hook("get_customer")
def normalize_customer_data(raw_result: dict) -> dict:
    """
    POST-TOOL HOOK: Normalize customer data from CRM system.
    CRM returns phone as integer, membership_since as Unix timestamp.
    """
    if raw_result.get("isError"):
        return raw_result

    normalized = dict(raw_result)

    # Phone stored as integer in legacy CRM
    if "phone_int" in normalized:
        phone = str(normalized.pop("phone_int"))
        normalized["phone"] = f"+1-{phone[:3]}-{phone[3:6]}-{phone[6:]}"

    # Membership date as Unix timestamp
    if "member_since_ts" in normalized:
        ts = normalized.pop("member_since_ts")
        normalized["member_since"] = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

    # Account tier as integer
    tier_map = {1: "standard", 2: "silver", 3: "gold", 4: "platinum"}
    if "tier_id" in normalized:
        normalized["tier"] = tier_map.get(normalized.pop("tier_id"), "unknown")

    return normalized


# ─── Simulated tool implementations ───────────────────────────────────────────

def _raw_lookup_order(order_number: str) -> dict:
    """Simulates raw MCP tool returning inconsistent formats."""
    return {
        "order_id": order_number,
        "customer_id": "CUST-1234",
        "total": 125.00,
        "status_code": 3,          # ← integer status code (needs normalization)
        "created_ts": 1748390400,  # ← Unix timestamp (needs normalization)
        "delivery_ts": 1748649600, # ← Unix timestamp (needs normalization)
        "is_returnable": 1,        # ← integer boolean (needs normalization)
        "items": [{"sku": "WIDGET-A", "qty": 2}],
    }


def _raw_get_customer(email: str) -> dict:
    """Simulates legacy CRM returning inconsistent types."""
    return {
        "customer_id": "CUST-1234",
        "email": email,
        "name": "Jane Smith",
        "phone_int": 5551234567,    # ← integer phone (needs normalization)
        "member_since_ts": 1577836800,  # ← Unix timestamp (needs normalization)
        "tier_id": 2,               # ← integer tier (needs normalization)
    }


def _raw_process_refund(order_id: str, amount: float, reason: str) -> dict:
    return {
        "refund_id": f"REF-{hash(order_id) % 1000:03d}",
        "amount": amount,
        "status": "approved",
    }


def _raw_escalate_to_human(customer_id: str, root_cause: str, amount: float, action: str) -> dict:
    return {
        "escalation_id": f"ESC-{hash(customer_id) % 1000:03d}",
        "assigned_to": "tier-2-support",
        "customer_id": customer_id,
        "root_cause": root_cause,
        "amount": amount,
        "action": action,
    }


# ─── Hook-aware tool executor ──────────────────────────────────────────────────

def execute_tool_with_hooks(tool_name: str, tool_input: dict) -> dict:
    """
    Execute a tool with pre/post hooks applied.

    1. Run PreToolUse hook → block or allow
    2. If allowed: execute tool
    3. Run PostToolUse hook → normalize result
    """
    # Step 1: Pre-tool hook
    if tool_name in pre_tool_hooks:
        hook_result = pre_tool_hooks[tool_name](tool_input)
        if not hook_result.allow:
            return hook_result.modified_result  # Return the hook's block response

    # Step 2: Execute the raw tool
    raw_dispatch = {
        "get_customer": lambda: _raw_get_customer(tool_input["email"]),
        "lookup_order": lambda: _raw_lookup_order(tool_input["order_number"]),
        "process_refund": lambda: _raw_process_refund(
            tool_input["order_id"], tool_input["amount"], tool_input["reason"]
        ),
        "escalate_to_human": lambda: _raw_escalate_to_human(
            tool_input["customer_id"], tool_input["root_cause"],
            tool_input["refund_amount"], tool_input["recommended_action"]
        ),
    }

    fn = raw_dispatch.get(tool_name)
    if fn is None:
        return {"isError": True, "message": f"Unknown tool: {tool_name}"}

    result = fn()

    # Step 3: Post-tool hook (normalization)
    if tool_name in post_tool_hooks:
        result = post_tool_hooks[tool_name](result)

    return result


# ─── Full agent with hook system ───────────────────────────────────────────────

HOOK_TOOLS = [
    {
        "name": "get_customer",
        "description": "Verify customer identity by email. Returns normalized customer data.",
        "input_schema": {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]},
    },
    {
        "name": "lookup_order",
        "description": "Look up order details. Returns normalized order data with ISO timestamps.",
        "input_schema": {"type": "object", "properties": {"order_number": {"type": "string"}}, "required": ["order_number"]},
    },
    {
        "name": "process_refund",
        "description": "Process a refund. Amounts over $500 are automatically escalated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["order_id", "amount", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate to human agent with structured handoff context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "root_cause": {"type": "string"},
                "refund_amount": {"type": "number"},
                "recommended_action": {"type": "string"},
            },
            "required": ["customer_id", "root_cause", "refund_amount", "recommended_action"],
        },
    },
]


def run_agent_with_hooks(request: str) -> str:
    messages = [{"role": "user", "content": request}]
    system = "You are a customer support agent. Verify customer first, then look up order, then process request."

    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=system, tools=HOOK_TOOLS, messages=messages
        )

        if response.stop_reason == "end_turn":
            return " ".join(b.text for b in response.content if hasattr(b, "text"))

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n  Tool call: {block.name}({block.input})")
                    result = execute_tool_with_hooks(block.name, block.input)
                    print(f"  Final result (post-hooks): {json.dumps(result, indent=2)[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})

    return ""


def main():
    print("=" * 60)
    print("Task 1.5: Agent SDK Hooks — Interception & Normalization")
    print("=" * 60)

    print("\n--- Test 1: Normal refund (under $500 limit) ---")
    result1 = run_agent_with_hooks(
        "Customer email: jane@example.com. Refund order ORD-5678 for $125. Item was defective."
    )
    print(f"\nAgent response: {result1}")

    print("\n--- Test 2: Large refund (over $500 limit — hook blocks it) ---")
    result2 = run_agent_with_hooks(
        "Customer email: jane@example.com. Refund order ORD-5678 for $750. Item was defective."
    )
    print(f"\nAgent response: {result2}")

    print("\n" + "=" * 60)
    print("Hooks provide DETERMINISTIC enforcement.")
    print("PostToolUse normalizes raw tool data before model sees it.")
    print("PreToolUse blocks policy violations regardless of prompt instructions.")


if __name__ == "__main__":
    main()
