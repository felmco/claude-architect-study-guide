"""
Task Statement 5.6: Preserve information provenance and handle uncertainty in multi-source synthesis

Key concepts:
- Source attribution lost during summarization — preserve claim-source mappings
- Conflicting statistics: annotate with source, don't arbitrarily select
- Publication/collection dates required to prevent temporal misinterpretation
- Synthesis reports: well-established vs contested findings sections
- Render content appropriately: financial data as tables, news as prose, technical as lists
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Claim-source mapping structure ───────────────────────────────────────────

def make_claim_source_mapping(
    claim: str,
    evidence_excerpt: str,
    source_url: str,
    source_title: str,
    publication_date: str,  # REQUIRED — prevents temporal misinterpretation
    confidence: float = 0.9,
) -> dict:
    """
    Structured claim-source mapping that must be preserved through synthesis.

    These mappings allow:
    1. Attribution in final report (which source supports which claim)
    2. Conflict detection (when two sources contradict each other)
    3. Temporal interpretation (2019 stat vs 2024 stat)
    """
    return {
        "claim": claim,
        "evidence": evidence_excerpt,
        "source": {
            "url": source_url,
            "title": source_title,
            "publication_date": publication_date,  # ISO 8601
        },
        "confidence": confidence,
        "contested": False,  # Updated if conflicting source found
    }


# ─── Conflict annotation ──────────────────────────────────────────────────────

def annotate_conflict(
    claim_a: dict,
    claim_b: dict,
    resolution_notes: str = "",
) -> dict:
    """
    When two credible sources report conflicting statistics:
    - Annotate BOTH values with source attribution
    - Do NOT arbitrarily select one value
    - Include resolution notes if any (methodology differences, time periods)

    The coordinator or final synthesis decides how to reconcile.
    """
    return {
        "type": "conflicting_claims",
        "topic": claim_a.get("claim", ""),
        "value_a": {
            "value": claim_a.get("claim"),
            "source": claim_a.get("source", {}),
            "evidence": claim_a.get("evidence", ""),
        },
        "value_b": {
            "value": claim_b.get("claim"),
            "source": claim_b.get("source", {}),
            "evidence": claim_b.get("evidence", ""),
        },
        "resolution_notes": resolution_notes,
        "requires_editorial_judgment": True,
    }


# ─── Subagent output with preserved provenance ────────────────────────────────

def simulate_search_subagent_with_provenance(topic: str) -> dict:
    """
    Simulates a search subagent that returns structured findings
    with claim-source mappings preserved.

    BAD: Subagent summarizes into prose ("Studies show X and Y")
    GOOD: Subagent returns structured mappings preserving attribution
    """
    # Simulate findings about AI adoption (topic)
    findings = {
        "topic": topic,
        "claims": [
            make_claim_source_mapping(
                claim="AI tool adoption among creative professionals grew 40% from 2021 to 2023",
                evidence_excerpt="Our survey of 500 creative professionals found 40% increased AI tool usage",
                source_url="https://example.com/creative-ai-survey-2023",
                source_title="Creative Industry AI Adoption Survey 2023",
                publication_date="2023-06-15",
                confidence=0.9,
            ),
            make_claim_source_mapping(
                claim="AI adoption in creative industries grew 25% from 2021 to 2023",
                evidence_excerpt="Industry data shows 25% year-over-year growth in AI tool subscriptions",
                source_url="https://example.com/industry-report-2023",
                source_title="Creative Technology Market Report Q4 2023",
                publication_date="2023-12-01",
                confidence=0.85,
            ),
            # This second claim CONFLICTS with the first (40% vs 25%)
        ],
        "data_collection_date": "2025-05-28",  # When subagent collected this data
    }

    return findings


# ─── Synthesis with provenance preservation ───────────────────────────────────

def synthesize_with_conflict_detection(subagent_findings: list[dict]) -> str:
    """
    Synthesis that preserves attribution and handles conflicts explicitly.
    """
    # Collect all claims
    all_claims = []
    for findings in subagent_findings:
        all_claims.extend(findings.get("claims", []))

    # Detect conflicts (same topic, different values, credible sources)
    conflicts = []
    well_supported = []

    for i, claim_a in enumerate(all_claims):
        conflict_found = False
        for claim_b in all_claims[i+1:]:
            # Simple conflict detection: different numbers on same topic
            if (claim_a.get("claim", "").startswith("AI tool adoption") and
                    claim_b.get("claim", "").startswith("AI")):
                conflicts.append(annotate_conflict(claim_a, claim_b,
                    "Methodology difference: survey vs subscription data"))
                conflict_found = True

        if not conflict_found:
            well_supported.append(claim_a)

    # Build synthesis prompt with structured data
    synthesis_prompt = f"""
Synthesize research findings. Preserve attribution and distinguish well-established from contested.

WELL-SUPPORTED FINDINGS (single credible source):
{json.dumps(well_supported, indent=2)}

CONTESTED FINDINGS (conflicting credible sources):
{json.dumps(conflicts, indent=2)}

INSTRUCTIONS:
1. Present well-supported findings with source attribution
2. For contested findings: present BOTH values with attribution (do not arbitrarily choose one)
3. Note temporal context (2023 data vs 2024 data are different time periods)
4. Distinguish "well-established" section from "contested findings" section
5. Render financial data as structured format, narrative as prose

Return a synthesis report with clear sections.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    return response.content[0].text


# ─── Anti-patterns ────────────────────────────────────────────────────────────

def show_provenance_anti_patterns():
    print("\n=== Provenance Anti-Patterns ===\n")

    print("ANTI-PATTERN 1: Summarization loses attribution")
    bad = "Studies show AI adoption grew 35% in creative industries."
    print(f"  '{bad}'")
    print("  Problem: Where did 35% come from? Which study? When? Can't verify.")
    print()

    print("ANTI-PATTERN 2: Arbitrary conflict resolution")
    print("  Source A says 40%, Source B says 25% for same metric.")
    print("  Bad synthesis: 'AI adoption grew 40%' (picked higher number)")
    print("  Good synthesis: 'Adoption grew 40% (survey data, Smith 2023) or 25% (market data, Jones 2023)'")
    print()

    print("ANTI-PATTERN 3: Missing publication dates")
    print("  'Studies show 15% growth' — is this 2019 or 2024?")
    print("  2019 stat + 2024 stat can look identical without dates")
    print("  Temporal differences misread as contradictions")
    print()

    print("CORRECT: Preserve claim-source mappings through synthesis")
    correct = make_claim_source_mapping(
        claim="AI adoption grew 40% from 2021-2023",
        evidence_excerpt="Survey of 500 designers found 40% adoption",
        source_url="https://example.com/survey-2023",
        source_title="Creative AI Survey 2023",
        publication_date="2023-06-15",
    )
    print(f"  {json.dumps(correct, indent=2)}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.6: Information Provenance in Multi-Source Synthesis")
    print("=" * 60)

    show_provenance_anti_patterns()

    print("\n=== Synthesis with Conflict Detection ===\n")
    findings = simulate_search_subagent_with_provenance("AI adoption in creative industries")
    print(f"Subagent found {len(findings['claims'])} claims (including conflicting statistics)")

    synthesis = synthesize_with_conflict_detection([findings])
    print(f"\nSynthesis report:\n{synthesis[:400]}...")

    print("\n" + "=" * 60)
    print("Claim-source mappings must survive summarization steps.")
    print("Conflicting sources: annotate both values, don't pick one.")
    print("Publication dates: required to distinguish temporal differences from contradictions.")


if __name__ == "__main__":
    main()
