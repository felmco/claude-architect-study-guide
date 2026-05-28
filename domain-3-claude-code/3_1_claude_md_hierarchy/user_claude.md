# Example: User-level CLAUDE.md (~/.claude/CLAUDE.md)

> **Exam Key:** This file is stored at ~/.claude/CLAUDE.md
> It is PERSONAL and NOT shared via version control.
> Instructions here apply to ALL projects for this user only.
> New team members will NOT receive these instructions.

## My Personal Preferences

- Always prefer type hints in Python
- Use `uv` instead of `pip` for package management
- My preferred diff format: unified (git diff style)
- I prefer verbose logging during debugging sessions

## Personal Tools Available

- GitHub CLI (`gh`) is installed and authenticated
- Docker is available for container testing

## When Working in This Project

- My personal GPG key is configured for commit signing
- I have write access to the main branch (be careful with force pushes)

---

**WHY THIS IS USER-LEVEL (Exam Scenario):**
If a new developer joins the team and these instructions were meant for everyone,
they would need to be moved to the PROJECT-LEVEL CLAUDE.md instead.

Diagnosis: "A new team member isn't receiving our coding standards instructions."
Root cause: Instructions in ~/.claude/CLAUDE.md (user-level) instead of project root CLAUDE.md
Fix: Move to <repo>/CLAUDE.md or <repo>/.claude/CLAUDE.md (committed to version control)
