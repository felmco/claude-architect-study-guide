"""
Task Statement 2.2: Implement structured error responses for MCP tools

Key concepts:
- isError flag: signals tool failure back to the agent
- errorCategory: transient / validation / permission / business
- isRetryable: boolean — prevents wasted retry attempts
- Uniform generic errors prevent intelligent agent recovery
- Access failure vs valid empty result — VERY different semantics
- Local recovery in subagents before propagating to coordinator
"""

import json
import os
import time
import random
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Error category definitions ───────────────────────────────────────────────

ERROR_CATEGORIES = {
    "transient": {
        "description": "Temporary failure — service unavailable, timeout, rate limit",
        "isRetryable": True,
        "agent_action": "Retry with exponential backoff",
        "examples": ["503 Service Unavailable", "Connection timeout", "Rate limit exceeded"],
    },
    "validation": {
        "description": "Invalid input — wrong format, missing required field",
        "isRetryable": False,
        "agent_action": "Fix input and retry (or ask user for correct input)",
        "examples": ["Invalid email format", "Order number must start with 'ORD-'", "Amount must be positive"],
    },
    "permission": {
        "description": "Unauthorized — missing credentials, insufficient scope",
        "isRetryable": False,
        "agent_action": "Escalate or inform user of permission requirements",
        "examples": ["Customer not verified", "Insufficient role for this operation"],
    },
    "business": {
        "description": "Policy violation — valid input, but business rule prevents execution",
        "isRetryable": False,
        "agent_action": "Inform user of policy, offer alternatives (escalation, etc.)",
        "examples": ["Refund exceeds $500 limit", "Return window expired", "Order already refunded"],
    },
}


# ─── Structured error builder ──────────────────────────────────────────────────

def make_error(
    category: str,
    message: str,
    is_retryable: Optional[bool] = None,
    customer_message: Optional[str] = None,
    alternative_action: Optional[str] = None,
) -> dict:
    """
    Create a structured MCP error response.

    The isRetryable field prevents the agent from wasting retry attempts
    on errors that will never succeed (business rules, permission violations).
    """
    error_info = ERROR_CATEGORIES.get(category, {})
    return {
        "isError": True,
        "errorCategory": category,
        "isRetryable": is_retryable if is_retryable is not None else error_info.get("isRetryable", False),
        "message": message,
        "customerMessage": customer_message or message,
        "alternativeAction": alternative_action,
    }


# ─── Tool implementations demonstrating each error type ────────────────────────

def search_database(query: str, simulate_failure: str = "none") -> dict:
    """
    Demonstrates all error types and the access_failure vs empty_result distinction.

    simulate_failure options: "none", "transient", "validation", "permission",
                               "business", "empty_result"
    """
    if simulate_failure == "transient":
        return make_error(
            category="transient",
            message="Database connection timeout after 5s. Service may be temporarily unavailable.",
            is_retryable=True,
            alternative_action="Retry in 2-5 seconds. If persistent, check service status.",
        )

    if simulate_failure == "validation":
        return make_error(
            category="validation",
            message=f"Invalid query format: '{query}'. Query must be at least 3 characters.",
            is_retryable=False,
            customer_message="Please provide a more specific search term (at least 3 characters).",
        )

    if simulate_failure == "permission":
        return make_error(
            category="permission",
            message="Access denied: customer identity not verified. Call get_customer first.",
            is_retryable=False,
            alternative_action="Call get_customer to obtain session_token, then retry.",
        )

    if simulate_failure == "business":
        return make_error(
            category="business",
            message="Return window expired: order was delivered 45 days ago (limit: 30 days).",
            is_retryable=False,
            customer_message="Unfortunately, this order is outside the 30-day return window.",
            alternative_action="Customer may request manager review via escalate_to_human.",
        )

    if simulate_failure == "empty_result":
        # CORRECT: Empty result is NOT an error — it's a valid query with no matches
        # This is the KEY DISTINCTION from an access failure
        return {
            "isError": False,      # ← NOT an error!
            "found": False,        # ← Valid query, just no results
            "results": [],
            "query": query,
            "message": "No orders matching this query. This is a valid result, not a failure.",
        }

    # Successful result
    return {
        "isError": False,
        "found": True,
        "results": [{"id": "ORD-5678", "status": "delivered"}],
        "query": query,
    }


# ─── Anti-pattern: generic errors ─────────────────────────────────────────────

