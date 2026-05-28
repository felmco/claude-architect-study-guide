"""
Task Statement 4.1: Design prompts with explicit criteria to reduce false positives

Key concepts:
- Explicit categorical criteria vs vague instructions ("be conservative")
- "Only high confidence" or "be conservative" fail to improve precision
- False positives undermine trust in accurate categories too
- Disable high-FP categories temporarily to restore trust
- Severity criteria need concrete code examples, not abstract descriptions

Exam Q3: Agent escalates easy cases, handles complex ones.
Root cause: Unclear escalation decision boundaries.
Fix: Explicit criteria + few-shot examples showing when to escalate vs resolve.
"""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Vague vs Explicit criteria ───────────────────────────────────────────────

VAGUE_REVIEW_PROMPT = """
Review this code for issues. Be conservative and only report high-confidence findings.
Focus on things that would clearly be a problem in production.
"""

EXPLICIT_REVIEW_PROMPT = """
Review this code. Apply these SPECIFIC criteria:

FLAG (report these):
- SQL injection: any string concatenation in database query construction
- Hardcoded secrets: API keys, passwords, tokens in source code
- Logic bugs: conditions that are always true/false, off-by-one in loops
- Missing null checks: dereferencing variables that could be None/null

SKIP (do not report):
- Comment accuracy: "check that comments describe what code does" — too subjective
- Variable naming: unless it's misleading (e.g., `is_active = False` assigned as `user.enabled`)
- Style preferences: line length, whitespace, import ordering
- Theoretical risks: "could be a problem if..." without concrete attack vector

SEVERITY CRITERIA (with examples):
- CRITICAL: user-supplied input reaches SQL/shell unescaped
  Example: `db.execute(f"SELECT * FROM users WHERE id={user_id}")`
- HIGH: authentication/authorization logic flaw
  Example: `if user.role == "admin" or True:` (always true)
- MEDIUM: data loss risk in specific scenario
  Example: list.pop() on potentially empty list in error handler
- LOW: not-blocking improvement
  Example: catching broad Exception instead of specific error type
"""

# ─── Demonstration ─────────────────────────────────────────────────────────────

SAMPLE_CODE = """
import os

API_KEY = "sk-prod-abc123"  # hardcoded secret

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    return db.execute(query)

def process_orders(orders):
    for i in range(len(orders) + 1):  # off-by-one
        order = orders[i]
        # This loop handles order processing
        if order.status == "pending":
            order.process()
"""


def compare_review_approaches():
    """Run review with vague vs explicit criteria and compare results."""

    print("=== Vague Criteria Review ===")
    response_vague = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"{VAGUE_REVIEW_PROMPT}\n\nCode:\n```python\n{SAMPLE_CODE}\n```"
        }],
    )
    print(response_vague.content[0].text)

    print("\n=== Explicit Criteria Review ===")
    response_explicit = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"{EXPLICIT_REVIEW_PROMPT}\n\nCode:\n```python\n{SAMPLE_CODE}\n```"
        }],
    )
    print(response_explicit.content[0].text)

    print("\n" + "=" * 60)
    print("Explicit criteria produce focused, actionable findings.")
    print("'Be conservative' does not change precision — it's too vague.")


# ─── High false-positive category management ──────────────────────────────────

def demonstrate_fp_category_management():
    """
    When a specific category has high false-positive rates:
    1. Disable it temporarily to restore trust in other categories
    2. Improve the criteria for that category
    3. Re-enable with refined criteria
    """
    print("\n=== False Positive Category Management ===\n")
    print("Scenario: Comment accuracy check produces 80% false positives")
    print("Developer trust in ALL review findings is eroding")
    print()
    print("STEP 1: Disable the high-FP category temporarily")
    print("  Add to SKIP list: 'comment accuracy — currently under calibration'")
    print()
    print("STEP 2: Improve criteria for the problematic category")
    bad_criteria = "'check that comments are accurate'"
    good_criteria = "'flag comments ONLY when claimed behavior CONTRADICTS actual code behavior'"
    print(f"  Before: '{bad_criteria}'")
    print(f"  After:  '{good_criteria}'")
    print()
    print("  Example of REAL violation:")
    print("    # Returns user's email address")
    print("    def get_user_name(user): return user.email  # Comment says email, returns name")
    print()
    print("  Example of NOT a violation (style preference, not contradiction):")
    print("    # Validates input")
    print("    def validate(x): if not isinstance(x, str): raise ValueError(...)")
    print("    (Validation is correct — comment isn't misleading)")
    print()
    print("STEP 3: Re-enable with refined criteria after calibration")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 4.1: Explicit Criteria for Precision")
    print("=" * 60)

    compare_review_approaches()
    demonstrate_fp_category_management()

    print("\nKey rules:")
    print("  'Be conservative' → does NOT improve precision (too vague)")
    print("  Explicit categorical criteria → reliably reduces false positives")
    print("  High-FP categories → disable temporarily, calibrate, re-enable")


if __name__ == "__main__":
    main()
