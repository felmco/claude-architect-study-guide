# Concepts Glossary

All key terms from the exam guide appendix, with definitions and code references.

---

## A

**Agentic loop** — A control flow pattern where an application repeatedly sends requests to Claude, executes tool calls requested by Claude, appends results to conversation history, and continues until `stop_reason == "end_turn"`.
→ `domain-1-agentic-architecture/1_1_agentic_loop.py`

**AgentDefinition** — Configuration for a subagent type in the Agent SDK: name, description, system prompt, and `allowedTools`.
→ `domain-1-agentic-architecture/1_3_subagent_spawning.py`

**allowedTools** — List of tool names a coordinator agent is permitted to use. Must include `"Task"` for a coordinator to spawn subagents.
→ `scenarios/scenario-3-multi-agent-research/coordinator.py`

**argument-hint** — SKILL.md frontmatter field that prompts the user for required arguments when invoking a skill without arguments.
→ `.claude/skills/explore-codebase/SKILL.md`

---

## B

**Batch API** — See "Message Batches API"

**built-in tools** — Tools available natively in Claude Code: `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`. Selected based on operation type (content search vs file name search vs file modification).
→ `domain-2-tool-design-mcp/2_5_builtin_tools.py`

---

## C

**case facts block** — A persistent structured block containing transactional facts (amounts, dates, IDs) that is included in every prompt, outside summarized conversation history. Prevents loss of critical values during summarization.
→ `domain-5-context-reliability/5_1_context_preservation.py`

**claim-source mapping** — A structured data format linking each factual claim to its source (URL, title, publication date, evidence excerpt). Must be preserved through synthesis steps to maintain attribution.
→ `domain-5-context-reliability/5_6_provenance.py`

**Claude Agent SDK** — The current name (2026) for what the exam guide calls the "Claude Code SDK." Provides the framework for building agentic applications with subagents, hooks, and the Task tool.

**CLAUDE.md** — Special file read by Claude at the start of every conversation. Can be placed at user level (`~/.claude/`), project level (repo root), or directory level. @import syntax for modularity.
→ `domain-3-claude-code/3_1_claude_md_hierarchy/`

**context: fork** — SKILL.md frontmatter option that runs a skill in an isolated sub-agent context. Verbose skill output stays in the sub-agent's context; only the final response returns to the main conversation.
→ `.claude/skills/explore-codebase/SKILL.md`

**custom_id** — A user-provided identifier in Message Batches API requests. Used to correlate each request with its response, and to identify failed requests for resubmission.
→ `domain-4-prompt-engineering/4_5_batch_processing.py`

---

## E

**end_turn** — A `stop_reason` value indicating Claude has completed its response. The agentic loop should terminate when this value is received.

**errorCategory** — Field in a structured MCP error response indicating the type of failure: `transient`, `validation`, `permission`, or `business`.
→ `domain-2-tool-design-mcp/2_2_structured_errors.py`

**Explore subagent** — A built-in Claude Code subagent type used to isolate verbose discovery output. The `Explore` agent reads files and returns only summaries, preserving the main agent's context window.
→ `domain-3-claude-code/3_4_plan_vs_direct.md`

---

## F

**few-shot examples** — 2-4 concrete input/output examples included in a prompt to demonstrate expected behavior, output format, and handling of ambiguous cases. More effective than detailed prose instructions for consistency.
→ `domain-4-prompt-engineering/4_2_few_shot.py`

**fork_session** — Agent SDK concept that creates an independent branch from the current session state, enabling exploration of divergent approaches without polluting the original context.
→ `domain-1-agentic-architecture/1_7_session_management.py`

---

## H

**hub-and-spoke architecture** — Multi-agent pattern where a coordinator agent manages all communication between subagents. No direct subagent-to-subagent communication. All information routes through the coordinator.
→ `domain-1-agentic-architecture/1_2_coordinator_subagent.py`

---

## I

