---
name: explore-codebase
description: Explore the study guide codebase to understand patterns, find examples for a specific exam topic, or locate all files related to a domain
context: fork
allowed-tools: Read, Grep, Glob
argument-hint: "domain name, task statement (e.g. 1.3), or concept (e.g. stop_reason)"
---

# Explore Codebase Skill

Given a topic, domain, or task statement number, find and summarize all relevant files in this study guide.

## Instructions

1. Use `Glob` to find files matching the topic's domain directory
2. Use `Grep` to search for the specific concept or keyword across the codebase
3. Use `Read` to read the most relevant files
4. Return a concise summary: which files cover the topic, key patterns used, and the exam concept demonstrated

## Examples

- `/explore-codebase stop_reason` → finds all agentic loop examples using stop_reason
- `/explore-codebase 1.3` → finds Task Statement 1.3 files (subagent spawning)
- `/explore-codebase tool_choice` → finds all tool_choice usage across Domain 2 and 4

## Note on context: fork

This skill runs in an isolated sub-agent context. Verbose file output stays in the skill's context window and only a concise summary returns to your main conversation. This prevents context exhaustion during exploration.
