# 4-Week Study Schedule

Weighted by domain importance and your current coverage gap.

---

## Week 1: Foundation + Highest-Priority Gaps (Domain 1 + Domain 3)

**Goal:** Cover the two zero-coverage domains (45% of exam combined)

### Days 1-2: Domain 1 Basics
- Read `domain-1-agentic-architecture/README.md` (all sequence diagrams)
- Run `python domain-1-agentic-architecture/1_1_agentic_loop.py`
- Study `1_4_workflow_enforcement.py` (MOST EXAM-CRITICAL)
- Read Sample Questions 1, 7, 8 in `practice-exam/sample_questions.md`

### Days 3-4: Domain 3 — Claude Code Config
- Read `domain-3-claude-code/README.md`
- Study the `.claude/` structure in this repo (it IS the demonstration)
- Read `3_4_plan_vs_direct.md` — memorize the decision matrix
- Read Sample Questions 4, 5, 6

### Days 5-7: Scenario 1 Deep Dive
- Read `scenarios/scenario-1-customer-support/README.md`
- Run `python scenarios/scenario-1-customer-support/agent.py --smoke`
- Run `pytest scenarios/scenario-1-customer-support/test_agent.py -v`
- Understand the three sample questions (Q1, Q2, Q3) in depth

---

## Week 2: Multi-Agent + Tool Design (Domain 1 Advanced + Domain 2)

### Days 1-2: Domain 1 Advanced
- Run `1_2_coordinator_subagent.py` and `1_3_subagent_spawning.py`
- Study `1_5_hooks.py` — hooks vs prompt enforcement
- Study `1_6_task_decomposition.py` — chaining vs dynamic

### Days 3-4: Scenario 3 (Multi-Agent Research)
- Read `scenarios/scenario-3-multi-agent-research/README.md`
- Run `python scenarios/scenario-3-multi-agent-research/coordinator.py`
- Map Q7, Q8, Q9 to the code

### Days 5-7: Domain 2 — Tool Design & MCP
- Run `2_1_tool_descriptions.py` (BAD vs GOOD descriptions)
- Run `2_2_structured_errors.py` (all error categories)
- Run `2_3_tool_distribution.py` (tool_choice options)
- Read the MCP server in `2_4_mcp_integration/server.py`
- Memorize the MCP scope table in `reference/cheat-sheet.md`

---

## Week 3: Prompt Engineering + Context (Domain 4 + Domain 5)

### Days 1-2: Domain 4 Basics
- Run `4_3_structured_output.py` (tool_use + JSON schemas)
- Run `4_4_validation_retry.py` (Pydantic retry loop)
- Understand when to use nullable fields

### Days 3-4: Domain 4 Advanced
- Run `4_5_batch_processing.py` — memorize Batch API characteristics
- Run `4_6_multi_pass_review.py` — understand Q12
- Read Sample Questions 10, 11, 12

### Days 5-7: Domain 5
- Run `5_1_context_preservation.py` (case facts block)
- Run `5_2_escalation_patterns.py` (escalation criteria)
- Run `5_3_error_propagation.py` (structured vs generic errors)
- Run `5_6_provenance.py` (claim-source mappings)

---

## Week 4: Integration + Practice Exam Prep

### Days 1-2: Scenario 6 (Extraction Pipeline)
- Study `scenarios/scenario-6-extraction/README.md`
- Run the extraction, validation, and batch scripts
- Connect to Domain 4 knowledge

### Days 3-4: Scenario 5 (CI/CD Integration)
- Study `scenarios/scenario-5-ci-cd/README.md`
- Review the GitHub Actions workflow
- Understand the `-p` flag and JSON output flags

### Days 5-6: Reference Review
- Read `reference/cheat-sheet.md` — memorize key tables
- Read `reference/api-changes.md` — note terminology differences
- Review `reference/concepts-glossary.md` for any unfamiliar terms

### Day 7: Practice Exam Simulation
- Answer all 12 questions in `practice-exam/sample_questions.md` without looking at answers
- Check your answers
- For any you got wrong, re-read the relevant code file and explanation
- Focus extra time on the domains where you missed questions

---

## Quick Reference: Domain Coverage by Scenario

| Scenario | Primary Coverage |
|----------|----------------|
| Scenario 1 | D1 (loops, enforcement), D2 (tool descriptions, errors), D5 (escalation) |
| Scenario 2 | D3 (CLAUDE.md, commands, plan mode) |
| Scenario 3 | D1 (coordinator, parallel subagents), D2 (scoped tools), D5 (provenance) |
| Scenario 4 | D2 (built-in tools), D3 (skills) |
| Scenario 5 | D3 (CI/CD, -p flag), D4 (explicit criteria, few-shot) |
| Scenario 6 | D4 (structured output, retry, batch), D5 (confidence, human review) |

---

## Exam Day Prep

1. Read `reference/cheat-sheet.md` the morning of the exam
2. Remember: 4 of the 6 scenarios are drawn randomly — know ALL 6
3. For each question: identify the domain, read carefully, eliminate wrong answers
4. Wrong answer patterns to watch for:
   - Prompt-based enforcement for mandatory business rules → WRONG (use programmatic)
   - Sentiment/confidence scores for escalation → WRONG (use explicit criteria)
   - Generic error status → WRONG (use structured context)
   - Batch API for blocking workflows → WRONG (use sync)
   - Text content detection for loop termination → WRONG (use stop_reason)
