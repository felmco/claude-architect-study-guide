"""
Task Statement 2.4: Integrate MCP servers into Claude Code and agent workflows

This FastMCP server demonstrates:
- Tool definitions with detailed descriptions (Task 2.1)
- Resources for content catalogs (reduces exploratory tool calls)
- Structured error responses (Task 2.2)
- Environment variable usage (configured via .mcp.json)

Configure in .mcp.json (project-scoped, shared via version control):
  {
    "mcpServers": {
      "study-tools": {
        "type": "stdio",
        "command": "python",
        "args": ["domain-2-tool-design-mcp/2_4_mcp_integration/server.py"],
        "env": { "API_KEY": "${ANTHROPIC_API_KEY:-not-set}" }
      }
    }
  }

MCP Scope Reference (2026 — differs from exam guide v0.1):
  local   → ~/.claude.json (per-project, private) — was: "project" in older docs
  project → .mcp.json in repo root (shared via git) — was: "project" in older docs
  user    → ~/.claude.json (global) — was: "global" in older docs

Usage:
  python server.py   # Run as standalone MCP server
"""

import json
import os
from datetime import datetime, timezone
from fastmcp import FastMCP

mcp = FastMCP("study-guide-mcp")

# Loaded from environment (configured in .mcp.json with ${VAR:-default})
API_KEY = os.environ.get("API_KEY", "not-configured")


# ─── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_domain_info(domain_number: int) -> str:
    """
    Retrieve information about a specific exam domain.

    Returns the domain name, weight percentage, task statement count,
    and the primary files in this study guide that cover the domain.

    Use this tool when a user asks about what's covered in a specific exam domain,
    how much it's weighted, or where to find code examples for it.

    Accepts: domain_number as integer (1-5).
    Returns: JSON with domain name, weight, task_count, and file locations.

    Do NOT use for individual task statement details — use get_task_statement for that.
    """
    domains = {
        1: {
            "name": "Agentic Architecture & Orchestration",
            "weight_pct": 27,
            "task_count": 7,
            "task_range": "1.1-1.7",
            "files": [f"domain-1-agentic-architecture/1_{i}_{name}.py"
                     for i, name in enumerate(["1_agentic_loop", "2_coordinator_subagent",
                                                "3_subagent_spawning", "4_workflow_enforcement",
                                                "5_hooks", "6_task_decomposition", "7_session_management"], 1)],
            "key_concepts": ["stop_reason", "hub-and-spoke", "PostToolUse hooks", "fork_session"],
        },
        2: {
            "name": "Tool Design & MCP Integration",
            "weight_pct": 18,
            "task_count": 5,
            "task_range": "2.1-2.5",
            "files": ["domain-2-tool-design-mcp/2_1_tool_descriptions.py",
                     "domain-2-tool-design-mcp/2_2_structured_errors.py",
                     "domain-2-tool-design-mcp/2_3_tool_distribution.py",
                     "domain-2-tool-design-mcp/2_4_mcp_integration/server.py",
                     "domain-2-tool-design-mcp/2_5_builtin_tools.py"],
            "key_concepts": ["tool descriptions", "isError", "errorCategory", "tool_choice", "MCP scoping"],
        },
        3: {
            "name": "Claude Code Configuration & Workflows",
            "weight_pct": 20,
            "task_count": 6,
            "task_range": "3.1-3.6",
            "files": ["domain-3-claude-code/3_1_claude_md_hierarchy/",
                     "domain-3-claude-code/3_2_commands_skills/",
                     "domain-3-claude-code/3_3_path_rules/",
                     "domain-3-claude-code/3_4_plan_vs_direct.md",
                     "domain-3-claude-code/3_5_iterative_refinement.md",
                     "domain-3-claude-code/3_6_ci_cd/"],
            "key_concepts": ["CLAUDE.md hierarchy", "@import", ".claude/rules/ paths:", "context: fork", "-p flag"],
        },
        4: {
            "name": "Prompt Engineering & Structured Output",
            "weight_pct": 20,
            "task_count": 6,
            "task_range": "4.1-4.6",
            "files": ["domain-4-prompt-engineering/4_3_structured_output.py",
                     "domain-4-prompt-engineering/4_4_validation_retry.py",
                     "domain-4-prompt-engineering/4_5_batch_processing.py"],
            "key_concepts": ["few-shot", "tool_choice forced", "Pydantic retry", "Message Batches API"],
        },
        5: {
            "name": "Context Management & Reliability",
            "weight_pct": 15,
            "task_count": 6,
            "task_range": "5.1-5.6",
            "files": ["domain-5-context-reliability/5_1_context_preservation.py",
                     "domain-5-context-reliability/5_2_escalation_patterns.py",
                     "domain-5-context-reliability/5_3_error_propagation.py"],
            "key_concepts": ["case facts block", "lost-in-middle", "scratchpad files", "claim-source mappings"],
        },
    }

    info = domains.get(domain_number)
    if info is None:
        return json.dumps({
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"Domain {domain_number} does not exist. Valid domains: 1-5.",
        })

    return json.dumps(info, indent=2)