def bad_generic_error_response(error_type: str) -> dict:
    """
    ANTI-PATTERN: Generic error response that hides context.
    The agent cannot make intelligent recovery decisions from this.
    """
    return {
        "error": True,
        "message": "Operation failed",  # Useless! What failed? Why? Can we retry?
    }


# ─── Subagent local recovery pattern ──────────────────────────────────────────

def subagent_with_local_recovery(query: str) -> dict:
    """
    Subagent should handle transient failures locally before propagating to coordinator.
    Only propagate errors it cannot resolve, with full context.
    """
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        result = search_database(query, simulate_failure="transient" if attempt < 2 else "none")

        if not result.get("isError"):
            print(f"  Local recovery succeeded on attempt {attempt + 1}")
            return result

        if not result.get("isRetryable", False):
            # Non-retryable — propagate immediately with context
            print(f"  Non-retryable error — propagating to coordinator")
            return {
                "isError": True,
                "propagated_from_subagent": True,
                "failure_type": result["errorCategory"],
                "attempted_query": query,
                "attempts_made": attempt + 1,
                "partial_results": [],
                "alternative_approaches": ["Try a different search strategy", "Use cached results"],
                "original_error": result,
            }

        # Transient — retry with backoff
        wait = 0.1 * (2 ** attempt)
        print(f"  Transient error on attempt {attempt + 1}, retrying in {wait:.1f}s...")
        time.sleep(wait)
        last_error = result

    # All retries exhausted — propagate with context
    return {
        "isError": True,
        "propagated_from_subagent": True,
        "failure_type": "transient_exhausted",
        "attempted_query": query,
        "attempts_made": max_retries,
        "partial_results": [],
        "original_error": last_error,
        "alternative_approaches": ["Search is currently unavailable", "Fall back to cached data"],
    }


# ─── Demonstrate access failure vs empty result ────────────────────────────────

def demonstrate_access_vs_empty():
    """
    This distinction is critical for coordinator recovery decisions.

    ACCESS FAILURE: Something went wrong — coordinator should retry or use alternative
    EMPTY RESULT: Query worked fine, just no matching data — coordinator should not retry
    """
    print("=== Access Failure vs Valid Empty Result ===\n")

    access_failure = search_database("test", simulate_failure="transient")
    empty_result = search_database("ORD-NONEXISTENT", simulate_failure="empty_result")

    print("ACCESS FAILURE (retry warranted):")
    print(json.dumps(access_failure, indent=2))
    print()
    print("EMPTY RESULT (do NOT retry — query succeeded, no data exists):")
    print(json.dumps(empty_result, indent=2))
    print()
    print("Key: isError=True → access failure (retry decision needed)")
    print("     isError=False + found=False → empty result (don't retry)")


# ─── Run agent with structured error handling ──────────────────────────────────

TOOLS_WITH_STRUCTURED_ERRORS = [
    {
        "name": "search_orders",
        "description": (
            "Search for orders matching a query string. "
            "Returns structured error with errorCategory and isRetryable if the search fails. "
            "Transient errors (service unavailable) should be retried. "
            "Business errors (expired return window) should NOT be retried. "
            "A 'found: false' result is NOT an error — it means no matching orders exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "simulate_failure": {
                    "type": "string",
                    "enum": ["none", "transient", "validation", "permission", "business", "empty_result"],
                    "description": "For testing: simulate a specific failure type",
                },
            },
            "required": ["query"],
        },
    },
]


def main():
    print("=" * 60)
    print("Task 2.2: Structured Error Responses")
    print("=" * 60)

    print("\n=== Error Categories ===")
    for category, info in ERROR_CATEGORIES.items():
        print(f"\n{category.upper()}:")
        print(f"  Description: {info['description']}")
        print(f"  isRetryable: {info['isRetryable']}")
        print(f"  Agent action: {info['agent_action']}")

    print("\n=== Anti-pattern: Generic vs Structured Error ===")
    print("GENERIC (agent can't decide what to do):")
    print(json.dumps(bad_generic_error_response("timeout"), indent=2))
    print()
    print("STRUCTURED (agent knows exactly how to respond):")
    print(json.dumps(make_error("transient", "Database timeout", customer_message="Temporary issue, please try again."), indent=2))

    demonstrate_access_vs_empty()

    print("\n=== Subagent Local Recovery ===")
    result = subagent_with_local_recovery("ORD-5678")
    print(f"Final result: {json.dumps(result, indent=2)[:300]}...")


if __name__ == "__main__":
    main()
