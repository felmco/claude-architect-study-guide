"""
Task Statement 1.3: Configure subagent invocation, context passing, and spawning

Key concepts:
- Task tool is the mechanism for spawning subagents (Agent SDK)
- allowedTools must include "Task" for a coordinator to invoke subagents
- Subagents do NOT automatically inherit parent context
- Parallel spawning: multiple Task calls in a single coordinator response
- Structured data format to separate content from metadata (source URLs, dates)
- fork_session for divergent approach exploration from shared baseline
- Coordinator prompts specify GOALS, not step-by-step instructions

Note: "Claude Code SDK" in the exam guide (v0.1) = "Claude Agent SDK" in 2026 docs.
Subagents cannot spawn their own subagents (2026 constraint).
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Structured subagent output format ────────────────────────────────────────

def format_subagent_output(
    content: str,
    sources: list[dict],
    publication_dates: list[str],
    coverage_areas: list[str],
) -> str:
    """
    Structured format separating content from metadata.

    Source attribution is preserved through synthesis by keeping it
    in a separate structured field — not embedded in prose where it
    gets lost during summarization.
    """
    return json.dumps({
        "content": content,
        "metadata": {
            "sources": sources,          # [{url, title, page}]
            "dates": publication_dates,  # Publication/collection dates
            "coverage": coverage_areas,
        },
    }, indent=2)


# ─── Simulated subagent implementations ───────────────────────────────────────

def web_search_subagent(
    research_goals: str,
    quality_criteria: str,
    # NOTE: No coordinator_history parameter — isolation is intentional
) -> str:
    """
    Web search subagent.

    Receives explicit research goals and quality criteria from coordinator.
    Does NOT receive coordinator's full conversation history.
    Returns structured output with source metadata preserved.
    """
    prompt = f"""You are a web research specialist.

RESEARCH GOALS: {research_goals}
QUALITY CRITERIA: {quality_criteria}

Search for information and return a JSON object with:
- "content": your findings
- "sources": [{{"url": "...", "title": "...", "page": "..."}}]
- "dates": ["2025-01-15", ...]  (publication dates of sources)
- "coverage_areas": ["area1", "area2"]

Return ONLY the JSON object."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    # Parse and re-format as structured output
    try:
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        return format_subagent_output(
            content=data.get("content", "Search findings"),
            sources=data.get("sources", [{"url": "https://example.com", "title": "Research Source", "page": "1"}]),
            publication_dates=data.get("dates", ["2025-01-15"]),
            coverage_areas=data.get("coverage_areas", ["general research"]),
        )
    except (json.JSONDecodeError, ValueError):
        return format_subagent_output(
            content=text,
            sources=[{"url": "https://example.com", "title": "Search Result"}],
            publication_dates=["2025-01-15"],
            coverage_areas=["research"],
        )