**isError** — Boolean flag in MCP tool results indicating whether the tool call resulted in an error. When `true`, the model knows to make a recovery decision rather than proceeding normally.
→ `domain-2-tool-design-mcp/2_2_structured_errors.py`

**isRetryable** — Boolean in structured error responses indicating whether retrying the same call might succeed. `false` prevents the agent from wasting retry attempts on business rule violations.

---

## L

**lost-in-the-middle** — The tendency for models to reliably process information at the beginning and end of long inputs but miss content in the middle. Mitigation: put key findings first, use section headers.
→ `domain-5-context-reliability/5_1_context_preservation.py`

---

## M

**Message Batches API** — Anthropic API for asynchronous batch processing of multiple requests. Offers 50% cost savings with up to 24-hour processing windows. No guaranteed latency SLA. Not suitable for blocking workflows.
→ `domain-4-prompt-engineering/4_5_batch_processing.py`

**MCP (Model Context Protocol)** — Open standard for connecting AI applications to external systems via tools and resources. MCP servers expose tools (actions) and resources (content catalogs) to the agent.
→ `domain-2-tool-design-mcp/2_4_mcp_integration/server.py`

---

## P

**path rules** — Files in `.claude/rules/` with YAML frontmatter `paths:` field containing glob patterns. These rules are automatically loaded only when editing files matching the patterns.
→ `domain-3-claude-code/3_3_path_rules/`

**plan mode** — Claude Code mode that enables codebase exploration and design before making changes. Used for complex tasks with architectural implications, multiple valid approaches, or many files affected.
→ `domain-3-claude-code/3_4_plan_vs_direct.md`

**PostToolUse** — Hook pattern that intercepts tool results after execution but before the model processes them. Used for data normalization (timestamps, status codes).
→ `domain-1-agentic-architecture/1_5_hooks.py`

**PreToolUse** — Hook pattern that intercepts outgoing tool calls before execution. Used for policy enforcement (blocking refunds over $500).
→ `domain-1-agentic-architecture/1_5_hooks.py`

**prompt chaining** — Task decomposition pattern where the output of one prompt step feeds as input to the next. Fixed sequential steps. Contrast with dynamic decomposition.
→ `domain-1-agentic-architecture/1_6_task_decomposition.py`

---

## R

**resources (MCP)** — Mechanism for exposing content catalogs to agents via `@resource` references. Reduces exploratory tool calls by giving agents visibility into available data upfront.
→ `domain-2-tool-design-mcp/2_4_mcp_integration/server.py`

---

## S

**scratchpad file** — A file written by an agent to persist key findings across context boundaries. Referenced in subsequent context windows so findings survive `/compact` and context resets.
→ `domain-5-context-reliability/5_4_large_codebase.py`

**SKILL.md** — The required file inside a `.claude/skills/<name>/` directory. Contains YAML frontmatter (name, description, context, allowed-tools, argument-hint) and the skill's instructions.
→ `.claude/skills/explore-codebase/SKILL.md`

**stop_reason** — The reason a Claude API response terminated. Key values: `"tool_use"` (Claude wants to call tools), `"end_turn"` (Claude finished responding).

**stratified sampling** — Sampling strategy that samples different subpopulations (e.g., high-confidence vs low-confidence extractions) at different rates. Used to detect hidden accuracy failures in specific segments.
→ `domain-5-context-reliability/5_5_human_review.py`

---

## T

**Task tool** — The mechanism in the Claude Agent SDK for spawning subagents. A coordinator's `allowedTools` must include `"Task"` to use it. Each Task call spawns an isolated subagent.
→ `domain-1-agentic-architecture/1_3_subagent_spawning.py`

**tool_choice** — API parameter controlling which tool (if any) Claude must call. Options: `"auto"` (model decides), `"any"` (must call a tool), `{"type": "tool", "name": "X"}` (must call X), `"none"`.
→ `domain-2-tool-design-mcp/2_3_tool_distribution.py`

**tool_use** — A `stop_reason` value and content block type indicating Claude wants to call one or more tools. The agentic loop should execute the requested tools and return results.
