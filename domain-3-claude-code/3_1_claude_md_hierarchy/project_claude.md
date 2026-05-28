# Example: Project-level CLAUDE.md (repo root or .claude/)

> **Exam Key:** This file goes in <repo>/CLAUDE.md or <repo>/.claude/CLAUDE.md
> It IS committed to version control and shared with ALL team members.
> Every developer who clones the repo receives these instructions.

## Project: E-Commerce Platform

## @import Syntax — Keep CLAUDE.md Modular

@import .claude/rules/testing.md
@import .claude/rules/api-conventions.md

## Universal Coding Standards (All Team Members)

- Python 3.11+, type hints required on all public functions
- All API endpoints must validate input with Pydantic
- Database queries must use parameterized statements (no f-string SQL)
- Error handling: never catch bare `Exception` — catch specific exception types

## Testing Standards

- Minimum 80% test coverage on new code
- Unit tests: pytest, no real database connections (use fixtures)
- Integration tests: `tests/integration/` directory, separate pytest marker

## Workflow Commands

- `make test` — run unit tests
- `make lint` — run flake8 and mypy
- `make smoke-test` — quick end-to-end verification

## Security Requirements

- Never commit .env files or secrets
- API keys must use environment variables, never hardcoded
- All user inputs must be validated before database operations

## Branch and PR Standards

- Feature branches: `feature/<ticket-id>-short-description`
- PRs require 1 approval + passing CI
- Squash merge to main

---

**HOW TO VERIFY WHAT'S LOADED:**
Use the `/memory` command in Claude Code to see which CLAUDE.md files are active
in the current session. This helps diagnose why instructions aren't being followed.
