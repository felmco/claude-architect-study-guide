---
paths: ["**/*.test.tsx", "**/*.test.ts", "**/test_*.py", "**/*_test.py", "**/tests/**/*.py"]
---

# Test Conventions (auto-loaded for ALL test files, regardless of location)

> **Exam Key (Q6):** This rule uses glob patterns so it applies to test files
> SCATTERED THROUGHOUT the codebase, not just in one directory.
> A subdirectory CLAUDE.md couldn't do this — it's directory-bound.

## Test Naming
- Python: `test_<function>_<condition>` e.g. `test_login_invalid_email`
- TypeScript: `it('should <behavior> when <condition>')`
- Test class names: `Test<ClassName>` e.g. `TestAuthService`

## What to Test
- Happy path: expected inputs produce expected outputs
- Edge cases: empty string, None/null, boundary values, empty list
- Error cases: invalid input, missing required fields, permission denied
- Do NOT test: framework internals, third-party library behavior

## Mocking Rules
- Mock external services (APIs, databases) for unit tests
- Integration tests in `tests/integration/` may use real connections
- Use `unittest.mock.MagicMock` or `pytest-mock`, not manual fakes
- Never mock the subject under test itself

## No Duplication
- Check existing test files before adding new tests
- Use parameterized tests (`@pytest.mark.parametrize`) for similar cases
- Fixtures go in `conftest.py`, not duplicated across test files

## Performance
- Unit tests must complete in < 100ms each
- Tests that take > 1 second must be marked `@pytest.mark.slow`
