"""
Task Statement 2.5: Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob)

Key concepts:
- Grep: content search (searching file contents for patterns)
- Glob: file path pattern matching (finding files by name/extension)
- Read/Write: full file operations
- Edit: targeted modifications using unique text matching
- When Edit fails (non-unique anchor text): use Read + Write as fallback
- Incremental codebase understanding: Grep entry points → Read to follow imports

This file documents the selection logic and shows simulated examples.
In production Claude Code sessions, these are the actual built-in tools.
"""

import os
import re
import fnmatch
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# ─── Tool selection guide ──────────────────────────────────────────────────────

TOOL_SELECTION_GUIDE = """
Built-in Tool Selection Guide
==============================

GREP — Content search (searching INSIDE files)
  Use when: "find all places where function X is called"
            "locate error messages matching pattern Y"
            "find all imports of module Z"
            "search for string 'deprecated_api' across codebase"
  Examples:
    Grep(pattern="def login", path="src/")
    Grep(pattern="import anthropic", path=".", recursive=True)
    Grep(pattern="raise.*Error", path="src/handlers/")

GLOB — File path matching (finding FILES by name/pattern)
  Use when: "find all test files"
            "list all TypeScript files in src/"
            "find all Python files that match *_agent.py"
            "locate configuration files"
  Examples:
    Glob(pattern="**/*.test.tsx")
    Glob(pattern="**/test_*.py")
    Glob(pattern="domain-*/README.md")
    Glob(pattern="scenarios/*/agent.py")

READ — Load full file contents
  Use when: "read the contents of auth.py"
            "following an import chain discovered by Grep"
            "Edit failed and you need Read + Write instead"
  Examples:
    Read(path="src/auth.py")
    Read(path="domain-1/1_1_agentic_loop.py", offset=50, limit=100)

WRITE — Overwrite/create file
  Use when: "create a new file"
            "completely rewrite an existing file"
            "Edit failed due to non-unique anchor text (fallback)"
  Note: Always Read first before Write on existing files!

EDIT — Targeted modification using unique text matching
  Use when: "change a specific function" with unique surrounding context
             "add a line after a specific comment"
             "replace one specific code block"
  Limitation: Fails if the target text appears multiple times in the file
  Fallback: If Edit fails → Read the whole file + Write with modification

BASH — Shell commands
  Use when: running tests, installing packages, git operations,
            file operations that no dedicated tool handles
  Prefer dedicated tools (Read/Write/Grep/Glob) when they fit.
"""


# ─── Simulated tool operations ─────────────────────────────────────────────────

def simulated_grep(pattern: str, path: str, recursive: bool = True) -> list[dict]:
    """
    Simulate Grep: search file contents for a pattern.
    Returns matches with file, line number, and content.
    """
    results = []
    search_path = Path(path)

    if not search_path.exists():
        return [{"error": f"Path not found: {path}"}]

    glob_pattern = "**/*" if recursive else "*"
    for filepath in search_path.glob(glob_pattern):
        if filepath.is_file() and filepath.suffix in {".py", ".md", ".json", ".ts", ".tsx"}:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(pattern, line):
                        results.append({
                            "file": str(filepath),
                            "line": i,
                            "content": line.strip()[:100],
                        })
            except Exception:
                pass
    return results[:10]  # Limit for demo


def simulated_glob(pattern: str, base_path: str = ".") -> list[str]:
    """
    Simulate Glob: find files matching a path pattern.
    Returns list of matching file paths.
    """
    base = Path(base_path)
    if not base.exists():
        return []
    return [str(p) for p in base.glob(pattern)][:20]


def demonstrate_grep_vs_glob():
    """
    Shows when to use Grep vs Glob — a common exam confusion point.
    """
    print("=== Grep vs Glob Selection ===\n")

    # The repo root for demonstration
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("GLOB — Finding files by NAME PATTERN:")
    readme_files = simulated_glob("**/README.md", repo_root)
    print(f"  Glob('**/README.md') → {len(readme_files)} README files found")
    for f in readme_files[:3]:
        print(f"    {f}")

    python_files = simulated_glob("domain-1-agentic-architecture/*.py", repo_root)
    print(f"\n  Glob('domain-1-agentic-architecture/*.py') → {len(python_files)} Python files")
    for f in python_files[:3]:
        print(f"    {f}")

    print("\nGREP — Searching FILE CONTENTS for patterns:")
    stop_reason_hits = simulated_grep(r"stop_reason", os.path.join(repo_root, "domain-1-agentic-architecture"))
    print(f"  Grep('stop_reason', 'domain-1/') → {len(stop_reason_hits)} matches")
    for hit in stop_reason_hits[:3]:
        print(f"    {hit['file'].split('/')[-1]}:{hit['line']}: {hit['content']}")

    tool_use_hits = simulated_grep(r"tool_choice", os.path.join(repo_root, "domain-2-tool-design-mcp"))
    print(f"\n  Grep('tool_choice', 'domain-2/') → {len(tool_use_hits)} matches")
    for hit in tool_use_hits[:3]:
        print(f"    {hit['file'].split('/')[-1]}:{hit['line']}: {hit['content']}")


