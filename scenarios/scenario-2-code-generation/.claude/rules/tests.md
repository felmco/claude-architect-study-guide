---
paths: ["**/*.test.tsx", "**/*.test.ts", "**/*.spec.tsx", "**/*.spec.ts", "**/test_*.py"]
---

# Test Conventions — All test files regardless of location (Exam Q6)

This rule applies to test files SCATTERED throughout the repo (Button.test.tsx
lives next to Button.tsx). A subdirectory CLAUDE.md can't do this — it's directory-bound.
Glob patterns in .claude/rules/ solve this correctly.

## Standards
- Name tests: `it('should <behavior> when <condition>')`
- Mock: external services only — never mock the subject under test
- Each test: one assertion per behavior, not one mega-test
- Fixtures: shared fixtures in `__fixtures__/` not duplicated per test file
