# API Changes: Exam Guide v0.1 (Feb 2025) vs Current Docs (May 2026)

This file documents terminology and API changes between the exam guide and current documentation.
The exam tests based on the v0.1 guide — but understanding current docs helps you understand WHY things work the way they do.

---

## 1. SDK Name Change

| Exam Guide (v0.1) | Current Docs (2026) |
|-------------------|---------------------|
| "Claude Code SDK" | "Claude Agent SDK" |

The SDK was renamed to reflect its broader capabilities beyond coding tasks.
The underlying concepts (Task tool, allowedTools, subagents, hooks) are the same.

---

## 2. MCP Scope Names

This is the most likely cause of confusion on the exam.

| Old Name (in some older docs) | Current (2026) | Meaning |
|-------------------------------|----------------|---------|
| `project` | `local` | Per-project, private to you, stored in `~/.claude.json` |
| `project` | `project` | Shared with team via `.mcp.json` in repo |
| `global` | `user` | All your projects, private, stored in `~/.claude.json` |

**Current scope behavior:**
- `local` (default): stored in `~/.claude.json` under the current project path
- `project`: stored in `.mcp.json` committed to the repo (shared via git)
- `user`: stored in `~/.claude.json` globally (all projects on your machine)

**Exam Guide v0.1 says:**
> "MCP server scoping: project-level (`.mcp.json`) for shared team tooling vs user-level (`~/.claude.json`) for personal/experimental servers"

The exam guide description of the BEHAVIOR is correct even if terminology shifted.

---

## 3. Subagent Spawning Constraint (2026 addition)

**Exam Guide v0.1:** Does not explicitly state this constraint.

**Current Docs (2026):** Subagents **cannot spawn their own subagents**.

Only the main agent (coordinator) can spawn subagents. Subagents are leaf nodes.
This is why all inter-subagent communication routes through the coordinator.

---

## 4. tool_choice = "none" Added

**2026:** Added `{"type": "none"}` as an explicit option (default when no tools provided).

Exam questions use `"auto"`, `"any"`, and forced tool selection — these are unchanged.

---

## 5. input_examples Field Added

**2026:** Tool definitions now accept an optional `input_examples` array:
```python
{
    "name": "get_weather",
    "input_schema": {...},
    "input_examples": [        # NEW in 2026
        {"location": "San Francisco, CA", "unit": "fahrenheit"},
        {"location": "Tokyo, Japan"}
    ]
}
```

The exam guide doesn't mention this — it's a 2026 addition. Core concepts (detailed descriptions) remain the primary mechanism.

---

## 6. Tool Search / Deferred Loading

**2026:** MCP tools are now deferred by default (Tool Search). Only tool names load at session start; schemas load on demand.

**Exam Guide:** Tests the fundamental pattern of all tools being available from configured MCP servers.

For exam purposes: understand that tools from all configured MCP servers are **discovered at connection time and available to the agent** — this is what the exam tests.

---

## 7. MCP Transport Types

**Exam Guide:** Focuses on stdio transport (`.mcp.json` with `command` field).

**2026:** Three transport types:
- `stdio` — local process (exam focus)
- `http` / `streamable-http` — remote HTTP server
- `sse` — Server-Sent Events (deprecated in 2026)

The core concepts (project vs user scoping, env var expansion, `.mcp.json` format) are the same.

---

## 8. /compact Command

**Exam Guide:** References `/compact` for reducing context usage.

**2026:** `/compact` remains available — compresses prior conversation context.

For exam: know that `/compact` reduces context during extended exploration sessions.

---

## 9. Structured Outputs (2026 addition)

**2026:** A new `structured_outputs` feature was added as a beta capability (separate from tool_use).

**Exam Guide:** Tests tool_use with JSON schemas as the primary structured output method.

For exam purposes: `tool_use` with JSON schemas = the exam-tested approach. Structured outputs is a newer addition not in the v0.1 exam guide.
