# Claude Certified Architect – Foundations Study Guide

Developed by **Future Tales** (futuretales.ai) · Powered by **Anthropic Claude**

This repository is a comprehensive study guide for the **Claude Certified Architect – Foundations**
certification exam. It contains working Python code for all 28 task statements across 5 domains,
6 complete scenario mini-projects, 52 practice questions, and full reference materials.

---

## Project Structure

```
domain-1-agentic-architecture/   ← Tasks 1.1–1.7  (27% of exam — highest priority)
domain-2-tool-design-mcp/        ← Tasks 2.1–2.5  (18%)
domain-3-claude-code/            ← Tasks 3.1–3.6  (20%)
domain-4-prompt-engineering/     ← Tasks 4.1–4.6  (20%)
domain-5-context-reliability/    ← Tasks 5.1–5.6  (15%)
scenarios/                       ← 6 complete mini-projects (exam scenarios)
practice-exam/                   ← 12 official sample questions + 40 knowledge checks
reference/                       ← Cheat sheet, glossary, API changes, study schedule
assets/                          ← Banner SVG
```

## Exam Quick Reference

- **Pass score:** 720 / 1000 (scaled)
- **Format:** Multiple choice, 4 choices, 1 correct answer
- **Scenarios:** 4 of the 6 drawn at random per sitting
- **Domains by weight:** D1 (27%) → D3 (20%) → D4 (20%) → D2 (18%) → D5 (15%)

---

## Python Conventions

- Python 3.11+; type hints required on all public functions
- Use `python-dotenv` — copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`
- Every runnable `.py` file has `def main()` and `if __name__ == "__main__": main()`
- Smoke tests use `claude-haiku-4-5-20251001`; production examples use `claude-opus-4-7`
- Pydantic for all structured data validation (Domain 4 extraction pipeline)
- No bare `except Exception:` — catch specific types; log with `print()` in educational code

## Running the Code

```bash
# Install dependencies
pip install anthropic fastmcp pydantic python-dotenv pytest pytest-asyncio

# Smoke test (uses API — ~$0.05-0.15)
make smoke-test

# Unit tests (mocked, free)
pytest scenarios/scenario-1-customer-support/test_agent.py -v

# Run any domain file directly
python domain-1-agentic-architecture/1_1_agentic_loop.py
python domain-4-prompt-engineering/4_3_structured_output.py
```

## Key Exam Anti-Patterns to Avoid in Code

When generating or modifying code in this repo, ensure examples demonstrate CORRECT patterns:

| Anti-Pattern | Correct Pattern |
|---|---|
| Check `response.content[0].text` for "done" to end loop | Check `stop_reason == "end_turn"` |
| Prompt-only enforcement for mandatory tool ordering | Programmatic prerequisite in tool function |
| Return `{"status": "unavailable"}` on MCP error | Structured error with `isError`, `errorCategory`, `isRetryable` |
| `tool_choice: "auto"` when you need guaranteed output | `tool_choice: "any"` or forced tool |
| Message Batches API for blocking pre-merge checks | Synchronous API for blocking; Batch for overnight |
| Escalate on negative sentiment | Escalate on explicit criteria only |

---

## Imported Rules

@import .claude/rules/python.md
@import .claude/rules/tests.md

---

## This Repo Demonstrates Domain 3 By Its Own Configuration

The `.claude/` directory is a live working example of the exact patterns tested on the exam:

| Exam Task | Where It's Demonstrated |
|---|---|
| Task 3.1 — CLAUDE.md hierarchy | This file (project-level); `domain-3-claude-code/3_1_claude_md_hierarchy/` |
| Task 3.2 — Commands and skills | `.claude/commands/review.md`; `.claude/skills/explore-codebase/SKILL.md` |
| Task 3.3 — Path-scoped rules | `.claude/rules/python.md` (`paths: ["**/*.py"]`); `.claude/rules/tests.md` |
| Task 2.4 — MCP configuration | `.mcp.json` with `${ANTHROPIC_API_KEY:-not-set}` expansion |
| Task 3.4 — Plan mode | Plan mode was used to design this entire repo before implementation |

The `/explore-codebase` skill uses `context: fork` and `allowed-tools: Read,Grep,Glob`
so verbose discovery stays isolated from the main conversation context.
