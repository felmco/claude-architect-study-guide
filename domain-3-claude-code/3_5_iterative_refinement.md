# Task 3.5: Iterative Refinement Techniques

## Technique 1: Concrete Input/Output Examples

**When to use:** Natural language descriptions produce inconsistent results.

**Problem:**
```
"Transform the data format to be more readable"
→ Claude interprets "readable" differently each time
→ Inconsistent results across iterations
```

**Solution:**
```
Provide 2-3 concrete examples:

Input:  {"ts": 1748390400, "status": 3, "amount_cents": 2500}
Output: {"timestamp": "2025-05-28T00:00:00Z", "status": "delivered", "amount_usd": 25.00}

Input:  {"ts": 1748476800, "status": 1, "amount_cents": 9900}
Output: {"timestamp": "2025-05-29T00:00:00Z", "status": "processing", "amount_usd": 99.00}
```

The examples clarify: Unix → ISO 8601, status codes → strings, cents → dollars.
Prose can't communicate all three transformations as clearly.

---

## Technique 2: Test-Driven Iteration

**When to use:** Complex logic with edge cases.

**Pattern:**
1. Write tests FIRST covering expected behavior, edge cases, and performance
2. Share failing tests with Claude
3. Claude implements to make tests pass
4. Repeat with additional test cases for newly discovered edges

**Example:**
```python
def test_migration_handles_null_email():
    result = migrate_user({"name": "Jane", "email": None})
    assert result["email"] is None  # Should not throw

def test_migration_handles_duplicate_phone():
    result = migrate_user({"phone": "555-1234", "phone2": "555-1234"})
    assert result["phones"] == ["555-1234"]  # Deduped, not doubled
```

Share these tests with Claude: "These 2 tests fail. Fix the migration."
Claude sees exactly what's expected for each edge case.

---

## Technique 3: The Interview Pattern

**When to use:** Unfamiliar domain where you don't know the right questions to ask.

**How:**
```
"Before implementing a caching solution for our API, ask me 5-10 questions
to understand our constraints and requirements. Don't implement yet."
```

Claude might ask:
- "What's your current cache invalidation strategy?"
- "Do you need cache sharing across multiple instances?"
- "What's your acceptable staleness tolerance?"
- "Do you handle cache stampede scenarios?"

These surface considerations you hadn't thought of, preventing costly rework.

---

## Technique 4: Single Message for Interacting Issues

**When to use:** Multiple issues that affect each other.

**Problem with sequential iteration:**
```
Turn 1: "Fix bug A"
Turn 2: "Fix bug B"
→ Fix for B might undo fix for A if they interact
→ Claude doesn't see both constraints simultaneously
```

**Solution:**
```
Single message: "Fix bug A (line 42), bug B (line 87), and edge case C (line 103).
Note that A and B both affect the auth state — ensure fixes are consistent."
→ Claude sees all constraints at once and can find compatible solution
```

**Sequential iteration is fine for:**
```
"Fix the typo in the variable name" (then)
"Add the missing null check in a different function"
→ Independent changes, no interaction risk
```

---

## Technique 5: Specific Test Cases for Edge Cases

```
"The migration script fails on records where middle_name is null.
Here's a specific failing case:
  Input: {"first": "Jane", "middle_name": null, "last": "Smith"}
  Expected: {"full_name": "Jane Smith"}  # null middle_name skipped
  Actual: {"full_name": "Jane null Smith"}  # null included as string

Fix this specific case."
```

Giving exact input + expected + actual is dramatically more effective than
"the script doesn't handle null values in some fields."
