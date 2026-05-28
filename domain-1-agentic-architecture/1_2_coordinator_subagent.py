"""
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns

Key concepts:
- Hub-and-spoke: coordinator manages ALL inter-subagent communication
- Coordinator does dynamic selection (doesn't always route through full pipeline)
- Iterative refinement: coordinator re-delegates when synthesis has coverage gaps
- Subagents have isolated context — no automatic inheritance from coordinator
- ANTI-PATTERN: overly narrow task decomposition (misses entire subtopics)

Note: This file demonstrates the PATTERN. The full working implementation
with the actual Agent SDK Task tool is in scenario-3-multi-agent-research/.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Data structures ───────────────────────────────────────────────────────────

@dataclass
class SubagentResult:
    """Structured output from a subagent — content separated from metadata."""
    content: str
    sources: list[dict] = field(default_factory=list)  # [{url, title, date}]
    coverage_areas: list[str] = field(default_factory=list)
    has_errors: bool = False
    error_context: Optional[str] = None


@dataclass
class ResearchTask:
    topic: str
    subtopics: list[str]
    depth: str = "standard"  # "standard" | "deep"


# ─── Simulated subagents ───────────────────────────────────────────────────────
# In production, these would be spawned via the Agent SDK Task tool.
# The coordinator passes ALL context explicitly — subagents have no memory.

def search_subagent(query: str, context_from_coordinator: str) -> SubagentResult:
    """
    Simulates the web search subagent.

    Key: receives context EXPLICITLY from coordinator.
    Returns structured output preserving source attribution.
    """
    prompt = f"""You are a web search specialist. Search for information about: {query}

Context from coordinator: {context_from_coordinator}

Return a JSON object with:
- "content": your findings (2-3 sentences)
- "sources": list of {{"url": "...", "title": "...", "date": "2025-01-15"}}
- "coverage_areas": list of subtopics you covered
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        # Parse structured output
        data = json.loads(text[text.find("{") : text.rfind("}") + 1])
        return SubagentResult(
            content=data.get("content", text),
            sources=data.get("sources", [{"url": "example.com", "title": query, "date": "2025-01-15"}]),
            coverage_areas=data.get("coverage_areas", [query]),
        )
    except (json.JSONDecodeError, ValueError):
        return SubagentResult(content=text, sources=[], coverage_areas=[query])


def analysis_subagent(documents: list[str], focus: str) -> SubagentResult:
    """
    Simulates the document analysis subagent.
    Receives explicit document list from coordinator.
    """
    docs_text = "\n\n".join(f"Document {i+1}: {d}" for i, d in enumerate(documents))
    prompt = f"""Analyze these documents focusing on: {focus}

{docs_text}

Return JSON with "content" (your analysis) and "coverage_areas" (topics you analyzed).
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        data = json.loads(text[text.find("{") : text.rfind("}") + 1])
        return SubagentResult(
            content=data.get("content", text),
            coverage_areas=data.get("coverage_areas", [focus]),
        )
    except (json.JSONDecodeError, ValueError):
        return SubagentResult(content=text, coverage_areas=[focus])


def synthesis_subagent(
    search_results: SubagentResult,
    analysis_results: SubagentResult,
    topic: str,
) -> tuple[str, list[str]]:
    """
    Simulates the synthesis subagent.

    Key: receives COMPLETE findings from prior agents directly in prompt.
    Returns (report, coverage_gaps) so coordinator can check completeness.
    """
    prompt = f"""Synthesize research on: {topic}

=== WEB SEARCH FINDINGS ===
{search_results.content}
Sources: {json.dumps(search_results.sources)}
Areas covered: {search_results.coverage_areas}

=== DOCUMENT ANALYSIS ===
{analysis_results.content}
Areas covered: {analysis_results.coverage_areas}

Write a synthesis report. Then list any COVERAGE GAPS — important subtopics
not addressed by the provided research. Return JSON:
{{"report": "...", "gaps": ["gap1", "gap2"]}}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        data = json.loads(text[text.find("{") : text.rfind("}") + 1])
        return data.get("report", text), data.get("gaps", [])
    except (json.JSONDecodeError, ValueError):
        return text, []


# ─── Coordinator ───────────────────────────────────────────────────────────────

