.PHONY: install smoke-test test clean

install:
	pip install -e ".[dev]" 2>/dev/null || pip install anthropic fastmcp pydantic python-dotenv pytest pytest-asyncio httpx

smoke-test:
	@echo "Running smoke tests (uses claude-haiku-4-5, ~\$$0.05-0.15)..."
	@cp -n .env.example .env 2>/dev/null || true
	python domain-1-agentic-architecture/1_1_agentic_loop.py
	@echo "Domain 1 smoke test passed."
	python domain-4-prompt-engineering/4_3_structured_output.py
	@echo "Domain 4 smoke test passed."
	python scenarios/scenario-1-customer-support/agent.py --smoke
	@echo "Scenario 1 smoke test passed."
	@echo "All smoke tests passed."

test:
	pytest scenarios/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
