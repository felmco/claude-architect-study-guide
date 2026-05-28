# Scenario 5: Claude Code for CI/CD

**Primary Domains:** 3 (Claude Code Config), 4 (Prompt Engineering)

**Exam questions based on this scenario:** Q10, Q11, Q12

---

## The System

Claude Code integrated into GitHub Actions for automated code review:
- Non-interactive mode (`-p` flag)
- Structured JSON output (`--output-format json --json-schema`)
- Deduplication of findings across commits
- Independent review instance (not the same session that wrote the code)

---

## Key CI/CD Patterns

```bash
# CORRECT: Non-interactive mode (Exam Q10 — Answer A)
claude -p "Review for security issues" --output-format json --json-schema schema.json

# WRONG: Will hang waiting for interactive input
claude "Review for security issues"
```

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/claude-review.yml` | GitHub Actions workflow |
| `review_schema.json` | JSON schema for structured findings output |
| `review_prompt.md` | Few-shot examples for code review |

---

## Exam Questions Exercised

**Q10:** Pipeline hangs → add `-p` flag for non-interactive mode.

**Q11:** Batch API for overnight debt report only; sync for pre-merge (blocking).

**Q12:** 14-file PR inconsistent → split into per-file passes + integration pass.
