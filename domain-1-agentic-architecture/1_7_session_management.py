"""
Task Statement 1.7: Manage session state, resumption, and forking

Key concepts:
- Named session resumption: --resume <session-name> for prior conversations
- fork_session: independent branches from a shared analysis baseline
- Inform resumed sessions about changes to previously analyzed files
- Fresh session + structured summary > resuming with stale tool results
- Session context isolation: subagents don't share sessions

CLI Usage (in Claude Code):
  claude --resume my-session-name          # Resume a named session
  claude --resume                           # Resume most recent session

fork_session is an Agent SDK concept for creating divergent exploration branches.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")


# ─── Session State Pattern ─────────────────────────────────────────────────────

class SessionState:
    """
    Structured session state for persistence across context boundaries.

    Used for crash recovery: each agent exports state to a known location,
    and the coordinator loads a manifest on resume.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now().isoformat()
        self.findings: list[dict] = []
        self.analyzed_files: list[str] = []
        self.pending_tasks: list[str] = []
        self.completed_tasks: list[str] = []
        self.phase: str = "initialization"

    def to_manifest(self) -> dict:
        """Export state as a manifest for crash recovery / session resumption."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "phase": self.phase,
            "analyzed_files": self.analyzed_files,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "findings_count": len(self.findings),
            "key_findings": self.findings[-5:] if self.findings else [],  # Last 5 for context
        }

    @classmethod
    def from_manifest(cls, manifest: dict) -> "SessionState":
        """Reconstruct session from saved manifest."""
        session = cls(manifest["session_id"])
        session.phase = manifest.get("phase", "unknown")
        session.analyzed_files = manifest.get("analyzed_files", [])
        session.completed_tasks = manifest.get("completed_tasks", [])
        session.pending_tasks = manifest.get("pending_tasks", [])
        return session


# ─── Session resumption patterns ───────────────────────────────────────────────

def demonstrate_session_resumption():
    """
    Shows the two session resumption strategies:
    1. --resume <session-name>: when prior context is mostly valid
    2. Fresh session + injected summary: when prior tool results are stale
    """
    print("\n=== Session Resumption Strategies ===\n")

    print("STRATEGY 1: --resume with session name")
    print("  CLI: claude --resume codebase-investigation-v2")
    print("  Best when: prior context is mostly valid, continuing work from yesterday")
    print("  After resuming: inform session about any file changes:")
    print("    'auth.py was modified since our last session — re-analyze it'")
    print("    'The database schema changed: users table now has a role column'")
    print()

    print("STRATEGY 2: Fresh session with structured summary injection")
    print("  Best when: prior tool results are stale (files changed, APIs updated)")
    print("  Why: Resuming with stale tool results can mislead the model")
    print("  How: Summarize prior findings → start new session → inject summary as context")
    print()

    # Demonstrate the summary injection pattern
    stale_session = SessionState("investigation-2025-05-26")
    stale_session.phase = "analysis"
    stale_session.analyzed_files = ["auth.py", "orders.py", "payments.py"]
    stale_session.completed_tasks = ["Map codebase structure", "Identify entry points"]
    stale_session.pending_tasks = ["Analyze auth flow", "Check SQL injection risks"]
    stale_session.findings = [
        {"file": "auth.py", "issue": "Plaintext password comparison", "severity": "critical"},
        {"file": "orders.py", "issue": "N+1 query pattern in list_orders", "severity": "medium"},
    ]

    manifest = stale_session.to_manifest()
    print("Saved session manifest:")
    print(json.dumps(manifest, indent=2))

    # Create resumption prompt from manifest
    resumption_context = f"""
PREVIOUS SESSION CONTEXT (session: {manifest['session_id']})
Phase when interrupted: {manifest['phase']}
Files already analyzed: {', '.join(manifest['analyzed_files'])}
Completed tasks: {', '.join(manifest['completed_tasks'])}
Remaining tasks: {', '.join(manifest['pending_tasks'])}
Key findings from prior work:
{json.dumps(manifest['key_findings'], indent=2)}