@mcp.tool()
def get_task_statement(task_id: str) -> str:
    """
    Get detailed information about a specific task statement from the exam.

    Accepts task IDs in the format '1.1', '2.3', '4.5', etc. (domain.task_number).
    Returns: description, key skills tested, relevant code file, and whether it
    maps to any of the 12 sample exam questions.

    Use this when preparing for the exam and you want to understand what a specific
    task statement tests and where to find the code examples.

    Do NOT use for domain-level overview — use get_domain_info for that.
    """
    task_map = {
        "1.1": {"desc": "Agentic loop lifecycle: stop_reason handling", "file": "domain-1-agentic-architecture/1_1_agentic_loop.py", "exam_q": None},
        "1.2": {"desc": "Multi-agent coordinator-subagent patterns (hub-and-spoke)", "file": "domain-1-agentic-architecture/1_2_coordinator_subagent.py", "exam_q": "Q7"},
        "1.3": {"desc": "Subagent spawning, context passing, parallel execution", "file": "domain-1-agentic-architecture/1_3_subagent_spawning.py", "exam_q": None},
        "1.4": {"desc": "Workflow enforcement and structured handoffs", "file": "domain-1-agentic-architecture/1_4_workflow_enforcement.py", "exam_q": "Q1"},
        "1.5": {"desc": "Agent SDK hooks: PostToolUse normalization, interception", "file": "domain-1-agentic-architecture/1_5_hooks.py", "exam_q": None},
        "1.6": {"desc": "Task decomposition: chaining vs dynamic", "file": "domain-1-agentic-architecture/1_6_task_decomposition.py", "exam_q": "Q12"},
        "1.7": {"desc": "Session management: resume, fork_session, stale state", "file": "domain-1-agentic-architecture/1_7_session_management.py", "exam_q": None},
        "2.1": {"desc": "Tool descriptions: purpose, inputs, outputs, boundaries", "file": "domain-2-tool-design-mcp/2_1_tool_descriptions.py", "exam_q": "Q2"},
        "2.2": {"desc": "Structured errors: isError, errorCategory, isRetryable", "file": "domain-2-tool-design-mcp/2_2_structured_errors.py", "exam_q": "Q8"},
        "2.3": {"desc": "Tool distribution and tool_choice configuration", "file": "domain-2-tool-design-mcp/2_3_tool_distribution.py", "exam_q": "Q9"},
        "2.4": {"desc": "MCP server configuration: scoping, env vars, resources", "file": "domain-2-tool-design-mcp/2_4_mcp_integration/server.py", "exam_q": None},
        "2.5": {"desc": "Built-in tools: Grep vs Glob vs Read vs Edit selection", "file": "domain-2-tool-design-mcp/2_5_builtin_tools.py", "exam_q": None},
        "3.1": {"desc": "CLAUDE.md hierarchy: user/project/directory levels", "file": "domain-3-claude-code/3_1_claude_md_hierarchy/", "exam_q": "Q4"},
        "3.2": {"desc": "Commands in .claude/commands/, skills with SKILL.md frontmatter", "file": "domain-3-claude-code/3_2_commands_skills/", "exam_q": "Q6"},
        "3.3": {"desc": "Path-specific rules in .claude/rules/ with glob patterns", "file": "domain-3-claude-code/3_3_path_rules/", "exam_q": None},
        "3.4": {"desc": "Plan mode vs direct execution decision criteria", "file": "domain-3-claude-code/3_4_plan_vs_direct.md", "exam_q": "Q5"},
        "3.5": {"desc": "Iterative refinement: examples, test-driven, interview pattern", "file": "domain-3-claude-code/3_5_iterative_refinement.md", "exam_q": None},
        "3.6": {"desc": "CI/CD integration: -p flag, --output-format json, CLAUDE.md in CI", "file": "domain-3-claude-code/3_6_ci_cd/", "exam_q": "Q10"},
        "4.1": {"desc": "Explicit criteria to reduce false positives", "file": "domain-4-prompt-engineering/4_1_explicit_criteria.py", "exam_q": "Q3"},
        "4.2": {"desc": "Few-shot prompting for consistency and format", "file": "domain-4-prompt-engineering/4_2_few_shot.py", "exam_q": None},
        "4.3": {"desc": "Structured output via tool_use and JSON schemas", "file": "domain-4-prompt-engineering/4_3_structured_output.py", "exam_q": None},
        "4.4": {"desc": "Validation-retry loops with error feedback", "file": "domain-4-prompt-engineering/4_4_validation_retry.py", "exam_q": None},
        "4.5": {"desc": "Message Batches API: 50% savings, 24h window, custom_id", "file": "domain-4-prompt-engineering/4_5_batch_processing.py", "exam_q": "Q11"},
        "4.6": {"desc": "Multi-pass review: independent instances, per-file passes", "file": "domain-4-prompt-engineering/4_6_multi_pass_review.py", "exam_q": None},
        "5.1": {"desc": "Context preservation: case facts, trimming, position effects", "file": "domain-5-context-reliability/5_1_context_preservation.py", "exam_q": None},
        "5.2": {"desc": "Escalation criteria: customer requests, policy gaps", "file": "domain-5-context-reliability/5_2_escalation_patterns.py", "exam_q": "Q3"},
        "5.3": {"desc": "Error propagation in multi-agent systems", "file": "domain-5-context-reliability/5_3_error_propagation.py", "exam_q": "Q8"},
        "5.4": {"desc": "Large codebase exploration: scratchpad files, subagent delegation", "file": "domain-5-context-reliability/5_4_large_codebase.py", "exam_q": None},
        "5.5": {"desc": "Human review workflows and confidence calibration", "file": "domain-5-context-reliability/5_5_human_review.py", "exam_q": None},
        "5.6": {"desc": "Information provenance: claim-source mappings, conflict annotation", "file": "domain-5-context-reliability/5_6_provenance.py", "exam_q": None},
    }

    task = task_map.get(task_id)
    if task is None:
        return json.dumps({
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"Task '{task_id}' not found. Format: '1.1' through '5.6'.",
        })

    return json.dumps({"task_id": task_id, **task}, indent=2)


