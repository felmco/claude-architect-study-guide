"""
Scenario 1: Customer Support MCP Server

FastMCP server exposing 4 tools with detailed descriptions.
Demonstrates Task 2.1 (tool descriptions), Task 2.2 (structured errors),
Task 2.4 (MCP server setup).

Run this server directly to test tools:
  python mcp_server.py

Or configure it in .mcp.json for Claude Code to use it.
"""

import json
import random
from datetime import datetime, timezone
from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("customer-support-tools")

# ─── Simulated database ────────────────────────────────────────────────────────

CUSTOMERS = {
    "jane@example.com": {
        "customer_id": "CUST-1234",
        "name": "Jane Smith",
        "tier": "gold",
        "account_status": "active",
        "member_since": "2022-03-15",
    },
    "bob@example.com": {
        "customer_id": "CUST-5678",
        "name": "Bob Johnson",
        "tier": "standard",
        "account_status": "active",
        "member_since": "2023-07-01",
    },
}

ORDERS = {
    "ORD-5678": {
        "order_id": "ORD-5678",
        "customer_id": "CUST-1234",
        "items": [{"sku": "WIDGET-A", "qty": 2, "price": 12.50}],
        "total": 25.00,
        "status": "delivered",
        "delivery_date": "2025-05-20",
        "return_window_days": 30,
    },
    "ORD-9999": {
        "order_id": "ORD-9999",
        "customer_id": "CUST-1234",
        "items": [{"sku": "GADGET-X", "qty": 1, "price": 599.00}],
        "total": 599.00,
        "status": "delivered",
        "delivery_date": "2025-05-22",
        "return_window_days": 30,
    },
}

verified_customers: dict[str, str] = {}  # session_token → customer_id


# ─── Tool 1: get_customer ──────────────────────────────────────────────────────

@mcp.tool()
def get_customer(email: str) -> str:
    """
    REQUIRED FIRST STEP: Verify a customer's identity using their email address.

    Returns a verified customer_id, customer name, account tier, and account status.
    This tool MUST be called before lookup_order or process_refund — attempting
    to call those tools without first verifying the customer will result in an error.

    Use this tool when: the customer provides their email address, account number,
    or any identifying information. Always verify identity before accessing order data.

    Does NOT return: payment methods, password information, or full billing address.

    Examples:
      - Input: "jane@example.com" → verified customer_id returned
      - Input: "unknown@test.com" → error with message that customer was not found
    """
    customer = CUSTOMERS.get(email.lower())

    if customer is None:
        return json.dumps({
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"No customer found with email: {email}. Please verify the email address.",
        })

    # Register as verified in this session
    session_token = f"sess-{random.randint(1000, 9999)}"
    verified_customers[session_token] = customer["customer_id"]

    return json.dumps({
        "verified": True,
        "session_token": session_token,
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "tier": customer["tier"],
        "account_status": customer["account_status"],
        "member_since": customer["member_since"],
    })


# ─── Tool 2: lookup_order ──────────────────────────────────────────────────────

@mcp.tool()
def lookup_order(order_number: str, session_token: str) -> str:
    """
    Look up an order by order number to retrieve its details, status, and return eligibility.

    REQUIRES: get_customer must have been called first to obtain a session_token.
    Passing an invalid or missing session_token will result in an authentication error.

    Returns: order items, total, delivery status, delivery date, and whether the
    order is within the return window. Does NOT return payment method details.

    Use this tool when: customer asks about an order status, wants to return an item,
    or needs to know what was ordered. Use get_customer FIRST to get the session_token.

    Examples:
      - Input: order_number="ORD-5678", session_token="sess-1234" → full order details
      - Input: invalid session_token → authentication error requiring get_customer call
    """
    customer_id = verified_customers.get(session_token)

    if customer_id is None:
        return json.dumps({
            "isError": True,
            "errorCategory": "permission",
            "isRetryable": False,
            "message": (
                "Authentication required. Call get_customer first to obtain a session_token, "
                "then pass that token to lookup_order."
            ),
        })

    order = ORDERS.get(order_number)

    if order is None:
        return json.dumps({
            "isError": False,  # NOT an error — valid query with no results
            "found": False,
            "message": f"Order {order_number} not found. Verify the order number with the customer.",
        })

    # Verify the order belongs to the verified customer
    if order["customer_id"] != customer_id:
        return json.dumps({
            "isError": True,
            "errorCategory": "permission",
            "isRetryable": False,
            "message": f"Order {order_number} does not belong to the verified customer.",
        })

    # Calculate return eligibility
    delivery_date = datetime.strptime(order["delivery_date"], "%Y-%m-%d")
    days_since_delivery = (datetime.now() - delivery_date).days
    within_return_window = days_since_delivery <= order["return_window_days"]

    return json.dumps({
        **order,
        "return_eligible": within_return_window,
        "days_since_delivery": days_since_delivery,
    })


