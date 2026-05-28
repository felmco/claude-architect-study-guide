---
paths: ["**/*.py"]
---

# Python Conventions (auto-loaded for .py files)

- Use type hints on all function signatures
- Use `python-dotenv` and `load_dotenv()` at module top for `.env` loading
- Prefer `anthropic.Anthropic()` over direct HTTP calls
- Model names: `claude-haiku-4-5-20251001` for tests, `claude-opus-4-7` for production
- Each runnable file needs `def main()` and `if __name__ == "__main__": main()`
- Use `print()` with clear labels — this is educational code, not production logging
