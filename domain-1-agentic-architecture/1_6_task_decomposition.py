"""
Task Statement 1.6: Design task decomposition strategies for complex workflows

Key concepts:
- Prompt chaining: sequential fixed steps (predictable multi-aspect reviews)
- Dynamic decomposition: adaptive subtasks based on intermediate findings
- Per-file local analysis passes THEN separate cross-file integration pass
- When to use which: fixed pipeline for predictable tasks, dynamic for open-ended
"""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Strategy 1: Prompt Chaining (fixed sequential) ───────────────────────────

def prompt_chain_code_review(files: dict[str, str]) -> dict:
    """
    PROMPT CHAINING for code review.

    Use when: predictable multi-aspect review with fixed steps.
    Pattern: Analyze each file individually → cross-file integration pass.

    Why split into passes?
    - Per-file passes: deep, consistent analysis of each file in isolation
    - Integration pass: catches cross-file data flow issues, API mismatches
    - Single-pass on 14 files → attention dilution → inconsistent results (Q12 anti-pattern)
    """
    results = {}
    per_file_analyses = {}

    print("Phase 1: Per-file local analysis")
    for filename, code in files.items():
        prompt = f"""Perform a focused code review of this single file.
Look for: bugs, security issues, error handling gaps, performance problems.
Do NOT look for cross-file issues yet.

File: {filename}
```python
{code}
```

Return: List of issues found (or 'No issues found')."""

        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        analysis = response.content[0].text
        per_file_analyses[filename] = analysis
        print(f"  ✓ {filename}: {len(analysis)} chars of findings")

    print("\nPhase 2: Cross-file integration pass")
    all_analyses = "\n\n".join(
        f"=== {fname} ===\n{analysis}"
        for fname, analysis in per_file_analyses.items()
    )

    integration_prompt = f"""You have per-file analyses of a multi-file codebase.
Now look ONLY for cross-file issues:
- Data passed from one file but expected differently in another
- API contracts not matching between caller and callee
- Shared state mutations that could cause races
- Import cycles or circular dependencies

Per-file analyses:
{all_analyses}

Return: Cross-file integration issues only."""

    integration_response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": integration_prompt}],
    )

    results["per_file"] = per_file_analyses
    results["integration"] = integration_response.content[0].text
    print(f"  ✓ Integration pass complete")
    return results


# ─── Strategy 2: Dynamic Decomposition (adaptive) ─────────────────────────────

def dynamic_decompose_test_task(codebase_description: str) -> dict:
    """
    DYNAMIC DECOMPOSITION for open-ended tasks.

    Use when: task is open-ended (e.g., "add comprehensive tests to legacy codebase").
    Pattern: First map structure → identify high-impact areas → create prioritized plan.

    The plan adapts as dependencies are discovered, unlike fixed prompt chains.
    """
    print("\nDynamic decomposition: mapping codebase structure first")

    # Step 1: Map the structure (discover what we're working with)
    map_prompt = f"""You are analyzing a legacy codebase to plan comprehensive test coverage.

Codebase description: {codebase_description}

First, map what exists:
1. What are the main modules/components?
2. What are the most complex areas (high lines of code, many dependencies)?
3. What areas have the highest business risk if broken?

Return a JSON object with:
{{"modules": ["module1", ...], "high_complexity": ["..."], "high_risk": ["..."]}}"""

    map_response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": map_prompt}],
    )
    map_text = map_response.content[0].text
    print(f"  ✓ Structure mapped")

    # Step 2: Adaptive plan based on what was discovered
    plan_prompt = f"""Based on this codebase mapping:
{map_text}

Create a PRIORITIZED test plan that adapts to what was found:
1. Start with highest-risk, highest-impact areas
2. Identify dependencies that must be tested first
3. Note areas where mocking is needed vs integration tests

This plan should be different from a generic test plan — it reflects
the SPECIFIC structure discovered in step 1.

Return a numbered list of testing tasks in priority order."""

    plan_response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": plan_prompt}],
    )

    print(f"  ✓ Adaptive plan created based on discovered structure")
    return {
        "structure_map": map_text,
        "adaptive_plan": plan_response.content[0].text,
    }


# ─── Selection guide ───────────────────────────────────────────────────────────

def show_selection_guide():
    """When to use prompt chaining vs dynamic decomposition."""
    guide = """
Task Decomposition Selection Guide
===================================

USE PROMPT CHAINING (fixed sequential) when:
  ✓ Task has predictable structure (code review, document analysis)
  ✓ Steps are always the same regardless of content
  ✓ Each step's output feeds directly into the next
  Examples:
    - PR review: per-file analysis → integration pass → summary
    - Document processing: extract → validate → enrich → store
    - Content pipeline: translate → summarize → classify → route

USE DYNAMIC DECOMPOSITION (adaptive) when:
  ✓ Task is open-ended ("add comprehensive tests")
  ✓ Steps depend on what's discovered at each stage
  ✓ Different inputs lead to different investigation paths
  Examples:
    - Exploring an unfamiliar codebase
    - Debugging a non-deterministic failure
    - Planning a migration for an unknown system

MULTI-PASS REVIEW PATTERN (specific exam topic):
  Problem: Reviewing 14 files in one pass → attention dilution
    → Superficial comments on some files
    → Obvious bugs missed
    → Contradictory feedback across files

  Solution:
    Pass 1: Each file individually → local issues
    Pass 2: Cross-file integration → data flow, API contracts

  This is Exam Sample Question 12 — Answer A.
"""
    print(guide)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.6: Task Decomposition — Chaining vs Dynamic")
    print("=" * 60)

    show_selection_guide()

    print("--- Prompt Chaining: Code Review with Multi-Pass ---")
    sample_files = {
        "auth.py": "def login(user, pwd): return db.query(f'SELECT * FROM users WHERE pwd={pwd}')",
        "orders.py": "def get_orders(user_id): return cache.get(user_id) or db.fetch(user_id)",
        "refunds.py": "def process(order_id, amount): if amount > 0: return refund_api.post(order_id, amount)",
    }
    review_results = prompt_chain_code_review(sample_files)
    print(f"\nIntegration findings: {review_results['integration'][:200]}...")

    print("\n--- Dynamic Decomposition: Test Coverage Planning ---")
    decomp_results = dynamic_decompose_test_task(
        "E-commerce platform: auth module (500 LOC), order processing (1200 LOC), "
        "payment integration (800 LOC, external API). Currently 0% test coverage."
    )
    print(f"\nAdaptive plan preview: {decomp_results['adaptive_plan'][:300]}...")


if __name__ == "__main__":
    main()