NOTE: The files listed above may have changed since this session.
Before using any cached analysis, re-read the relevant files.

CURRENT TASK: Continue from where we left off. Start with the pending tasks.
"""
    print(f"\nResumption context to inject into new session (first 300 chars):")
    print(resumption_context[:300])


# ─── fork_session pattern ──────────────────────────────────────────────────────

def demonstrate_fork_session():
    """
    Shows fork_session for exploring divergent approaches from a shared baseline.

    fork_session creates independent branches so both can be explored
    without one polluting the other's context.
    """
    print("\n=== fork_session for Divergent Approach Exploration ===\n")

    shared_analysis = """
    After analyzing the legacy authentication system:
    - Current: session tokens in database, 1M+ rows
    - Pain points: slow lookups, no token refresh, security issues
    - Constraints: cannot break existing mobile apps, 2-week deadline
    """

    print("Shared baseline analysis:")
    print(shared_analysis)

    print("\nCreating two fork branches from this shared baseline...")
    print()
    print("FORK A: JWT migration approach")
    print("  fork_session('jwt-approach')")
    print("  Context: shared analysis + JWT exploration")
    print("  Explores: JWT implementation, token refresh, backward compat layer")
    print()
    print("FORK B: Redis-based session approach")
    print("  fork_session('redis-approach')")
    print("  Context: shared analysis + Redis exploration")
    print("  Explores: Redis setup, session replication, mobile app compatibility")
    print()

    # Simulate what each fork would explore
    fork_a_prompt = f"""
Based on this codebase analysis:
{shared_analysis}

Evaluate the JWT migration approach:
1. What changes are needed?
2. How long would this take?
3. What are the risks for mobile app compatibility?
Keep the answer brief (2-3 sentences per question).
"""

    fork_b_prompt = f"""
Based on this codebase analysis:
{shared_analysis}

Evaluate the Redis-based session approach:
1. What infrastructure is needed?
2. How long would this take?
3. What are the risks for mobile app compatibility?
Keep the answer brief (2-3 sentences per question).
"""

    print("Running fork A evaluation...")
    response_a = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": fork_a_prompt}],
    )
    print(f"Fork A (JWT): {response_a.content[0].text[:250]}...")

    print("\nRunning fork B evaluation...")
    response_b = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": fork_b_prompt}],
    )
    print(f"Fork B (Redis): {response_b.content[0].text[:250]}...")

    print("\nDeveloper can compare both and choose the winning approach.")
    print("Each fork's exploration stays isolated — no cross-contamination.")


# ─── File change notification pattern ─────────────────────────────────────────

def demonstrate_file_change_notification():
    """
    When resuming a session after code modifications, inform the agent
    about specific changed files rather than requiring full re-exploration.
    """
    print("\n=== Informing Resumed Session About File Changes ===\n")

    targeted_update = """
Session resumed. Since our last session, these files changed:
- auth.py: Password hashing now uses bcrypt (was SHA-256)
- config.py: DATABASE_URL moved to environment variables (was hardcoded)
- NEW FILE: middleware/rate_limit.py added

Please re-analyze ONLY these files and update your findings.
Do NOT re-analyze unchanged files (orders.py, payments.py, utils.py).
"""

    print("CORRECT: Targeted re-analysis of changed files only")
    print(targeted_update)

    print("\nWRONG: Asking agent to 'start over and re-analyze everything'")
    print("→ Wastes context on files that haven't changed")
    print("→ May get different results due to non-determinism")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 1.7: Session State, Resumption, and Forking")
    print("=" * 60)

    demonstrate_session_resumption()
    demonstrate_fork_session()
    demonstrate_file_change_notification()

    print("\n" + "=" * 60)
    print("CLI commands: claude --resume <name>")
    print("SDK concept: fork_session for divergent exploration")
    print("Key rule: stale tool results → fresh session + summary injection")


if __name__ == "__main__":
    main()
