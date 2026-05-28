---
paths: ["**/test_*.py", "**/*_test.py"]
---

# Test Conventions (auto-loaded for test files)

- Use `pytest` with `pytest-asyncio` for async tests
- Test files live alongside the code they test inside `scenarios/`
- Mock the Anthropic API client for unit tests (use `unittest.mock.MagicMock`)
- Test names: `test_<what>_<condition>` e.g. `test_hook_blocks_large_refund`
- Each scenario's `test_agent.py` must test: tool ordering, hook enforcement, error handling
