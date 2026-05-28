# Domain 2 Knowledge Check — Tool Design & MCP Integration

---

**Q1.** A tool returns `{"isError": false, "found": false, "results": []}` when no matching orders exist. A colleague suggests changing this to `{"isError": true, ...}` since "no orders is an error." Which response is correct and why?

A) The colleague is right — any unexpected result should use `isError: true`  
B) The original is correct — a valid query with no results is NOT an error; `isError: true` should be reserved for access failures  
C) Use `isError: true` with `isRetryable: true` so the agent knows to try again  
D) Return an empty 200 response with no body  

---

**Q2.** Which tool_choice configuration guarantees that the model calls a tool but allows it to choose among several extraction schemas?

A) `{"type": "auto"}`  
B) `{"type": "any"}`  
C) `{"type": "tool", "name": "extract_invoice"}`  
D) `{"type": "none"}`  

---

**Q3.** Your team adds a new Jira MCP server for project management. A colleague suggests building a custom Jira MCP server. What is the better approach?

A) Always build custom MCP servers for full control  
B) Choose an existing community Jira MCP server; reserve custom servers for team-specific workflows not covered by existing servers  
C) Configure the Jira REST API directly as a tool (not an MCP server)  
D) Embed Jira credentials directly in the `.mcp.json` file  

---

**Q4.** A developer configured an MCP server in `~/.claude.json` globally. A new team member clones the repo but the MCP server is not available in their Claude Code session. What is the root cause?

A) The MCP server needs to be restarted after each clone  
B) The server was configured at user scope (`~/.claude.json`) rather than project scope (`.mcp.json` in the repo) — it is personal to the original developer  
C) MCP servers must be approved by a team lead before they become available  
D) The new developer needs to run `claude mcp sync` to pull remote configs  

---

**Q5.** You have an `analyze_document` tool and an `analyze_web_content` tool. Production logs show the model frequently uses `analyze_document` on web URLs and `analyze_web_content` on PDF files. What is the most likely cause?

A) The tools have identical or near-identical descriptions that don't differentiate their input types  
B) The model is choosing randomly between similar-named tools  
C) Tool selection depends on system prompt keywords, not tool descriptions  
D) Both A and C are equally likely causes  

---

## Answers

1. **B** — `isError: false` + `found: false` is a valid empty result. `isError: true` signals an access failure requiring a coordinator recovery decision. If a valid query simply finds no matching records, the system is working correctly — the coordinator should NOT retry.

2. **B** — `"any"` guarantees a tool call while letting the model choose which tool. `"auto"` might return text instead. Forced `"tool"` requires specifying a name. `"none"` prevents tool calls.

3. **B** — Choose existing community servers for standard integrations (GitHub, Jira, Slack). Custom servers are for team-specific workflows not covered by community options.

4. **B** — User-scope configs in `~/.claude.json` are personal and not shared via version control. For team-shared MCP servers, use project scope (`.mcp.json` committed to the repo).

5. **D** — Both causes apply: near-identical descriptions (A) is the primary cause; system prompt keywords (C) can create unintended tool associations as a secondary cause. The exam guide explicitly mentions both.
