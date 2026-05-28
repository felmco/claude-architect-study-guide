# Scenario 2: Code Generation with Claude Code

**Primary Domains:** 3 (Claude Code Config), 5 (Context & Reliability)

**Exam questions based on this scenario:** Q4, Q5, Q6

---

## The System

A development team using Claude Code for code generation, refactoring, debugging, and documentation. The configuration demonstrates real-world Claude Code setup.

---

## Files

| File/Dir | Purpose |
|----------|---------|
| `CLAUDE.md` | Team coding standards (project-level) |
| `.claude/commands/review.md` | `/review` slash command (shared via git) |
| `.claude/rules/react.md` | React component conventions (paths: src/components) |
| `.claude/rules/api.md` | API handler conventions (paths: src/api) |
| `.claude/rules/tests.md` | Test conventions (paths: **/*.test.*) |

---

## Exam Questions Exercised

**Q4:** `/review` command in `.claude/commands/` → available to all via version control.

**Q5:** Monolith-to-microservices → plan mode (architectural decision, dozens of files, multiple valid approaches).

**Q6:** Test files spread throughout codebase → `.claude/rules/` with `paths: ["**/*.test.tsx"]` glob pattern (not subdirectory CLAUDE.md which is directory-bound).
