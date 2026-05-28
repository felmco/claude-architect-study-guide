# Task 3.4: Plan Mode vs Direct Execution

## Decision Matrix

| Factor | Use Plan Mode | Use Direct Execution |
|--------|--------------|---------------------|
| Number of files affected | >5 files | 1-2 files |
| Architectural impact | Reshapes structure | Localized change |
| Valid approaches | Multiple valid options | Clear single approach |
| Reversibility | Hard to undo | Easy to undo |
| Dependencies | Complex, many | None or simple |
| Discovery needed | Must explore first | Already understood |

---

## When to Use Plan Mode

**Monolith-to-microservices restructuring (Exam Q5 — correct answer)**
- 45+ files affected
- Multiple valid service boundary decisions
- Dependencies must be mapped before committing to an approach
- Architectural decisions will be hard to reverse

**Library migration (e.g., requests → httpx)**
- Affects many files across the codebase
- May require different patterns in different contexts
- Risk of breaking changes needs systematic assessment

**Feature with multiple implementation approaches**
- Different database schemas possible
- Different caching strategies possible
- Architectural choice has long-term implications

---

## When to Use Direct Execution

**Single-file bug fix (Exam Q5 — contrast)**
```
"The login function raises KeyError when email is None"
→ Clear stack trace, single function, obvious fix
→ Direct execution: go fix it
```

**Adding one validation check**
```
"Add email format validation to the registration endpoint"
→ Well-scoped, one file, clear implementation
→ Direct execution: add the check
```

**Renaming a constant**
```
"Rename MAX_RETRIES to MAX_RETRY_COUNT"
→ Simple find-and-replace
→ Direct execution
```

---

## The Explore Subagent

For tasks where you need extensive discovery before planning, use the `Explore` subagent
(`/explore-codebase` skill in this repo) to isolate verbose discovery output.

**Why:** Without `Explore`, a long discovery phase fills your main context window
with file contents, leaving less space for actual implementation.

**Pattern:**
1. Invoke `Explore` subagent to map the codebase
2. Explore returns a concise summary (not raw file contents)
3. Use that summary in your main session to plan and implement

---

## Combining Plan Mode + Direct Execution

A common workflow:
1. **Plan mode**: Explore codebase → design the approach → get approval
2. **Direct execution**: Implement the approved plan

Example:
```
Phase 1 (Plan mode): "I'll analyze the codebase, map all dependencies,
                      and design the microservice boundaries"
Phase 2 (Direct): Execute the specific changes planned in phase 1
```

---

## Exam Reference

**Q5 — Correct answer: A (Plan mode)**

Task: Restructure monolithic application into microservices.
- Changes across DOZENS of files ✓
- Architectural decisions required ✓
- Multiple valid service boundary options ✓

**Why not B (direct execution + incremental)?**
"Letting implementation reveal service boundaries" → costly rework when dependencies discovered late

**Why not C (direct execution with upfront instructions)?**
"Detailing how each service should be structured" → assumes you know the structure without exploring

**Why not D (start direct, switch to plan if needed)?**
"Switch to plan mode if you encounter unexpected complexity" → complexity is already stated in requirements
