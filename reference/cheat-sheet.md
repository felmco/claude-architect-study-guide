# Exam-Day Cheat Sheet

## Domain Weights
| Domain | Weight | Top Files to Know |
|--------|--------|-----------------|
| 1. Agentic Architecture | **27%** | 1_1_agentic_loop.py, 1_4_workflow_enforcement.py, 1_5_hooks.py |
| 3. Claude Code Config | **20%** | .claude/rules/, SKILL.md frontmatter, -p flag |
| 4. Prompt Engineering | **20%** | 4_3_structured_output.py, 4_5_batch_processing.py |
| 2. Tool Design & MCP | **18%** | 2_1_tool_descriptions.py, 2_2_structured_errors.py |
| 5. Context & Reliability | **15%** | 5_2_escalation_patterns.py, 5_3_error_propagation.py |

---

## stop_reason Values
| Value | Meaning | Action |
|-------|---------|--------|
| `"tool_use"` | Model wants to call tools | Execute tools, append results, continue loop |
| `"end_turn"` | Model finished | Extract text, terminate loop |
| `"max_tokens"` | Token limit hit | Handle gracefully |

**Key:** Terminate on `"end_turn"`, NOT on text content patterns.

---

## tool_choice Options
| Value | Effect | Use When |
|-------|--------|----------|
| `{"type": "auto"}` | Model chooses | Default; model may respond in text |
| `{"type": "any"}` | Must call a tool | Need guaranteed structured output |
| `{"type": "tool", "name": "X"}` | Must call tool X | Prerequisite step must run first |
| `{"type": "none"}` | Cannot call tools | Text-only response needed |

---

## MCP Scope Reference (2026 — different from v0.1 exam guide)
| Scope | Stored In | Shared? | Old Name |
|-------|-----------|---------|----------|
| `local` (default) | `~/.claude.json` per-project | No | "project" (old) |
| `project` | `.mcp.json` in repo | Yes (via git) | "project" (old) |
| `user` | `~/.claude.json` global | No | "global" (old) |

> Exam guide (v0.1) uses old terminology. Current docs use `local`/`project`/`user`.

---

## Structured Error Fields
```json
{
  "isError": true,
  "errorCategory": "transient|validation|permission|business",
  "isRetryable": true|false,
  "message": "Human-readable description",
  "customerMessage": "What to tell the customer"
}
```

| Category | Retryable? | Agent Action |
|----------|-----------|-------------|
| `transient` | Yes | Retry with backoff |
| `validation` | No (fix input) | Ask user for correct input |
| `permission` | No | Escalate or inform |
| `business` | No | Inform of policy, offer alternatives |

---

## Escalation Triggers (Not Sentiment-Based)
| Trigger | Action |
|---------|--------|
| Customer says "I want a human" | Escalate IMMEDIATELY, no negotiation |
| Refund > $500 | Escalate (or hook blocks it) |
| Policy gap | Escalate (policy silent on this case) |
| 2+ failed resolution attempts | Escalate |
| Customer is frustrated but issue is resolvable | DO NOT escalate |

---

## CLAUDE.md Hierarchy
```
~/.claude/CLAUDE.md           ← User-level (personal, NOT shared)
<repo>/CLAUDE.md              ← Project-level (shared via git ✓)
<repo>/src/CLAUDE.md          ← Directory-level (applies to src/)
```

**Key:** User-level = NOT shared. If team members don't get instructions → move to project-level.

---

## .claude/ Structure
```
.claude/
├── commands/review.md       ← /review available to all (project-scoped)
├── rules/tests.md           ← paths: ["**/*.test.*"] auto-loaded for test files
└── skills/explore/SKILL.md  ← context: fork, allowed-tools: Read,Grep,Glob
```

SKILL.md frontmatter options:
- `context: fork` — runs in isolated sub-agent
- `allowed-tools: Read,Grep,Glob` — restrict tool access
- `argument-hint: "..."` — prompt for missing args

---

## Message Batches API
| Characteristic | Value |
|---------------|-------|
| Cost savings | 50% vs sync |
| Max processing time | 24 hours |
| Latency SLA | None |
| Multi-turn tool calling | NOT supported |
| Request correlation | `custom_id` field |

**Use:** Overnight reports, weekly audits, mass extraction
**Don't use:** Blocking pre-merge checks, real-time responses

---

## CLI Flags
```bash
claude -p "prompt"                    # Non-interactive mode (CI/CD)
claude -p "..." --output-format json  # JSON output
claude -p "..." --json-schema schema  # Enforce JSON schema
claude --resume session-name          # Resume named session
```

---

## Built-in Tool Selection
| Tool | Use For |
|------|---------|
| `Grep` | Search file CONTENTS for patterns |
| `Glob` | Find FILE NAMES matching patterns |
| `Read` | Load full file contents |
| `Edit` | Targeted modification (unique anchor text required) |
| `Write` | Create/overwrite file (Read first!) |
| `Bash` | Shell operations no other tool handles |

**Edit fails?** → Read + Write as fallback.

---

## Anti-Patterns Summary
| What They Test | Wrong | Right |
|----------------|-------|-------|
| Loop termination | Check `response.content[0].text` for "done" | Check `stop_reason == "end_turn"` |
| Tool ordering | System prompt: "always call X first" | Programmatic prerequisite |
| Escalation | Self-reported confidence < 7 | Explicit categorical criteria |
| Error propagation | Return `{"status": "unavailable"}` | Structured error with category, retryable, alternatives |
| CI/CD | No special flag | `claude -p "..."` |
| Test conventions | Directory CLAUDE.md | `.claude/rules/` with `paths: ["**/*.test.*"]` |
| Task decomposition too narrow | Visual arts only for "creative industries" | Comprehensive subtopic coverage |
