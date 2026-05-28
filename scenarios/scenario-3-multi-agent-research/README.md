# Scenario 3: Multi-Agent Research System

**Primary Domains:** 1 (Agentic Architecture), 2 (Tool Design & MCP), 5 (Context & Reliability)

**Exam questions based on this scenario:** Q7, Q8, Q9

---

## The System

A coordinator agent delegates to 4 specialized subagents:
1. **Web Search** — finds relevant articles, returns structured `{claim, evidence, source_url, date}`
2. **Document Analysis** — analyzes provided documents, extracts key findings
3. **Synthesis** — combines findings from other agents, has `verify_fact` scoped tool (Q9)
4. **Report Generation** — produces final report distinguishing well-established from contested findings

---

## Sequence Diagram: Parallel Research Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Coordinator
    participant WebSearch
    participant DocAnalysis
    participant Synthesis
    participant ReportGen

    User->>Coordinator: "Research: impact of AI on creative industries"
    Coordinator->>Coordinator: Decompose into subtopics (music, writing, film, visual arts)
    
    par Parallel spawning (single coordinator response)
        Coordinator->>WebSearch: Task(goals="Research all 4 subtopics", quality_criteria="...")
        Coordinator->>DocAnalysis: Task(docs=[...], analysis_goals="...")
    end
    
    WebSearch-->>Coordinator: {claims: [{claim, source_url, date}], coverage: [...], gaps: [...]}
    DocAnalysis-->>Coordinator: {findings: [...], coverage: [...], errors: null}
    
    alt WebSearch timed out
        WebSearch-->>Coordinator: {is_error: true, failure_type: "timeout", attempted_query, partial_results}
        Coordinator->>Coordinator: Decide: proceed with partial results, annotate gap
    end
    
    Coordinator->>Synthesis: Task(search_results=[...], analysis_results=[...], topic="...")
    Note over Synthesis: Has verify_fact tool for 85% of simple checks (Q9)
    Synthesis->>Synthesis: verify_fact("Eiffel Tower completed 1889")
    Synthesis-->>Coordinator: {draft_report, gaps: ["music industry missing"]}
    
    Coordinator->>Coordinator: Evaluate coverage — gaps found
    Coordinator->>WebSearch: Task("Targeted: music industry AI adoption")
    WebSearch-->>Coordinator: Additional findings
    
    Coordinator->>ReportGen: Task(all_findings=[...])
    ReportGen-->>Coordinator: Final report with Well-Established / Contested sections
    
    Coordinator-->>User: Comprehensive cited research report
```

---

## Files

| File | Purpose |
|------|---------|
| `coordinator.py` | Hub-and-spoke coordinator with parallel spawning + iterative refinement |
| `agents/web_search.py` | Web search subagent with structured output + error handling |
| `agents/doc_analysis.py` | Document analysis subagent |
| `agents/synthesis.py` | Synthesis subagent with scoped verify_fact tool |
| `agents/report_gen.py` | Report generation with well-established vs contested sections |

---

## Key Exam Patterns Demonstrated

**Q7:** Coordinator decomposes comprehensively (not just visual arts).
**Q8:** WebSearch returns structured error context when it fails.
**Q9:** Synthesis has scoped `verify_fact` tool for 85% of simple verifications.
