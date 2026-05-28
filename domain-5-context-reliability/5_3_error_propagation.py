"""
Task Statement 5.3: Implement error propagation strategies across multi-agent systems

Key concepts (Exam Q8):
- Structured error context: failure_type, attempted_query, partial_results, alternatives
- Access failure (retry decision) vs valid empty result (don't retry)
- Subagents implement local recovery for transient failures
- Only propagate to coordinator if locally irresolvable (include context)
- Coverage annotations: which areas have gaps due to unavailable sources
- Anti-patterns: generic status, silent suppression, full workflow termination
"""

import json
import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


# ─── Structured error propagation ─────────────────────────────────────────────

def make_structured_error_for_coordinator(
    failure_type: str,
    attempted_query: str,
    partial_results: list,
    alternatives: list[str],
    attempts_made: int,
) -> dict:
    """
    Structured error context for coordinator decision-making.

    This gives the coordinator everything needed to choose a recovery strategy:
    - Should it retry with a different query?
    - Should it proceed with partial results?
    - Should it use an alternative source?

    Compare to ANTI-PATTERN generic: {"status": "search unavailable"}
    which hides all this context.
    """
    return {
        "is_error": True,
        "failure_type": failure_type,  # "timeout", "rate_limited", "not_found"
        "attempted_query": attempted_query,
        "attempts_made": attempts_made,
        "partial_results": partial_results,  # Whatever was found before failure
        "alternative_approaches": alternatives,
        "coordinator_options": _get_coordinator_options(failure_type, partial_results),
    }


def _get_coordinator_options(failure_type: str, partial_results: list) -> list[str]:
    """Suggest recovery options based on failure type."""
    options = []

    if failure_type in ["timeout", "rate_limited"]:
        options.append("retry_with_backoff")
        options.append("try_alternative_source")

    if partial_results:
        options.append(f"proceed_with_{len(partial_results)}_partial_results")
        options.append("annotate_synthesis_with_coverage_gap")

    if failure_type == "not_found":
        options.append("topic_may_not_exist_in_this_source")
        options.append("try_broader_query")

    return options


# ─── Subagent with local recovery ─────────────────────────────────────────────

