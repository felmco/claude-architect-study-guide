"""
Task Statement 4.6: Design multi-instance and multi-pass review architectures

Key concepts:
- Self-review limitation: same session retains reasoning from generation
- Independent review instance (without prior context) is more effective
- Multi-pass: per-file local analysis + cross-file integration pass
- Splitting avoids attention dilution on 14+ files

Exam Q12: 14-file PR with inconsistent single-pass review
Answer A: Split into per-file local passes + separate integration pass
"""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


def multi_pass_code_review(files: dict[str, str]) -> dict:
    """
    Multi-pass review architecture:
    1. Per-file local analysis (one independent Claude call per file)
    2. Cross-file integration pass (separate call with all local analyses)

    This is the correct answer to Exam Q12:
    - Single pass on 14 files → attention dilution → inconsistent results
    - Multi-pass → consistent depth per file + cross-file analysis
    """
    per_file_findings = {}

    # Pass 1: Independent per-file local analysis
    # Each file gets a fresh, focused review
    print("Phase 1: Per-file local analysis (one instance per file)")
    for filename, code in files.items():
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            # NOTE: Fresh API call per file = independent instance = no cross-file context
            # This is the key architectural point: independence prevents bias
            messages=[{
                "role": "user",
                "content": (
                    f"Analyze ONLY this file for LOCAL issues (bugs, security, logic errors). "
                    f"Do NOT look for cross-file issues yet. Focus exclusively on this file.\n\n"
                    f"File: {filename}\n```python\n{code}\n```\n\n"
                    f"Return JSON: {{\"findings\": [{{\"line\": N, \"issue\": \"...\", \"severity\": \"...\"}}]}}"
                ),
            }],
        )
        text = response.content[0].text
        per_file_findings[filename] = text
        print(f"  ✓ {filename}: analyzed")

    # Pass 2: Cross-file integration pass (separate instance — no file content, just analyses)
    print("\nPhase 2: Cross-file integration pass")
    analyses_summary = "\n\n".join(
        f"=== {fname} ===\n{analysis}"
        for fname, analysis in per_file_findings.items()
    )

    integration_response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        # Different focus: ONLY cross-file issues
        # Does not re-read the file contents — only the per-file analyses
        messages=[{
            "role": "user",
            "content": (
                f"Given these per-file analyses, identify ONLY cross-file issues:\n"
                f"- Data passed between files with mismatched types/formats\n"
                f"- API contracts that don't match between caller and callee\n"
                f"- Shared state mutations across files\n"
                f"- Import cycles or circular dependencies\n\n"
                f"Per-file analyses:\n{analyses_summary}\n\n"
                f"Return ONLY cross-file findings (not issues already identified per-file)."
            ),
        }],
    )

    return {
        "per_file": per_file_findings,
        "integration": integration_response.content[0].text,
    }


def demonstrate_independent_review_instance():
    """
    Shows why an independent review instance catches more issues than self-review.

    Self-review limitation: the model that GENERATED code retains reasoning context.
    When it reviews its own code, it has implicit bias toward its design decisions.
    An independent instance starts fresh — more likely to question assumptions.
    """
    print("\n=== Independent Review Instance ===\n")

    generated_code = """
def calculate_discount(price, user_tier):
    # Gold users get 20%, Silver get 10%, Standard get 0%
    tiers = {"gold": 0.20, "silver": 0.10, "standard": 0.0}
    discount = tiers.get(user_tier, 0.0)
    return price * (1 - discount)
"""

    print("Code to review:", generated_code)

    # Simulating independent review (no knowledge of why code was written this way)
    independent_review = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "Review this function for bugs and edge cases. "
                "You have no context about why it was written this way.\n"
                f"```python\n{generated_code}\n```\n"
                "What issues or edge cases exist?"
            ),
        }],
    )
    print("Independent review findings:")
    print(independent_review.content[0].text)
    print()
    print("Key: The independent instance might notice:")
    print("  - No validation that price is non-negative")
    print("  - tier='platinum' would get 0% discount (default) — likely unintended")
    print("  - No type checking on price (string would return 0.0 silently)")
    print()
    print("Self-review is less likely to catch these because the generator 'knows'")
    print("the intended usage and doesn't question the assumptions.")


def show_confidence_reporting():
    """
    Verification passes: model self-reports confidence alongside findings.
    Low-confidence findings route to human review.
    """
    print("\n=== Confidence Score Alongside Findings ===\n")

    code = """
def process_payment(amount, card_number):
    if not card_number.startswith("4"):
        raise ValueError("Only Visa cards accepted")
    return payment_api.charge(card_number, amount)
"""

    review_with_confidence = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Review this code. For each finding, include a confidence score (0-1.0).\n"
                f"Format: {{\"severity\": \"...\", \"issue\": \"...\", \"confidence\": 0.9}}\n\n"
                f"Code:\n```python\n{code}\n```"
            ),
        }],
    )
    print(review_with_confidence.content[0].text)
    print()
    print("Low confidence findings (< 0.7) → route to human review")
    print("High confidence findings (> 0.85) → can be acted on automatically")


def main():
    print("=" * 60)
    print("Task 4.6: Multi-Pass Review Architecture")
    print("=" * 60)

    # Demonstrate multi-pass on sample files
    sample_files = {
        "auth.py": (
            "def login(email, password):\n"
            "    user = db.query(f'SELECT * FROM users WHERE email={email}')\n"
            "    if user and user.password == password:\n"
            "        return generate_token(user.id)"
        ),
        "orders.py": (
            "def get_orders(user_id):\n"
            "    token = request.headers.get('Authorization')\n"
            "    # TODO: validate token\n"
            "    return db.query(f'SELECT * FROM orders WHERE user_id={user_id}')"
        ),
    }

    print(f"\nReviewing {len(sample_files)} files with multi-pass approach...")
    results = multi_pass_code_review(sample_files)
    print(f"\nIntegration findings: {results['integration'][:300]}...")

    demonstrate_independent_review_instance()
    show_confidence_reporting()

    print("\n" + "=" * 60)
    print("Multi-pass review = consistent depth + cross-file analysis")
    print("Independent instance = unbiased review without generator's context")


if __name__ == "__main__":
    main()
