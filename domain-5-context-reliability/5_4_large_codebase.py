"""
Task Statement 5.4: Manage context effectively in large codebase exploration

Key concepts:
- Context degradation: extended sessions give inconsistent answers, reference "typical patterns"
- Scratchpad files: persist key findings across context boundaries
- Subagent delegation: isolate verbose exploration output from main agent
- Structured state persistence for crash recovery (manifest pattern)
- /compact: reduce context usage during extended exploration sessions
"""

import json
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Scratchpad file pattern ───────────────────────────────────────────────────

class ExplorationScratchpad:
    """
    Persist key findings to a file so they survive context window resets.

    When context fills up and gets compacted/summarized, the scratchpad
    provides a reliable source of discovered facts that can be re-injected.
    """

    def __init__(self, session_id: str, path: str = "/tmp"):
        self.session_id = session_id
        self.filepath = f"{path}/scratchpad_{session_id}.json"
        self._data: dict = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "key_findings": [],
            "entry_points": [],
            "dependencies_map": {},
            "high_risk_areas": [],
            "completed_areas": [],
            "pending_areas": [],
        }

    def record_finding(self, area: str, finding: str, severity: str = "info"):
        """Record a key finding to survive context boundaries."""
        self._data["key_findings"].append({
            "area": area,
            "finding": finding,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()

    def record_entry_point(self, file: str, function: str, description: str):
        """Track discovered entry points."""
        self._data["entry_points"].append({
            "file": file, "function": function, "description": description
        })
        self.save()

    def mark_completed(self, area: str):
        if area not in self._data["completed_areas"]:
            self._data["completed_areas"].append(area)
        if area in self._data["pending_areas"]:
            self._data["pending_areas"].remove(area)
        self.save()

    def as_context_injection(self) -> str:
        """Format scratchpad contents for injection into next context window."""
        findings_text = "\n".join(
            f"  [{f['severity'].upper()}] {f['area']}: {f['finding']}"
            for f in self._data["key_findings"][-20:]  # Last 20 findings
        )
        return f"""
=== SCRATCHPAD: Prior Exploration Findings ===
(Reference these instead of re-exploring completed areas)

Session: {self._data['session_id']}
Completed areas: {', '.join(self._data['completed_areas'])}
Pending areas: {', '.join(self._data['pending_areas'])}

Key findings:
{findings_text}

Entry points discovered: {len(self._data['entry_points'])} files
High-risk areas: {', '.join(self._data['high_risk_areas'])}
=== END SCRATCHPAD ===
"""

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass  # Silent fail for demo purposes

    @classmethod
    def load(cls, session_id: str, path: str = "/tmp") -> Optional["ExplorationScratchpad"]:
        filepath = f"{path}/scratchpad_{session_id}.json"
        if not os.path.exists(filepath):
            return None
        with open(filepath) as f:
            data = json.load(f)
        pad = cls(session_id, path)
        pad._data = data
        return pad


# ─── Crash recovery manifest ───────────────────────────────────────────────────

class CrashRecoveryManifest:
    """
    Structured state persistence for crash recovery.

    Each agent exports state to a known location.
    Coordinator loads manifest on resume and injects into agent prompts.
    """

    def __init__(self, manifest_path: str = "/tmp/agent_manifest.json"):
        self.path = manifest_path
        self._manifest = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "agents": {},
            "overall_phase": "not_started",
            "completed_tasks": [],
            "in_progress_tasks": [],
            "pending_tasks": [],
        }

    def update_agent_state(self, agent_name: str, state: dict):
        """Agent calls this to export its current state."""
        self._manifest["agents"][agent_name] = {
            **state,
            "exported_at": datetime.now().isoformat(),
        }
        self._manifest["last_updated"] = datetime.now().isoformat()
        self.save()

    def get_resumption_prompt(self, agent_name: str) -> str:
        """Generate a resumption prompt for an agent from its saved state."""
        agent_state = self._manifest["agents"].get(agent_name, {})
        if not agent_state:
            return f"Agent '{agent_name}' has no saved state. Start fresh."

        return f"""
RESUMING SESSION for agent: {agent_name}
State exported at: {agent_state.get('exported_at')}

Completed tasks: {agent_state.get('completed', [])}
In-progress (resume here): {agent_state.get('in_progress', [])}
Findings so far: {json.dumps(agent_state.get('findings', []), indent=2)}

Continue from where you left off. Do NOT re-do completed tasks.
"""

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self._manifest, f, indent=2)


# ─── Subagent delegation for codebase exploration ─────────────────────────────

def explore_with_subagent_delegation(topic: str) -> str:
    """
    Demonstrates how to use subagent delegation to isolate verbose exploration.

    Main agent stays at high level. Subagents do the verbose file reading.
    Only concise summaries return to main agent (preserves main context).
    """
    # In production Agent SDK: main agent spawns this as a Task
    # Here we simulate with a separate API call

    explore_prompt = f"""You are an exploration subagent. Your task is highly focused:

Find all test files in this study guide codebase related to: {topic}

Steps:
1. Think about what file names or patterns would be relevant
2. List the likely files based on the topic
3. Summarize: how many files, what they contain, which exam task they map to

Return a CONCISE summary (not file contents). The main agent has limited context.
Maximum 200 words in your response.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": explore_prompt}],
    )

    summary = response.content[0].text
    print(f"  Subagent exploration summary ({len(summary)} chars — concise, not raw file contents):")
    return summary


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 5.4: Large Codebase Context Management")
    print("=" * 60)

    print("\n=== 1. Scratchpad File Pattern ===")
    pad = ExplorationScratchpad("investigation-2025-05-28")
    pad.record_finding("auth.py", "SQL injection in login()", "critical")
    pad.record_finding("orders.py", "N+1 query pattern in list_orders()", "medium")
    pad.record_entry_point("main.py", "main()", "Application entry point")
    pad.mark_completed("auth.py")
    pad._data["pending_areas"] = ["orders.py", "payments.py"]

    context = pad.as_context_injection()
    print(f"Scratchpad context injection ({len(context)} chars):")
    print(context[:400])

    print("\n=== 2. Crash Recovery Manifest ===")
    manifest = CrashRecoveryManifest("/tmp/study_guide_manifest.json")
    manifest.update_agent_state("search_agent", {
        "completed": ["web_search_1", "web_search_2"],
        "in_progress": ["web_search_3"],
        "findings": [{"query": "AI adoption", "results": 3}],
    })
    print("Search agent state exported. Resumption prompt:")
    print(manifest.get_resumption_prompt("search_agent")[:300])

    print("\n=== 3. Subagent Delegation for Verbose Exploration ===")
    summary = explore_with_subagent_delegation("agentic loops")
    print(f"Summary: {summary}")

    print("\n=== 4. /compact Usage ===")
    print("When context fills with verbose discovery output:")
    print("  /compact  →  Claude compresses prior context, preserves key findings")
    print("  Use before: starting a new exploration phase")
    print("  Use after: filling context with file reads")
    print("  Key: after /compact, inject scratchpad findings so they're not lost")

    print("\n" + "=" * 60)
    print("Scratchpad files: persist findings across context boundaries")
    print("Subagent delegation: verbose output stays in subagent, summary returns")
    print("Crash manifest: coordinator loads on resume, injects into agent prompts")


if __name__ == "__main__":
    main()
