"""
Task Statement 4.2: Apply few-shot prompting to improve output consistency

Key concepts:
- Few-shot examples: most effective technique for format consistency
- Target ambiguous scenarios where the model might go either way
- Examples show reasoning for WHY one action was chosen over alternatives
- Reduces false positives by showing acceptable patterns alongside real issues
- Handles varied document structures (inline citations vs bibliographies)
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Few-shot examples for format consistency ─────────────────────────────────

CODE_REVIEW_SYSTEM = """You are a code reviewer. Report findings in this exact format:

EXAMPLES OF CORRECT OUTPUT FORMAT:

Example 1 — Real bug:
{
  "severity": "high",
  "file": "auth.py",
  "line": 42,
  "issue": "SQL injection: user_id concatenated directly into query string",
  "detected_pattern": "f-string in db.execute()",
  "suggestion": "Use parameterized query: cursor.execute('WHERE id = ?', (user_id,))"
}

Example 2 — False positive (acceptable pattern, do NOT flag):
Code: `users = [u for u in all_users if u.is_active]`
NOT flagged because: list comprehension filtering is idiomatic Python,
not a performance concern unless profile confirms it.

Example 3 — Ambiguous case (flag this one):
Code: `except Exception as e: pass`
Flag as medium: Silent exception suppression hides bugs. Even if intentional,
should at minimum log the exception.

GUIDANCE: Flag real bugs and security issues. Skip style preferences and patterns
that appear normal in the codebase. For ambiguous cases, explain your reasoning.
"""


def review_code_with_few_shot(code: str) -> str:
    """Run code review with few-shot format examples."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=CODE_REVIEW_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Review this code:\n```python\n{code}\n```\nReturn findings as JSON list."
        }],
    )
    return response.content[0].text


# ─── Few-shot for document extraction with varied structures ──────────────────

EXTRACTION_SYSTEM = """Extract publication dates from academic documents.
Documents have VARIED FORMATS — use these examples:

Format 1 — Inline citation:
  Text: "According to Smith (2023, p. 15), the effect was..."
  Extract: {"date": "2023", "format": "inline_citation", "location": "parenthetical"}

Format 2 — Bibliography entry:
  Text: "Smith, J. (2023). Title. Journal, 45(2), 123-145."
  Extract: {"date": "2023", "format": "bibliography", "location": "reference_list"}

Format 3 — Date range:
  Text: "Data collected from January 2021 to March 2023"
  Extract: {"date": "2021-2023", "format": "collection_range", "location": "methodology"}

Format 4 — Absent (return null, do NOT invent):
  Text: A document with no visible date information
  Extract: {"date": null, "format": null, "location": null}

Always match the actual format in the document. Never invent dates not present.
"""


def extract_with_format_few_shot(document: str) -> dict:
    """Extract dates from documents with varying structures."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=EXTRACTION_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Extract publication dates:\n\n{document}"
        }],
    )
    text = response.content[0].text
    try:
        return json.loads(text[text.find("{"):text.rfind("}")+1])
    except (json.JSONDecodeError, ValueError):
        return {"raw_response": text}


# ─── Few-shot for tool selection disambiguation ────────────────────────────────

TOOL_SELECTION_SYSTEM = """You help decide which tool to call for customer support queries.

EXAMPLES showing reasoning for ambiguous cases:

Example 1:
User: "Check my order #12345"
→ Call: lookup_order(order_number="ORD-12345")
→ Why: User provides ORDER number (starts with digits/hash format). get_customer is for email/identity only.

Example 2:
User: "My name is Jane Smith, check my account"
→ Call: get_customer (ask for email)
→ Why: "Account" indicates customer record. Names are not unique identifiers — need email.

Example 3 (ambiguous — use this reasoning):
User: "Can you look up what I ordered last week?"
→ Call: get_customer first (ask for email)
→ Why: We have no order number, so we can't call lookup_order directly.
   Must verify customer identity before any order operations.
   Don't guess an order number.

Example 4:
User: "I need a refund for the broken widget"
→ Call: get_customer first (ask for email)
→ Why: Need verified customer_id before any refund operation.
   Even though end goal is a refund, order verification must happen first.
"""


def demonstrate_tool_selection_few_shot():
    """Shows how few-shot examples guide tool selection in ambiguous cases."""
    ambiguous_queries = [
        "Look up my last order",
        "I bought something last week, can you find it?",
        "Jane Smith, I need help with my account",
    ]

    print("=== Few-Shot Tool Selection for Ambiguous Queries ===\n")
    for query in ambiguous_queries:
        response = client.messages.create(
            model=MODEL,
            max_tokens=150,
            system=TOOL_SELECTION_SYSTEM,
            messages=[{"role": "user", "content": f"What tool to call? Query: '{query}'"}],
        )
        print(f"Query: '{query}'")
        print(f"Decision: {response.content[0].text[:100]}...")
        print()


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 4.2: Few-Shot Prompting for Consistency")
    print("=" * 60)

    print("\n--- Code Review with Few-Shot Format Examples ---")
    code = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result
"""
    print(f"Code:\n{code}")
    review = review_code_with_few_shot(code)
    print(f"Review:\n{review}")

    print("\n--- Document Extraction with Varied Format Examples ---")
    test_docs = [
        "According to Johnson (2022, p. 45), the results showed significant improvement.",
        "Smith, A., & Brown, B. (2021). Effects on learning. Journal of Ed, 12(3), 45-67.",
        "A white paper analyzing market trends for Q3.",
    ]
    for doc in test_docs:
        result = extract_with_format_few_shot(doc)
        print(f"Doc: {doc[:60]}...")
        print(f"Extracted: {result}\n")

    demonstrate_tool_selection_few_shot()

    print("Key: 2-4 targeted examples outperform detailed instructions alone.")
    print("Target AMBIGUOUS scenarios — that's where examples add most value.")


if __name__ == "__main__":
    main()
