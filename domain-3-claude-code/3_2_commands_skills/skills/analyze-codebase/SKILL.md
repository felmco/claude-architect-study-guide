---
name: analyze-codebase
description: Explore and summarize the codebase structure, entry points, dependencies, and patterns for a given topic, domain, or file path
context: fork
allowed-tools: Read,Grep,Glob
argument-hint: "topic, file path, or domain number (e.g. 'stop_reason', 'domain-1', 'auth flow')"
---

# Analyze Codebase Skill

## What This Skill Does

Given a topic or area to explore, this skill:
1. Uses Glob to find all relevant files by pattern
2. Uses Grep to search for key symbols, patterns, or concepts
3. Uses Read to examine the most relevant files in detail
4. Returns a concise summary: what exists, where it is, key patterns

## Why context: fork

This skill runs in an **isolated sub-agent context**. All the verbose file reading and
search output stays inside the skill's context window. Only the final concise summary
returns to your main conversation. This prevents context window exhaustion during
multi-phase exploration tasks.

## Why allowed-tools: Read,Grep,Glob

This skill has READ-ONLY access to prevent accidental modifications during exploration.
If you need to make changes after exploring, return to the main session.

## Usage Examples

```
/analyze-codebase stop_reason
```
→ Finds all agentic loop code using stop_reason, summarizes patterns

```
/analyze-codebase domain-1
```
→ Lists all Domain 1 files, summarizes what each covers

```
/analyze-codebase escalation criteria
```
→ Finds all escalation-related code across scenarios

## Output Format

Return a structured summary:
- **Files found**: List of relevant file paths
- **Key patterns**: Code patterns used
- **Exam concepts**: Which task statements are demonstrated
- **Recommendation**: Which file to read next for deep understanding

## Limitations

- Cannot modify files (allowed-tools: Read,Grep,Glob only)
- Cannot execute code or run tests
- For modifications: describe what to change, then exit skill and implement in main session