# ─── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("study://exam-overview")
def exam_overview_resource() -> str:
    """
    MCP Resource: Study guide overview and exam statistics.

    Resources expose content catalogs — reduces exploratory tool calls.
    Claude can reference this resource with @study://exam-overview
    """
    return """
Claude Certified Architect — Foundations Exam Overview
=======================================================
Format: Multiple choice, 4 answers, 1 correct
Pass score: 720 / 1000 (scaled)
Domains: 5 (see below)
Scenarios: 4 drawn from 6 (at random per exam sitting)
Exam time: Not specified in guide

Domain Weights:
  1. Agentic Architecture & Orchestration: 27%
  2. Tool Design & MCP Integration: 18%
  3. Claude Code Configuration & Workflows: 20%
  4. Prompt Engineering & Structured Output: 20%
  5. Context Management & Reliability: 15%

Scenario Coverage:
  Scenario 1 (Customer Support): Domains 1, 2, 5 — Questions 1-3
  Scenario 2 (Code Generation): Domains 3, 5 — Questions 4-6
  Scenario 3 (Multi-Agent Research): Domains 1, 2, 5 — Questions 7-9
  Scenario 5 (CI/CD): Domains 3, 4 — Questions 10-12
"""


@mcp.resource("study://cheat-sheet")
def cheat_sheet_resource() -> str:
    """MCP Resource: Exam-day quick reference cheat sheet."""
    return open(
        os.path.join(os.path.dirname(__file__), "../../reference/cheat-sheet.md"), "r"
    ).read() if os.path.exists(
        os.path.join(os.path.dirname(__file__), "../../reference/cheat-sheet.md")
    ) else "Cheat sheet not yet generated. Run: python reference/generate_cheat_sheet.py"


if __name__ == "__main__":
    print("Starting Study Guide MCP Server...")
    print(f"API_KEY configured: {API_KEY != 'not-configured'}")
    mcp.run()
