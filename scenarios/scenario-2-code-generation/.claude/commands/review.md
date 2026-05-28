# /review — Team Code Review

Run the team's standard review checklist on the current file or diff.

## Usage
```
/review [file]
/review src/components/Button.tsx
```

## Criteria
Flag: SQL injection, XSS, hardcoded secrets, logic bugs, missing null checks
Skip: naming style, line length, import order

Return JSON: `{"findings": [...], "summary": "...", "merge_recommendation": "block|approve_with_notes|approve"}`