def coordinator(topic: str, max_refinement_rounds: int = 2) -> str:
    """
    Hub-and-spoke coordinator.

    Responsibilities:
    1. Decompose topic into comprehensive subtopics (avoid narrow decomposition)
    2. Dynamically select which subagents to invoke based on query complexity
    3. Pass complete context to each subagent (no automatic inheritance)
    4. Evaluate synthesis for gaps, re-delegate targeted queries if needed
    5. Route ALL subagent communication through coordinator (no direct links)
    """
    print(f"\nCoordinator: Researching '{topic}'")

    # Step 1: Decompose topic into comprehensive subtopics
    # CORRECT: Broad decomposition covering the full domain
    # ANTI-PATTERN: Decomposing "AI in creative industries" into only visual arts subtopics
    decomposition_prompt = f"""Decompose this research topic into 3-5 comprehensive subtopics
that together cover the FULL scope of the topic. Do not miss major sub-areas.

Topic: {topic}

Return JSON: {{"subtopics": ["subtopic1", "subtopic2", ...]}}"""

    decomp_response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": decomposition_prompt}],
    )
    decomp_text = decomp_response.content[0].text
    try:
        decomp_data = json.loads(decomp_text[decomp_text.find("{") : decomp_text.rfind("}") + 1])
        subtopics = decomp_data.get("subtopics", [topic])
    except (json.JSONDecodeError, ValueError):
        subtopics = [topic]

    print(f"Coordinator: Decomposed into subtopics: {subtopics}")

    # Step 2: Invoke subagents in parallel with explicit context
    # In Agent SDK: emit multiple Task tool calls in a single response
    print("Coordinator: Spawning search and analysis subagents in parallel...")

    search_context = f"Research all of these subtopics: {subtopics}"
    search_results = search_subagent(
        query=f"{topic}: {', '.join(subtopics[:3])}",
        context_from_coordinator=search_context,
    )

    analysis_results = analysis_subagent(
        documents=[f"Background document on {t}" for t in subtopics],
        focus=topic,
    )

    print(f"Search covered: {search_results.coverage_areas}")
    print(f"Analysis covered: {analysis_results.coverage_areas}")

    # Step 3: Route all results through coordinator to synthesis subagent
    report, gaps = synthesis_subagent(search_results, analysis_results, topic)
    print(f"Synthesis complete. Coverage gaps found: {gaps}")

    # Step 4: Iterative refinement — coordinator re-delegates for gaps
    for round_num in range(max_refinement_rounds):
        if not gaps:
            break

        print(f"\nCoordinator: Refinement round {round_num + 1} — filling gaps: {gaps}")
        gap_query = f"{topic}: focused on {', '.join(gaps)}"

        additional_search = search_subagent(
            query=gap_query,
            context_from_coordinator=f"Fill these specific gaps: {gaps}",
        )

        # Pass COMPLETE prior context + new findings to synthesis
        report, gaps = synthesis_subagent(
            search_results=SubagentResult(
                content=f"{search_results.content}\n\nAdditional findings:\n{additional_search.content}",
                sources=search_results.sources + additional_search.sources,
                coverage_areas=search_results.coverage_areas + additional_search.coverage_areas,
            ),
            analysis_results=analysis_results,
            topic=topic,
        )
        print(f"After refinement, remaining gaps: {gaps}")

    return report


# ─── Demonstrate anti-pattern ──────────────────────────────────────────────────

def antipattern_narrow_decomposition(topic: str) -> str:
    """
    ANTI-PATTERN: Coordinator decomposes too narrowly.

    Example from exam: topic = "impact of AI on creative industries"
    Coordinator only assigns: digital art, graphic design, photography
    Result: music, writing, film COMPLETELY MISSED
    """
    # This is what NOT to do:
    narrow_subtasks = ["AI in digital art creation", "AI in graphic design", "AI in photography"]
    # Missing: music, writing, film, game design, architecture...

    print(f"ANTI-PATTERN: Narrow decomposition misses major domains!")
    print(f"Assigned: {narrow_subtasks}")
    print(f"Missed: music, writing, film, game design, and more")
    return "Incomplete research — only covers visual arts"


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.2: Coordinator-Subagent Orchestration")
    print("=" * 60)

    print("\n--- CORRECT PATTERN: Comprehensive decomposition ---")
    report = coordinator("impact of AI on creative industries", max_refinement_rounds=1)
    print(f"\nFinal report preview: {report[:200]}...")

    print("\n--- ANTI-PATTERN: Narrow decomposition ---")
    antipattern_narrow_decomposition("impact of AI on creative industries")

    print("\n" + "=" * 60)
    print("Key takeaway: Coordinator must decompose comprehensively AND")
    print("pass ALL context explicitly to each subagent.")


if __name__ == "__main__":
    main()
