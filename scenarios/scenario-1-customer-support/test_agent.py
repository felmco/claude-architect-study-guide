"""
Unit tests for Scenario 1: Customer Support Agent

Tests:
1. Programmatic tool ordering enforcement
2. Hook: refund limit blocking
3. Escalation criteria correctness
4. Tool selection with similar descriptions

Run: pytest test_agent.py -v
"""

import json
import pytest
from unittest.mock import MagicMock, patch

# Import from agent (adjust path as needed)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from agent import execute_tool, WorkflowState, REFUND_LIMIT


# ─── Test 1: Programmatic workflow enforcement ─────────────────────────────────

def test_lookup_order_blocked_without_customer():
    """lookup_order must return error if get_customer not called first."""
    state = WorkflowState()  # Fresh state, no customer verified
    result = execute_tool("lookup_order", {"order_number": "ORD-5678"}, state)
    assert result["isError"] is True
    assert result["errorCategory"] == "business"
    assert "get_customer" in result["message"].lower()


def test_process_refund_blocked_without_customer():
    """process_refund blocked when customer not verified."""
    state = WorkflowState()
    result = execute_tool("process_refund", {"order_id": "ORD-5678", "amount": 25.0, "reason": "test"}, state)
    assert result["isError"] is True
    assert "get_customer" in result["message"].lower()


def test_process_refund_blocked_without_order_lookup():
    """process_refund blocked when order not looked up, even if customer verified."""
    state = WorkflowState()
    state.set_customer({"customer_id": "CUST-1234", "session_token": "sess-test"})
    # No lookup_order called — order not in state
    result = execute_tool("process_refund", {"order_id": "ORD-5678", "amount": 25.0, "reason": "test"}, state)
    assert result["isError"] is True
    assert "lookup_order" in result["message"].lower()


def test_correct_workflow_succeeds():
    """Full correct flow: get_customer → lookup_order → process_refund."""
    state = WorkflowState()

    # Step 1: Verify customer
    r1 = execute_tool("get_customer", {"email": "jane@example.com"}, state)
    assert not r1.get("isError"), f"get_customer failed: {r1}"
    assert state.is_customer_verified()

    # Step 2: Look up order
    r2 = execute_tool("lookup_order", {"order_number": "ORD-5678"}, state)
    assert not r2.get("isError") and r2.get("found", True), f"lookup_order failed: {r2}"
    assert state.is_order_verified("ORD-5678")

    # Step 3: Process refund (within limit)
    r3 = execute_tool("process_refund", {"order_id": "ORD-5678", "amount": 25.0, "reason": "defective"}, state)
    assert not r3.get("isError"), f"process_refund failed: {r3}"
    assert "refund_id" in r3


# ─── Test 2: Hook — refund limit ───────────────────────────────────────────────

def test_hook_blocks_large_refund():
    """Refunds > $500 should be blocked by the enforcement hook."""
    state = WorkflowState()
    state.set_customer({"customer_id": "CUST-1234", "session_token": "sess-test"})
    state.set_order("ORD-9999", {"order_id": "ORD-9999", "customer_id": "CUST-1234", "total": 599.0})

    result = execute_tool("process_refund", {
        "order_id": "ORD-9999",
        "amount": 599.0,  # Over $500 limit
        "reason": "not as described"
    }, state)

    assert result["isError"] is True
    assert result["errorCategory"] == "business"
    assert result.get("requires_escalation") is True
    assert "500" in result["message"]


def test_refund_at_limit_boundary():
    """Refund exactly at $500 should succeed."""
    state = WorkflowState()
    state.set_customer({"customer_id": "CUST-1234", "session_token": "sess-test"})
    state.set_order("ORD-5678", {"order_id": "ORD-5678", "customer_id": "CUST-1234", "total": 500.0})

    result = execute_tool("process_refund", {
        "order_id": "ORD-5678",
        "amount": REFUND_LIMIT,  # Exactly $500 — should be allowed
        "reason": "test"
    }, state)
    assert not result.get("isError"), f"Exact limit should be allowed: {result}"


# ─── Test 3: Structured error categories ──────────────────────────────────────

def test_unknown_customer_returns_validation_error():
    """Unknown email should return validation error, not system error."""
    state = WorkflowState()
    result = execute_tool("get_customer", {"email": "unknown@nowhere.com"}, state)
    assert result["isError"] is True
    assert result["errorCategory"] == "validation"
    assert result["isRetryable"] is False


def test_order_not_found_is_not_an_error():
    """Valid query with no results should NOT set isError (it's just empty)."""
    state = WorkflowState()
    state.set_customer({"customer_id": "CUST-1234", "session_token": "sess-test"})

    result = execute_tool("lookup_order", {"order_number": "ORD-NONEXISTENT"}, state)
    # Valid query with no match = isError False (distinguishes from access failure)
    assert result.get("isError") is False or result.get("found") is False


# ─── Test 4: Escalation tool ──────────────────────────────────────────────────

def test_escalate_to_human_returns_structured_handoff():
    """escalate_to_human should return structured handoff with all required fields."""
    state = WorkflowState()
    result = execute_tool("escalate_to_human", {
        "customer_id": "CUST-1234",
        "root_cause": "Customer requests refund for high-value item exceeding autonomous limit",
        "refund_amount": 599.0,
        "recommended_action": "Verify item condition and process refund if eligible",
    }, state)

    assert "escalation_id" in result
    assert result["customer_id"] == "CUST-1234"
    assert result["refund_amount"] == 599.0
    assert result["recommended_action"]  # Not empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
