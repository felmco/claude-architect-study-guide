# Claude Certified Architect – Foundations: Study Guide

A complete study repository for the **Claude Certified Architect – Foundations** certification exam. Every task statement has working Python code, Mermaid sequence diagrams, definitions, and explanations.

> **Note:** The exam guide (v0.1, Feb 2025) references "Claude Code SDK." The current name (2026) is the **Claude Agent SDK**. MCP scope names also changed — see [`reference/api-changes.md`](reference/api-changes.md).

---

## Exam Domain Weights

| Domain | Topic | Weight | Coverage in This Repo |
|--------|-------|--------|----------------------|
| 1 | Agentic Architecture & Orchestration | **27%** | 7 files + 2 scenarios |
| 2 | Tool Design & MCP Integration | **18%** | 6 files + working server |
| 3 | Claude Code Configuration & Workflows | **20%** | .claude/ config + 6 sections |
| 4 | Prompt Engineering & Structured Output | **20%** | 6 files + batch API |
| 5 | Context Management & Reliability | **15%** | 6 files |

---

## Exam Scenarios (drawn from these 6 at random)

| # | Scenario | Primary Domains | Location |
|---|----------|----------------|----------|
| 1 | Customer Support Resolution Agent | 1, 2, 5 | `scenarios/scenario-1-customer-support/` |
| 2 | Code Generation with Claude Code | 3, 5 | `scenarios/scenario-2-code-generation/` |
| 3 | Multi-Agent Research System | 1, 2, 5 | `scenarios/scenario-3-multi-agent-research/` |
| 4 | Developer Productivity with Claude | 2, 3, 1 | `scenarios/scenario-4-developer-productivity/` |
| 5 | Claude Code for CI/CD | 3, 4 | `scenarios/scenario-5-ci-cd/` |
| 6 | Structured Data Extraction | 4, 5 | `scenarios/scenario-6-extraction/` |

---

## Setup

```bash
# 1. Copy and fill in your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 2. Install dependencies
pip install anthropic fastmcp pydantic python-dotenv pytest pytest-asyncio

# 3. Run smoke tests (~$0.05–0.15)
make smoke-test

# 4. Run all scenario unit tests (mocked, free)
make test
```

---

## Repository Structure

```
.
├── CLAUDE.md                         ← Project-level Claude instructions
├── .mcp.json                         ← Project-scoped MCP with ${VAR} expansion
├── .claude/
│   ├── commands/review.md            ← /review slash command
│   ├── rules/python.md               ← paths: ["**/*.py"]
│   └── skills/explore-codebase/      ← context: fork skill
│
├── domain-1-agentic-architecture/    ← Tasks 1.1–1.7 (27%)
├── domain-2-tool-design-mcp/         ← Tasks 2.1–2.5 (18%)
├── domain-3-claude-code/             ← Tasks 3.1–3.6 (20%)
├── domain-4-prompt-engineering/      ← Tasks 4.1–4.6 (20%)
├── domain-5-context-reliability/     ← Tasks 5.1–5.6 (15%)
│
├── scenarios/                        ← 6 complete mini-projects
├── practice-exam/                    ← 12 sample questions + knowledge checks
└── reference/                        ← Glossary, cheat sheet, study schedule
```

---

## Study Path (4 Weeks)

See [`reference/study-schedule.md`](reference/study-schedule.md) for the full plan.

**Quick start by domain weight:**
1. Start with `domain-1-agentic-architecture/README.md` (highest weight, most new content)
2. Then `scenarios/scenario-1-customer-support/` (most questions on the exam)
3. Then `domain-3-claude-code/` (second highest weight, zero prior coverage)
4. Read `reference/cheat-sheet.md` before exam day

---

## Cost Estimate

| Activity | Estimated Cost |
|----------|---------------|
| `make smoke-test` | $0.05–0.15 |
| Full Scenario 1 run | $0.10–0.30 |
| Full Scenario 3 run | $0.20–0.50 |
| All scenarios end-to-end | < $2.00 |

All smoke tests use `claude-haiku-4-5-20251001`. Production examples use `claude-opus-4-7`.

---

## Key References

- [Exam Guide](docs/Claude%20Certified%20Architect%20-%20Foundations%20Certification%20Exam%20Guide.md) (in parent folder)
- [Anthropic Docs](https://docs.anthropic.com)
- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Agent SDK](https://docs.anthropic.com/en/agent-sdk/overview)
- [`reference/api-changes.md`](reference/api-changes.md) — v0.1 guide vs 2026 terminology