# ─── Tool 3: process_refund ───────────────────────────────────────────────────

@mcp.tool()
def process_refund(
    order_id: str,
    amount: float,
    reason: str,
    session_token: str,
) -> str:
    """
    Process a refund for a specific order. Issues a credit to the customer's original payment method.

    REQUIRES: Both get_customer (for session_token) and lookup_order must be called first.
    Refunds over $500 cannot be processed autonomously and will return an error
    indicating that escalation to a human agent is required.

    Use this tool when: customer is eligible for a refund and you have verified their
    identity (get_customer) and confirmed their order (lookup_order). Do NOT call
    this tool based only on customer-stated information without verification.

    Returns: refund confirmation ID, amount, and expected credit timeline.

    Examples:
      - Valid flow: get_customer → lookup_order → process_refund → confirmation
      - Invalid: process_refund called without prior get_customer → authentication error
    """
    customer_id = verified_customers.get(session_token)

    if customer_id is None:
        return json.dumps({
            "isError": True,
            "errorCategory": "permission",
            "isRetryable": False,
            "message": "get_customer must be called first to obtain session_token.",
        })

    # Verify order was looked up for this customer
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return json.dumps({
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"Order {order_id} must be verified via lookup_order before refund processing.",
        })

    # Business rule: amounts over $500 require human approval
    if amount > 500:
        return json.dumps({
            "isError": True,
            "errorCategory": "business",
            "isRetryable": False,
            "message": (
                f"Refund of ${amount:.2f} exceeds the $500 autonomous processing limit. "
                "Please escalate to a human agent using the escalate_to_human tool."
            ),
            "requires_escalation": True,
        })

    refund_id = f"REF-{random.randint(10000, 99999)}"
    return json.dumps({
        "refund_id": refund_id,
        "order_id": order_id,
        "amount": amount,
        "reason": reason,
        "status": "approved",
        "credit_timeline": "3-5 business days",
        "confirmation_sent_to": "customer email on file",
    })


# ─── Tool 4: escalate_to_human ────────────────────────────────────────────────

@mcp.tool()
def escalate_to_human(
    customer_id: str,
    root_cause: str,
    refund_amount: float,
    recommended_action: str,
    urgency: str = "normal",
) -> str:
    """
    Escalate a case to a human support agent with a complete structured handoff.

    IMPORTANT: Human agents cannot see the conversation transcript. Include ALL context
    needed for them to understand and resolve the case without reading back through history.

    Required fields:
      - customer_id: verified customer ID from get_customer
      - root_cause: clear description of why the customer needs help (1-2 sentences)
      - refund_amount: amount requested (0 if not a refund case)
      - recommended_action: what the human agent should do to resolve the case

    Escalation triggers:
      - Customer explicitly requests to speak with a human (escalate immediately, do not negotiate)
      - Refund amount exceeds $500
      - Policy exception required (situation not covered by standard policy)
      - Agent has made 2+ unsuccessful resolution attempts

    Use urgency="high" when: customer is distressed, issue involves fraud,
    or SLA timeline is at risk.
    """
    escalation_id = f"ESC-{random.randint(10000, 99999)}"

    handoff = {
        "escalation_id": escalation_id,
        "customer_id": customer_id,
        "root_cause": root_cause,
        "refund_amount_requested": refund_amount,
        "recommended_action": recommended_action,
        "urgency": urgency,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assigned_queue": "tier-2-support" if urgency == "high" else "tier-1-support",
    }

    return json.dumps({
        "escalation_created": True,
        **handoff,
    })


# ─── MCP Resources ─────────────────────────────────────────────────────────────

@mcp.resource("policy://return-policy")
def return_policy_resource() -> str:
    """Expose return policy as a resource — reduces exploratory tool calls."""
    return """
Customer Return Policy:
- Standard items: 30-day return window from delivery date
- Electronics: 15-day return window
- Refunds under $500: processed autonomously in 3-5 business days
- Refunds $500+: require human agent approval
- Items must be in original condition; damaged items require photo evidence
- Competitor price matching: applies to own-site price adjustments only
"""


if __name__ == "__main__":
    mcp.run()
