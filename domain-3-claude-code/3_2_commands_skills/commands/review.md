# /review — Team Code Review Command

> **Exam Key:** Stored in `.claude/commands/review.md` (project-scoped)
> Available to ALL developers via version control.
> Personal commands → `~/.claude/commands/` (not shared)

Run this team's standard code review checklist on the specified file or current changes.

## Usage
```
/review [file-or-path]
/review src/auth.py
/review  # reviews current git diff
```

## Review Checklist

Analyze the code for these specific categories:

### Must Flag (high confidence required)
- **Bugs**: Logic errors, off-by-one errors, null pointer risks
- **Security**: SQL injection, XSS, hardcoded secrets, insecure deserialization
- **Data integrity**: Missing transaction wrapping, race conditions

### Skip (do not report)
- Minor style preferences (variable naming, line length within limits)
- Local patterns that appear in CLAUDE.md as accepted conventions
- Theoretical risks with no realistic attack vector in this context

### Severity Levels
- **Critical**: Exploitable security issue or data loss risk → block merge
- **High**: Significant bug that will manifest in production → block merge
- **Medium**: Subtle bug or moderate risk → fix before merge recommended
- **Low**: Minor improvement, not blocking → informational

## Output Format
Return findings as JSON:
```json
{
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "file": "path/to/file.py",
      "line": 42,
      "issue": "SQL injection via unsanitized user input",
      "suggestion": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    }
  ],
  "summary": "2 critical, 1 high findings. Recommend blocking merge."
}
```
