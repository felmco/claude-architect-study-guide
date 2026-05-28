# /smoke-test — Run Smoke Tests

Run the minimal end-to-end smoke tests for this study guide.

## Usage
```
/smoke-test
```

## What It Runs
```bash
make smoke-test
```

This runs:
1. `python domain-1-agentic-architecture/1_1_agentic_loop.py` — basic agentic loop
2. `python domain-4-prompt-engineering/4_3_structured_output.py` — structured output via tool_use
3. `python scenarios/scenario-1-customer-support/agent.py --smoke` — full customer support scenario

Expected cost: $0.05–0.15 using claude-haiku-4-5.
