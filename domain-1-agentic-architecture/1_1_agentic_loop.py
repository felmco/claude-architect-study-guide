"""
Task Statement 1.1: Design and implement agentic loops for autonomous task execution

Key concepts:
- stop_reason "tool_use" → execute tools, append results, continue
- stop_reason "end_turn" → extract final response, terminate
- Tool results must be appended to conversation history for next iteration
- ANTI-PATTERNS: checking text content, arbitrary iteration caps as primary stop
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")

# ─── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "calculate",
        "description": (
            "Perform arithmetic calculations. Accepts a mathematical expression as a string "
            "and returns the numeric result. Use for addition, subtraction, multiplication, "
            "division, and parenthesized expressions. Do NOT use for non-numeric operations. "
            "Example: '(10 + 5) * 2' returns 30."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression string, e.g. '10 * 3 + 5'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_unit_price",
        "description": (
            "Look up the current unit price for a product SKU. Returns the price in USD. "
            "Use this before calculating order totals. Valid SKUs: 'WIDGET-A', 'WIDGET-B', 'GADGET-X'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Product SKU code",
                }
            },
            "required": ["sku"],
        },
    },
]

# ─── Simulated tool implementations ────────────────────────────────────────────

PRICES = {"WIDGET-A": 12.50, "WIDGET-B": 24.99, "GADGET-X": 89.00}


def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}})  # safe: no builtins
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def get_unit_price(sku: str) -> str:
    price = PRICES.get(sku.upper())
    if price is None:
        return json.dumps({"error": f"Unknown SKU: {sku}", "valid_skus": list(PRICES.keys())})
    return json.dumps({"sku": sku, "price_usd": price})


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch tool calls to their implementations."""
    if tool_name == "calculate":
        return calculate(tool_input["expression"])
    elif tool_name == "get_unit_price":
        return get_unit_price(tool_input["sku"])
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ─── Correct agentic loop ──────────────────────────────────────────────────────

def run_agent(user_message: str, verbose: bool = True) -> str:
    """
    CORRECT agentic loop implementation.

    Loop continues while stop_reason == "tool_use".
    Loop terminates when stop_reason == "end_turn".
    Tool results are appended to messages for each iteration.
    """
    messages = [{"role": "user", "content": user_message}]
    iteration = 0

    while True:
        iteration += 1
        if verbose:
            print(f"\n--- Iteration {iteration} ---")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        if verbose:
            print(f"stop_reason: {response.stop_reason}")

        # CORRECT: Check stop_reason, not response text content
        if response.stop_reason == "end_turn":
            # Extract the text response
            for block in response.content:
                if hasattr(block, "text"):
                    if verbose:
                        print(f"Final answer: {block.text}")
                    return block.text
            return ""

        elif response.stop_reason == "tool_use":
            # Append assistant response to history
            messages.append({"role": "assistant", "content": response.content})

            # Execute all requested tools and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"Tool call: {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    if verbose:
                        print(f"Tool result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Append tool results to history so Claude can reason about next action
            messages.append({"role": "user", "content": tool_results})

        else:
            # Handle unexpected stop reasons (max_tokens, stop_sequence, etc.)
            print(f"Unexpected stop_reason: {response.stop_reason}")
            break

    return ""


# ─── ANTI-PATTERN demonstrations ──────────────────────────────────────────────

def antipattern_text_check(user_message: str) -> str:
    """
    ANTI-PATTERN: Checking response text to determine loop termination.
    This is unreliable because LLM output is non-deterministic.
    The model may phrase "I'm done" differently each time.
    """
    messages = [{"role": "user", "content": user_message}]

    for _ in range(10):
        response = client.messages.create(
            model=MODEL, max_tokens=512, tools=TOOLS, messages=messages
        )
        # WRONG: looking for magic words in text
        text = " ".join(
            b.text for b in response.content if hasattr(b, "text")
        )
        if "final answer" in text.lower() or "here is the result" in text.lower():
            return text  # brittle!

        # ... rest of loop ...
    return "Max iterations reached"


def antipattern_iteration_cap(user_message: str, max_iter: int = 3) -> str:
    """
    ANTI-PATTERN: Using an arbitrary iteration cap as the PRIMARY stopping mechanism.
    If the task genuinely needs more iterations, it silently fails.
    Use stop_reason == "end_turn" as the primary stop; keep cap only as a safety net.
    """
    messages = [{"role": "user", "content": user_message}]

    for i in range(max_iter):  # WRONG as primary stop mechanism
        response = client.messages.create(
            model=MODEL, max_tokens=512, tools=TOOLS, messages=messages
        )
        if response.stop_reason == "end_turn":
            return " ".join(b.text for b in response.content if hasattr(b, "text"))
        # ... handle tool_use ...

    return "Silently gave up after 3 iterations"  # user doesn't know why


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.1: Agentic Loop — stop_reason Control Flow")
    print("=" * 60)

    # Multi-step task requiring multiple tool calls
    task = (
        "I need to order 3 WIDGET-A and 2 GADGET-X. "
        "What is the total cost in USD?"
    )
    print(f"\nUser: {task}")
    result = run_agent(task)
    print(f"\nFinal result: {result}")

    print("\n" + "=" * 60)
    print("Key takeaway: Loop terminates on stop_reason='end_turn',")
    print("NOT on text patterns or iteration counts.")


if __name__ == "__main__":
    main()