class SearchSubagent:
    """
    Demonstrates the correct error handling pattern for subagents:
    1. Try locally (with retries for transient failures)
    2. If locally irresolvable: propagate structured context to coordinator
    3. Never silently suppress errors or return empty success
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 0.1

    def search(self, query: str, simulate_scenario: str = "success") -> dict:
        """
        Execute search with local recovery.

        simulate_scenario options:
        - "success": works normally
        - "transient": fails twice, succeeds on third attempt (local recovery)
        - "exhausted": all retries fail → propagate to coordinator
        - "empty_result": succeeds but finds nothing (NOT an error)
        - "permission": non-retryable → propagate immediately
        """
        print(f"  SearchAgent: searching for '{query}' (scenario: {simulate_scenario})")

        for attempt in range(self.MAX_RETRIES):
            result = self._attempt_search(query, simulate_scenario, attempt)

            if result["type"] == "success":
                if result["found"]:
                    print(f"  SearchAgent: Found {len(result['results'])} results on attempt {attempt+1}")
                    return result
                else:
                    # CORRECT: Empty result is NOT an error
                    print(f"  SearchAgent: Valid query, no results found (NOT an error)")
                    return result

            elif result["type"] == "transient_error":
                if attempt < self.MAX_RETRIES - 1:
                    print(f"  SearchAgent: Transient failure (attempt {attempt+1}), retrying locally...")
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))
                    continue
                else:
                    # All retries exhausted — propagate to coordinator with full context
                    print(f"  SearchAgent: Local recovery exhausted after {self.MAX_RETRIES} attempts")
                    return make_structured_error_for_coordinator(
                        failure_type="transient_exhausted",
                        attempted_query=query,
                        partial_results=[],
                        alternatives=["try_alternative_search_engine", "use_cached_results"],
                        attempts_made=self.MAX_RETRIES,
                    )

            elif result["type"] == "permission_error":
                # Non-retryable — propagate immediately
                print(f"  SearchAgent: Non-retryable permission error, propagating immediately")
                return make_structured_error_for_coordinator(
                    failure_type="permission_denied",
                    attempted_query=query,
                    partial_results=[],
                    alternatives=["check_api_credentials", "use_public_source_instead"],
                    attempts_made=1,
                )

        return make_structured_error_for_coordinator(
            failure_type="unknown",
            attempted_query=query,
            partial_results=[],
            alternatives=[],
            attempts_made=self.MAX_RETRIES,
        )

    def _attempt_search(self, query: str, scenario: str, attempt: int) -> dict:
        """Simulate different search outcomes for demonstration."""
        if scenario == "success":
            return {"type": "success", "found": True, "results": [f"Result 1 for {query}", f"Result 2"]}

        elif scenario == "empty_result":
            return {"type": "success", "found": False, "results": [], "message": "No documents matched"}

        elif scenario == "transient":
            if attempt < 2:  # Fail twice, succeed on third
                return {"type": "transient_error", "message": "Connection timeout"}
            return {"type": "success", "found": True, "results": ["Result after retry"]}

        elif scenario == "exhausted":
            return {"type": "transient_error", "message": f"Timeout (attempt {attempt+1})"}

        elif scenario == "permission":
            return {"type": "permission_error", "message": "API key expired"}

        return {"type": "success", "found": True, "results": []}


# ─── Coordinator using structured errors ──────────────────────────────────────

class Coordinator:
    """Demonstrates intelligent coordinator recovery using structured error context."""

    def __init__(self):
        self.search_agent = SearchSubagent()

    def research_topic(self, topic: str, simulate: str = "success") -> dict:
        """
        Coordinator researches a topic. Handles subagent errors intelligently.
        """
        print(f"\nCoordinator: Researching '{topic}'")

        result = self.search_agent.search(topic, simulate_scenario=simulate)

        if result.get("is_error"):
            return self._handle_subagent_error(result, topic)

        # Success path — compile report
        return self._compile_report(topic, result, coverage_gaps=[])

    def _handle_subagent_error(self, error: dict, topic: str) -> dict:
        """
        Intelligent error handling based on structured error context.
        """
        failure_type = error.get("failure_type", "unknown")
        alternatives = error.get("alternative_approaches", [])
        partial = error.get("partial_results", [])
        options = error.get("coordinator_options", [])

        print(f"\nCoordinator: Handling error — type={failure_type}, options={options}")

        # Strategy decision based on structured context
        if "proceed_with_partial_results" in str(options) and partial:
            print("  Decision: Proceed with partial results, annotate gaps")
            return self._compile_report(
                topic,
                {"found": True, "results": partial},
                coverage_gaps=[f"Source unavailable ({failure_type}): {topic} section may be incomplete"],
            )

        elif "retry_with_backoff" in options and failure_type in ["timeout", "rate_limited"]:
            print("  Decision: Coordinator-level retry with delay")
            time.sleep(0.2)
            retry_result = self.search_agent.search(topic + " (retry)", simulate_scenario="success")
            return self._compile_report(topic, retry_result, coverage_gaps=[])

        else:
            print("  Decision: Report with explicit coverage gap annotation")
            return self._compile_report(
                topic,
                {"found": False, "results": []},
                coverage_gaps=[f"Coverage gap: {topic} — {failure_type}"],
            )

    def _compile_report(self, topic: str, search_result: dict, coverage_gaps: list) -> dict:
        results = search_result.get("results", [])
        return {
            "topic": topic,
            "findings": results,
            "well_supported": len(results) > 0,
            "coverage_gaps": coverage_gaps,  # Synthesis agent uses this for honest reporting
            "coverage_annotation": (
                f"⚠ Limited coverage in: {', '.join(coverage_gaps)}"
                if coverage_gaps else "Full coverage"
            ),
        }


# ─── Anti-patterns ────────────────────────────────────────────────────────────

def show_anti_patterns():
    print("\n=== Error Propagation Anti-Patterns ===\n")

    print("ANTI-PATTERN 1: Generic status (hides context)")
    generic_error = {"status": "search unavailable"}
    print(f"  {generic_error}")
    print("  Coordinator can't decide: retry? alternative? proceed? NO CONTEXT.")
    print()

    print("ANTI-PATTERN 2: Silent suppression (marks failure as success)")
    silent_suppression = {"found": True, "results": []}  # Looks like empty result!
    print(f"  {silent_suppression}")
    print("  Coordinator thinks query succeeded with no results.")
    print("  Doesn't know search was actually down. Can't recover.")
    print()

    print("ANTI-PATTERN 3: Full workflow termination")
    print("  One subagent fails → entire research workflow throws exception")
    print("  Real issue: partial results + annotation is better than no results")
    print()

    print("CORRECT: Structured context enables intelligent recovery")
    structured = make_structured_error_for_coordinator(
        failure_type="timeout",
        attempted_query="renewable energy statistics",
        partial_results=["Partial result: solar adoption 30% in 2023"],
        alternatives=["try_alternative_search_engine"],
        attempts_made=3,
    )
    print(f"  {json.dumps(structured, indent=2)[:300]}...")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.3: Error Propagation in Multi-Agent Systems")
    print("=" * 60)

    coordinator = Coordinator()

    print("\n--- Scenario 1: Successful search ---")
    r1 = coordinator.research_topic("renewable energy", "success")
    print(f"Result: {r1['coverage_annotation']}")

    print("\n--- Scenario 2: Local recovery (transient failure) ---")
    r2 = coordinator.research_topic("solar power stats", "transient")
    print(f"Result: {r2['coverage_annotation']}")

    print("\n--- Scenario 3: All retries exhausted (propagated to coordinator) ---")
    r3 = coordinator.research_topic("wind energy data", "exhausted")
    print(f"Result: {r3['coverage_annotation']}")

    print("\n--- Scenario 4: Empty result (valid query, no data — NOT an error) ---")
    r4 = coordinator.research_topic("fictional energy source XYZ-2099", "empty_result")
    print(f"Result: {r4['coverage_annotation']}")

    show_anti_patterns()


if __name__ == "__main__":
    main()
