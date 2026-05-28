# Claude Architect Study Guide — Project Context

This repository is a comprehensive study guide for the **Claude Certified Architect – Foundations** certification exam. It contains working Python code for all 28 task statements across 5 domains, 6 complete scenario mini-projects, and reference materials.

## Quick Navigation

- `domain-1-agentic-architecture/` — Agentic loops, multi-agent orchestration, hooks (27% of exam)
- `domain-2-tool-design-mcp/` — Tool descriptions, MCP servers, error handling (18%)
- `domain-3-claude-code/` — CLAUDE.md config, skills, commands, CI/CD (20%)
- `domain-4-prompt-engineering/` — Few-shot, structured output, batch API (20%)
- `domain-5-context-reliability/` — Context management, escalation, provenance (15%)
- `scenarios/` — 6 complete mini-projects matching the 6 exam scenarios
- `practice-exam/` — All 12 sample questions + knowledge checks per domain
- `reference/` — Cheat sheet, glossary, API changes, study schedule

## Python Conventions

- Python 3.11+
- Use `python-dotenv` to load `.env` — copy `.env.example` to `.env` and add your API key
- Every `.py` file has a `main()` function and `if __name__ == "__main__": main()` block
- Use `claude-haiku-4-5-20251001` for smoke tests; `claude-opus-4-7` for production examples
- Type hints required; Pydantic for any structured data validation

## Testing

- `make smoke-test` — runs cheap end-to-end tests (~$0.05–0.15 total)
- `pytest scenarios/` — unit tests for scenario hook enforcement and tool ordering
- Each domain file is self-contained and runnable: `python domain-1-agentic-architecture/1_1_agentic_loop.py`

## Imported Rules

@import .claude/rules/python.md
@import .claude/rules/tests.md

## Key Concept: This Repo Demonstrates Domain 3 By Its Own Configuration

The `.claude/` directory in this repo is a live working example of:
- Task 3.1: CLAUDE.md hierarchy (this file = project-level)
- Task 3.2: `.claude/commands/` and `.claude/skills/` with proper frontmatter
- Task 3.3: `.claude/rules/` with glob-pattern path scoping
- Task 2.4: `.mcp.json` with environment variable expansion
