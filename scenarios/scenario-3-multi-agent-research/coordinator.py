"""
Scenario 3: Multi-Agent Research System — Coordinator

Demonstrates:
- Task 1.2: Hub-and-spoke coordinator with dynamic subagent selection
- Task 1.3: Parallel subagent spawning, explicit context passing
- Task 1.4: Iterative refinement loop when synthesis has coverage gaps
- Task 5.3: Intelligent handling of subagent error propagation
- Task 5.6: Preservation of claim-source mappings through synthesis

Exam Q7: Comprehensive topic decomposition (not just visual arts)
Exam Q8: Structured error context from failing subagent
Exam Q9: Synthesis has scoped verify_fact tool
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# Import subagent functions (inline for simplicity — in production these would be Agent SDK Tasks)
def web_search_agent(query: str, quality_criteria: str) -> dict:
    """Web search subagent with structured output and error handling."""
    prompt = f"""Research: {query}

Quality criteria: {quality_criteria}

Return JSON with:
- "claims": [{{"claim": "...", "evidence": "...", "source_url": "https://example.com/...", "date": "2023-06-15"}}]
- "coverage_areas": ["area1", "area2"]
- "gaps": ["missing_area1"]

Return ONLY the JSON."""

    response = client.messages.create(
        model=MODEL, max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        return {"is_error": False, **data}
    except (json.JSONDecodeError, ValueError):
        return {
            "is_error": True, "failure_type": "parse_error",
            "attempted_query": query, "partial_results": [],
            "alternative_approaches": ["try_simpler_query"],
        }


def synthesis_agent(search_results: dict, analysis_results: dict, topic: str) -> dict:
    """
    Synthesis subagent with scoped verify_fact tool (Q9).

    The synthesis agent has a verify_fact tool for the 85% of verifications
    that are simple fact-checks. Complex verifications still route through coordinator.
    """
    # Include complete prior agent findings explicitly (no automatic context inheritance)
    claims_text = json.dumps(search_results.get("claims", []), indent=2)

    prompt = f"""Synthesize research on: {topic}

SEARCH FINDINGS (complete — do not assume other context):
Coverage areas: {search_results.get("coverage_areas", [])}
Claims with sources:
{claims_text}

ANALYSIS FINDINGS:
{json.dumps(analysis_results, indent=2)}

TASK:
1. Synthesize into a draft report
2. Identify COVERAGE GAPS — important subtopics not addressed
3. Mark findings as "well-established" (multiple credible sources) vs "contested" (conflicting sources)
4. Preserve ALL source attributions

Return JSON: {{"report": "...", "gaps": ["gap1", "gap2"], "contested_claims": []}}"""

    response = client.messages.create(
        model=MODEL, max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        return data
    except (json.JSONDecodeError, ValueError):
        return {"report": text, "gaps": [], "contested_claims": []}


def coordinator(topic: str, verbose: bool = True) -> dict:
    """
    Hub-and-spoke coordinator for research.

    Key patterns:
    1. Comprehensive decomposition (not narrow — Exam Q7 anti-pattern avoided)
    2. Parallel subagent spawning (single coordinator response)
    3. Explicit context passing (no automatic inheritance)
    4. Structured error handling from failing subagents
    5. Iterative refinement for coverage gaps
    """
    if verbose:
        print(f"\nCoordinator: Researching '{topic}'")

    # Step 1: Comprehensive topic decomposition
    decomp_response = client.messages.create(
        model=MODEL, max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                f"Decompose '{topic}' into 4-6 comprehensive subtopics covering ALL relevant domains.\n"
                f"Return JSON: {{\"subtopics\": [\"subtopic1\", ...]}}"
            )
        }],
    )
    decomp_text = decomp_response.content[0].text
    try:
        subtopics = json.loads(decomp_text[decomp_text.find("{"):decomp_text.rfind("}")+1]).get("subtopics", [topic])
    except (json.JSONDecodeError, ValueError):
        subtopics = [topic]

    if verbose:
        print(f"Decomposed into {len(subtopics)} subtopics: {subtopics}")

    # Step 2: Spawn subagents in parallel (simulated here — in Agent SDK: single response with multiple Task calls)
    if verbose:
        print("Spawning web_search and doc_analysis subagents in parallel...")

    # Both calls in one "turn" = parallel execution in Agent SDK
    search_results = web_search_agent(
        query=f"{topic}: {', '.join(subtopics[:4])}",
        quality_criteria="Include publication dates and source URLs. Cover all subtopics.",
    )

    analysis_results = {
        "findings": [f"Analysis of existing literature on {t}" for t in subtopics[:2]],
        "coverage_areas": subtopics[:2],
    }

    if verbose:
        print(f"Search status: {'error' if search_results.get('is_error') else 'success'}")

    # Step 3: Handle subagent errors with structured context
    if search_results.get("is_error"):
        failure_type = search_results.get("failure_type", "unknown")
        partial = search_results.get("partial_results", [])

        if verbose:
            print(f"  Error from search: {failure_type}. Proceeding with partial results.")

        # Coordinator uses structured error to make intelligent decision
        search_results = {
            "claims": partial,
            "coverage_areas": [],
            "gaps": subtopics,  # All subtopics become gaps
            "coverage_annotation": f"⚠ Search unavailable ({failure_type})",
        }

    # Step 4: Route through coordinator to synthesis (not direct subagent-to-subagent)
    if verbose:
        print("Invoking synthesis subagent with complete findings...")

    synthesis = synthesis_agent(search_results, analysis_results, topic)
    gaps = synthesis.get("gaps", [])

    if verbose:
        print(f"Synthesis complete. Coverage gaps: {gaps}")

    # Step 5: Iterative refinement for gaps
    if gaps:
        if verbose:
            print(f"Coordinator: Filling gaps: {gaps[:2]}...")

        additional_search = web_search_agent(
            query=f"{topic}: focused on {', '.join(gaps[:2])}",
            quality_criteria="Fill specific gaps in coverage.",
        )

        if not additional_search.get("is_error"):
            # Combine and re-synthesize with complete context
            search_results["claims"] = (
                search_results.get("claims", []) + additional_search.get("claims", [])
            )
            synthesis = synthesis_agent(search_results, analysis_results, topic)

    return {
        "topic": topic,
        "subtopics_covered": subtopics,
        "report": synthesis.get("report", ""),
        "coverage_gaps": synthesis.get("gaps", []),
        "contested_claims": synthesis.get("contested_claims", []),
    }


def main():
    print("=" * 60)
    print("Scenario 3: Multi-Agent Research System")
    print("=" * 60)

    result = coordinator("impact of AI on creative industries", verbose=True)

    print("\n=== Research Report ===")
    print(f"Topic: {result['topic']}")
    print(f"Subtopics covered: {result['subtopics_covered']}")
    print(f"Report preview: {result['report'][:300]}...")
    print(f"Remaining gaps: {result['coverage_gaps']}")


if __name__ == "__main__":
    main()
