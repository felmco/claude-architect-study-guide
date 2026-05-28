# Domain 1 Knowledge Check — Agentic Architecture & Orchestration

Self-test questions beyond the 12 official sample questions. Answers at bottom.

---

**Q1.** Your agentic loop runs without error but occasionally returns an empty string instead of an answer. On inspection, `stop_reason` is `"end_turn"` but `response.content` has no text blocks — only a tool_use block. What is the most likely cause?

A) The model ran out of tokens before generating a response  
B) The loop is checking `stop_reason` correctly but not handling the case where the final response contains only tool_use blocks with no text  
C) The agentic loop should not terminate when `stop_reason == "end_turn"`  
D) Tool results were not appended to messages before the next API call  

---

**Q2.** A coordinator agent needs to research three subtopics simultaneously to reduce latency. How should the coordinator emit these parallel subagent requests?

A) Three separate API calls to Claude, one per subtopic  
B) Three Task tool calls in a single coordinator response turn  
C) One Task tool call with all three subtopics listed in the prompt  
D) A loop that calls each subagent sequentially, appending results before the next call  

---

**Q3.** You have a PostToolUse hook that normalizes Unix timestamps from tool results. The hook works correctly for `get_customer` but the model still sees raw timestamps from `lookup_order`. What is the most likely cause?

A) PostToolUse hooks only work on the first tool call in a turn  
B) The hook is registered only for `get_customer`, not for `lookup_order`  
C) The hook must be re-registered after each tool call  
D) PostToolUse hooks cannot modify numeric fields  

---

**Q4.** After completing codebase exploration, you want to try two different refactoring approaches without one polluting the other's context. Which mechanism is designed for this?

A) `--resume` with two different session names  
B) `fork_session` to create two independent branches from the shared exploration state  
C) Start two fresh sessions and manually inject the exploration summary into each  
D) Use the `Explore` subagent twice with different instructions  

---

**Q5.** A synthesis subagent receives search results and analysis results from prior agents. It needs to verify a specific statistic before including it. The statistic is a simple date. What is the correct pattern?

A) The synthesis subagent should stop and return control to the coordinator for verification  
B) The synthesis subagent should use its scoped `verify_fact` tool for this simple check  
C) The synthesis subagent should include the unverified statistic with a caveat  
D) The coordinator should have pre-verified all statistics before passing them to synthesis  

---

## Answers

1. **B** — When `stop_reason == "end_turn"`, always iterate `response.content` checking for `hasattr(block, "text")` — don't assume the first block is text.

2. **B** — Parallel spawning = multiple Task tool calls in a **single** coordinator response. Separate API calls (A) would be sequential coordinator turns. One Task call (C) doesn't parallelize. Sequential loop (D) eliminates the latency benefit.

3. **B** — Hooks are registered per tool name. A hook registered for `get_customer` does not automatically apply to `lookup_order`.

4. **B** — `fork_session` is the mechanism for creating divergent exploration branches from a shared baseline. `--resume` (A) resumes a prior named session, not a fork. Fresh sessions (C) lose the exploration state — you'd have to re-explore. Explore subagent (D) is for discovery, not branching approaches.

5. **B** — Simple fact checks (85% of verifications in Q9) should use the synthesis agent's scoped `verify_fact` tool to avoid coordinator round-trips. Complex verifications (15%) still route through the coordinator.
