# Domain 3 Knowledge Check — Claude Code Configuration & Workflows (20%)

10 self-test questions. Answers at the bottom — don't peek!

---

**Q1.** A new developer joins your team and reports that Claude Code isn't following your team's Python coding standards. After investigation, you find the standards are defined in `~/.claude/CLAUDE.md` on the original author's machine. What is the correct fix?

A) Ask every new developer to copy the file manually to their `~/.claude/` directory  
B) Move the standards to a `CLAUDE.md` file in the project root and commit it to version control  
C) Add the standards to a `.claude/config.json` file with a `"shared": true` flag  
D) Store the standards in `~/.claude/commands/standards.md` and share it as a slash command  

---

**Q2.** Your project has test files spread throughout the codebase (e.g., `Button.test.tsx` next to `Button.tsx`, `api.test.ts` next to `api.ts`). You want Claude to automatically apply your team's test conventions whenever it works on any test file, regardless of location. What is the most maintainable solution?

A) Place a `CLAUDE.md` in each directory that contains test files  
B) Add test conventions to the root `CLAUDE.md` under a "Testing" section and rely on Claude to infer when they apply  
C) Create a `.claude/rules/tests.md` file with `paths: ["**/*.test.*", "**/*.spec.*"]` in the YAML frontmatter  
D) Create a skill in `.claude/skills/tests/` that developers invoke before writing tests  

---

**Q3.** You create a skill with `context: fork` in its `SKILL.md` frontmatter. What does this guarantee?

A) The skill runs faster by using a smaller model  
B) The skill's verbose output and intermediate context stay isolated in a sub-agent; only the final result returns to your main conversation  
C) The skill can only be invoked once per session  
D) The skill has read-only file access regardless of other settings  

---

**Q4.** A developer wants to run a detailed codebase analysis skill but doesn't want the intermediate file reads to consume their main session's context window. Which frontmatter option addresses this?

A) `allowed-tools: Read,Grep,Glob`  
B) `argument-hint: "path to analyze"`  
C) `context: fork`  
D) `description: runs in background`  

---

**Q5.** Which command runs Claude Code in non-interactive mode so it can be used in a CI/CD pipeline without hanging?

A) `claude --headless "review this PR"`  
B) `claude --batch "review this PR"`  
C) `claude -p "review this PR"`  
D) `claude --no-input "review this PR"`  

---

**Q6.** Your CI pipeline needs Claude Code to output review findings as machine-parseable JSON matching a specific schema, so the results can be automatically posted as inline PR comments. Which combination of flags achieves this?

A) `claude -p "..." --format json`  
B) `claude -p "..." --output-format json --json-schema schema.json`  
C) `claude -p "..." --structured-output schema.json`  
D) `claude -p "..." --json`  

---

**Q7.** You have a large `CLAUDE.md` covering React conventions, API conventions, database conventions, testing standards, and deployment procedures. It's become unwieldy. What is the recommended way to reorganize it?

A) Split it into multiple separate `CLAUDE.md` files in each relevant subdirectory  
B) Move all content into `~/.claude/CLAUDE.md` so it doesn't clutter the repo  
C) Use the `@import` syntax to reference topic-specific files in `.claude/rules/`, keeping the root `CLAUDE.md` as a concise index  
D) Create a single skill that loads all conventions when invoked  

---

**Q8.** A developer creates a personal variant of a shared skill so they can test modifications without affecting teammates. Where should they create it, and what should they name it to avoid conflict?

A) Overwrite the shared skill in `.claude/skills/` with their modifications  
B) Create `~/.claude/skills/my-<skillname>/SKILL.md` with a different name to avoid affecting the project version  
C) Fork the repository and modify the skill in their fork  
D) Add a `personal: true` flag to the shared SKILL.md frontmatter  

---

**Q9.** You want to use `@import` in your project's `CLAUDE.md` to load API-specific conventions only for files in `src/api/`. Which approach is more appropriate?

A) `@import` the API conventions in `CLAUDE.md` so they always load for every file  
B) Create a `.claude/rules/api.md` with `paths: ["src/api/**/*"]` — this loads the conventions automatically only when editing matching files, using fewer tokens than `@import` which always loads  
C) Create `src/api/CLAUDE.md` — the directory-level file is always better than path rules  
D) `@import` and path rules are interchangeable; choose either one  

---

**Q10.** After a developer runs `/memory` in Claude Code, they see only the user-level `CLAUDE.md` listed. They expected the project-level `CLAUDE.md` to also appear. What is the most likely cause?

A) Project-level `CLAUDE.md` requires a `--project-config` flag to activate  
B) The project-level `CLAUDE.md` exists but was placed in a subdirectory, not the repo root or `.claude/` directory  
C) Only one `CLAUDE.md` can be active at a time — the user-level takes precedence  
D) The `/memory` command only shows user-level files by design  

---

## Answers

1. **B** — User-level `~/.claude/CLAUDE.md` is personal and never shared via version control. Team-shared instructions must be in the project-level `CLAUDE.md` committed to the repo.

2. **C** — `.claude/rules/` with `paths: ["**/*.test.*"]` applies the rule to ALL test files regardless of directory location. A directory-level `CLAUDE.md` (A) can't handle scattered files. Root `CLAUDE.md` with inference (B) is unreliable. A skill (D) requires manual invocation.

3. **B** — `context: fork` runs the skill in an isolated sub-agent. All intermediate output (verbose file reads, search results) stays in the sub-agent's context window. Only the final summary returns to your main conversation, preserving your context budget.

4. **C** — `context: fork` is specifically designed to isolate verbose output from the main session. `allowed-tools` (A) restricts which tools can be used, not where output goes.

5. **C** — `-p` (or `--print`) is the documented non-interactive flag. The other options reference flags that don't exist.

6. **B** — `--output-format json` combined with `--json-schema schema.json` produces structured, schema-validated JSON output suitable for automated parsing.

7. **C** — `@import` in the root `CLAUDE.md` + topic-specific files in `.claude/rules/` (or separate markdown files) keeps the root file concise while keeping conventions modular and maintainable.

8. **B** — `~/.claude/skills/` is for personal skills that don't affect teammates. Using a different name avoids collision with the project's shared skill.

9. **B** — Path rules in `.claude/rules/` with `paths: ["src/api/**/*"]` load only when editing matching files, consuming tokens only when relevant. `@import` in root `CLAUDE.md` always loads regardless of which file you're editing.

10. **B** — Claude Code looks for `CLAUDE.md` at the repo root or inside `.claude/`. A file placed in an unexpected subdirectory won't be auto-discovered. Use `/memory` to diagnose; reposition the file to the project root.
