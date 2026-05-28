# /review — Code Review Checklist

Run a focused code review on the current file or specified path.

## Usage
```
/review [path]
```

## Checklist Applied
1. Does every `.py` file have a `main()` function?
2. Are all Anthropic API calls using the correct model names?
3. Is `stop_reason` handled for both `"tool_use"` and `"end_turn"`?
4. Are tool descriptions detailed enough (3+ sentences, inputs, outputs, when-to-use)?
5. Are structured errors using `isError`, `errorCategory`, and `isRetryable`?
6. Does any code rely on prompt-only enforcement for critical business rules?
7. Are nullable fields used where source data may be absent?
8. Is `custom_id` used in any Message Batches API calls?

Flag issues with: file path, line number, issue description, and suggested fix.