# ─── Incremental codebase understanding ───────────────────────────────────────

def demonstrate_incremental_understanding():
    """
    Correct pattern for understanding a large codebase:
    1. Grep for entry points
    2. Read to follow imports and trace flows
    NOT: Read all files upfront (wastes context)
    """
    print("\n=== Incremental Codebase Understanding Pattern ===\n")

    print("Step 1: Grep for entry points (e.g., main functions, route handlers)")
    print("  Grep(pattern='def main', path='.')")
    print("  Grep(pattern='@app.route', path='src/')")
    print()
    print("Step 2: Read the discovered entry point files")
    print("  Read(path='main.py')  # Follow the import trail")
    print()
    print("Step 3: Grep for imported modules")
    print("  Grep(pattern='from core', path='.')  # Find where 'core' is used")
    print()
    print("Step 4: Read specific functions discovered in step 3")
    print("  Read(path='core/claude.py', offset=1, limit=50)")
    print()
    print("DO NOT: Read all 200 files upfront — exhausts context window")
    print("DO: Build understanding incrementally, only read what's relevant")


# ─── Edit vs Read+Write fallback ──────────────────────────────────────────────

def demonstrate_edit_fallback():
    """
    Edit fails when the target text appears multiple times.
    Fallback: Read the entire file + Write with the modification.
    """
    print("\n=== Edit vs Read+Write Fallback ===\n")

    sample_code = """
def process_data(data):
    return data

def process_data_v2(data):
    return data  # same signature — Edit would fail here

class DataProcessor:
    def process_data(self):  # appears 3 times total
        return self.data
"""

    print("File content with repeated text (Edit would fail):")
    print(sample_code)

    print("Edit(old_string='return data', new_string='return data.strip()') → FAILS")
    print("  Reason: 'return data' appears 3 times — not unique")
    print()
    print("FALLBACK — Read + Write:")
    print("  1. Read(path='processor.py')  # Get full content")
    print("  2. Modify the specific occurrence in Python")
    print("  3. Write(path='processor.py', content=modified_content)")
    print()
    print("When to use Edit: target text is UNIQUE in the file (most cases)")
    print("When to use Read+Write: Edit fails due to non-unique anchor text")


# ─── Tracing function usage across wrapper modules ─────────────────────────────

def demonstrate_function_tracing():
    """
    Trace function usage across wrapper modules:
    1. Identify all exported names
    2. Search for each name across the codebase
    """
    print("\n=== Tracing Function Usage Across Modules ===\n")

    print("Goal: Find all callers of 'execute_tool'")
    print()
    print("Step 1: Grep for the function definition")
    print("  Grep(pattern='def execute_tool', path='.')")
    print("  → Found in: domain-1-agentic-architecture/1_1_agentic_loop.py")
    print()
    print("Step 2: Grep for all callers of the function")
    print("  Grep(pattern='execute_tool(', path='.')")
    print("  → Found in: 1_1_agentic_loop.py, 1_4_workflow_enforcement.py, ...")
    print()
    print("Step 3: Glob to find files that might re-export it")
    print("  Glob(pattern='**/tools.py')  # Find any tools module")
    print("  Grep(pattern='from.*execute_tool', path='.')  # Find re-exports")
    print()
    print("This incremental approach avoids reading unrelated files.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Task 2.5: Built-in Tools Selection Guide")
    print("=" * 60)
    print(TOOL_SELECTION_GUIDE)

    demonstrate_grep_vs_glob()
    demonstrate_incremental_understanding()
    demonstrate_edit_fallback()
    demonstrate_function_tracing()

    print("\n" + "=" * 60)
    print("Key rules:")
    print("  Grep = search INSIDE files (content)")
    print("  Glob = search FILE NAMES (paths)")
    print("  Edit fails → Read + Write (fallback)")
    print("  Build codebase understanding incrementally, not upfront")


if __name__ == "__main__":
    main()