def document_analysis_subagent(
    documents: list[str],
    analysis_goals: str,
) -> str:
    """
    Document analysis subagent.

    Receives complete document list explicitly — no automatic context.
    Returns structured output with source attribution intact.
    """
    docs_str = "\n\n".join(f"[Document {i+1}]\n{doc}" for i, doc in enumerate(documents))

    prompt = f"""Analyze these documents:

{docs_str}

ANALYSIS GOALS: {analysis_goals}

Return JSON with "content" (analysis), "sources" (document references),
"dates" (relevant dates found), and "coverage_areas".
Return ONLY the JSON."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    try:
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        return format_subagent_output(
            content=data.get("content", "Analysis complete"),
            sources=data.get("sources", [{"url": "document://1", "title": "Analyzed Document"}]),
            publication_dates=data.get("dates", ["2025-01-01"]),
            coverage_areas=data.get("coverage_areas", ["document analysis"]),
        )
    except (json.JSONDecodeError, ValueError):
        return format_subagent_output(
            content=text,
            sources=[{"url": "document://1", "title": "Document"}],
            publication_dates=["2025-01-01"],
            coverage_areas=["analysis"],
        )


# ─── Coordinator demonstrating parallel spawning ───────────────────────────────

def coordinator_with_parallel_spawning(topic: str) -> dict:
    """
    Demonstrates how a coordinator spawns parallel subagents.

    In Agent SDK: coordinator emits multiple Task tool calls in ONE response.
    This is equivalent to emitting them in a single turn.

    allowedTools for coordinator MUST include "Task" to spawn subagents.
    """
    print(f"\nCoordinator: Spawning parallel subagents for '{topic}'")
    print("(In Agent SDK: both Task calls emitted in single coordinator response)")

    # CORRECT: Pass complete, explicit context to each subagent
    # Coordinator specifies GOALS and quality criteria, not step-by-step instructions
    search_goals = (
        f"Research '{topic}': find key statistics, recent developments (2024-2025), "
        f"and expert perspectives. Prioritize peer-reviewed sources and authoritative reports."
    )
    analysis_goals = (
        f"Analyze documents about '{topic}': identify trends, conflicts between sources, "
        f"and gaps. Extract quantitative data with clear source attribution."
    )

    # In Agent SDK, both calls happen in one coordinator response turn
    # Here we simulate sequential for demonstration, but mark them as parallel
    print("  → Spawning: web_search_subagent")
    print("  → Spawning: document_analysis_subagent")
    print("  (Both run concurrently in production Agent SDK)")

    search_result_raw = web_search_subagent(
        research_goals=search_goals,
        quality_criteria="Cite sources with URLs and publication dates",
    )

    analysis_result_raw = document_analysis_subagent(
        documents=[
            f"Background report on {topic} from 2024",
            f"Industry analysis of {topic} trends",
        ],
        analysis_goals=analysis_goals,
    )

    # Parse structured outputs — metadata preserved for synthesis
    search_result = json.loads(search_result_raw)
    analysis_result = json.loads(analysis_result_raw)

    print(f"\nSearch sources: {len(search_result['metadata']['sources'])} found")
    print(f"Analysis coverage: {analysis_result['metadata']['coverage']}")

    return {
        "search": search_result,
        "analysis": analysis_result,
        "topic": topic,
    }


# ─── Context passing patterns ──────────────────────────────────────────────────

def demonstrate_context_passing():
    """
    Shows correct vs incorrect context passing to subagents.
    """
    print("\n=== Context Passing Patterns ===")

    print("\nCORRECT: Pass complete prior findings explicitly")
    # When synthesis subagent needs web search + analysis results:
    synthesis_prompt_correct = """
    You are a synthesis specialist.

    === WEB SEARCH FINDINGS ===
    {search_content}
    Sources: {search_sources}

    === DOCUMENT ANALYSIS ===
    {analysis_content}
    Sources: {analysis_sources}

    Synthesize these findings for topic: {topic}
    Preserve ALL source attributions in your synthesis.
    """.strip()
    print("Template shows complete prior context injected into subagent prompt")

    print("\nWRONG: Assume subagent has context from coordinator's conversation")
    synthesis_prompt_wrong = """
    Based on what we found so far, synthesize the research.
    """.strip()
    print("'What we found so far' doesn't exist in subagent's isolated context window!")


# ─── Anti-patterns ────────────────────────────────────────────────────────────

def antipattern_step_by_step_instructions():
    """
    ANTI-PATTERN: Coordinator gives step-by-step procedural instructions.

    This reduces subagent adaptability. Coordinator should specify
    GOALS and quality criteria, not exact steps.
    """
    bad_prompt = """
    1. First, search Google for the topic
    2. Then open the first 3 results
    3. Then extract the key points
    4. Then format as bullet points
    5. Then return the result
    """

    good_prompt = """
    Research goal: Find the most credible recent evidence on {topic}
    Quality criteria: Prefer peer-reviewed sources, include publication dates
    Output format: Structured JSON with content and source metadata
    """

    print("BAD: Step-by-step instructions limit adaptability")
    print("GOOD: Goal + criteria + output format enables adaptive execution")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.3: Subagent Spawning, Context Passing, Parallel Execution")
    print("=" * 60)

    results = coordinator_with_parallel_spawning("renewable energy adoption rates")

    demonstrate_context_passing()
    antipattern_step_by_step_instructions()

    print("\n" + "=" * 60)
    print("allowedTools must include 'Task' for coordinator to spawn subagents.")
    print("Context must be passed EXPLICITLY — no automatic inheritance.")
    print("Parallel spawning = multiple Task calls in ONE coordinator response.")


if __name__ == "__main__":
    main()
