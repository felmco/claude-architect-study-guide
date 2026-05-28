# Domain 5 Knowledge Check — Context Management & Reliability (15%)

10 self-test questions. Answers at the bottom.

---

**Q1.** During a long multi-turn customer support session, the agent begins referring to the customer's refund amount as "a few dollars" instead of the specific $127.50 that was established early in the conversation. What is the root cause and how do you fix it?

A) The model is hallucinating — use a more powerful model  
B) The specific dollar amount was buried in the middle of a long conversation and fell victim to the "lost in the middle" effect; extract transactional facts into a persistent case facts block included at the top of every prompt  
C) The session has exceeded the context window — reduce max_tokens  
D) Progressive summarization corrupted the value — stop summarizing and keep full history  

---

**Q2.** Your order lookup tool returns a 47-field JSON object, but your refund workflow only needs 6 of those fields. After 10 conversation turns, your context is nearly full. What is the most effective mitigation?

A) Increase `max_tokens` to allow a longer context  
B) Trim the tool result to only the 6 relevant fields before appending it to conversation history  
C) Ask the model to "remember" only important fields  
D) Store all tool results in a database and only retrieve them when needed  

---

**Q3.** A customer says: "I've been dealing with this for three weeks, your service is terrible, I just want this resolved!" The agent has a clear path to resolution (standard damaged-goods refund). What should the agent do?

A) Escalate immediately because of high negative sentiment  
B) Escalate because the customer has been waiting three weeks (long-running case)  
C) Acknowledge the frustration and proceed with resolution — the issue is within the agent's capability; escalate only if the customer reiterates their preference for a human  
D) Ask the customer if they'd prefer a human agent before attempting resolution  

---

**Q4.** A customer's account lookup returns two records for "Jane Smith." The agent must decide which account to use before looking up order details. What is the correct action?

A) Select the account with the most recent activity  
B) Select the account whose email domain matches the company the customer mentioned  
C) Ask the customer for an additional identifier (order number, email address, or phone number) to disambiguate  
D) Process both accounts and reconcile the results afterward  

---

**Q5.** A subagent fails to connect to an external API after 3 retry attempts. It has retrieved partial results (2 of 5 data points). Which response to the coordinator is correct?

A) Return `{"status": "error", "message": "API unavailable"}` — generic status  
B) Return empty results with `isError: false` so the coordinator knows to continue without this data  
C) Raise an exception that terminates the entire workflow  
D) Return structured error context including failure type, attempted query, partial results retrieved, and suggested alternative approaches  

---

**Q6.** Your research system synthesizes findings from multiple agents. After deployment, users complain that report citations are vague ("some sources suggest...") rather than specific. During investigation, you find that the summarization step strips source URLs and publication dates. What is the correct architectural fix?

A) Tell the summarization step "always include citations"  
B) Require subagents to return structured claim-source mappings (claim, source URL, publication date, evidence excerpt) and instruct all downstream agents to preserve these mappings — never convert them to prose summaries  
C) Run a separate citation-extraction pass after summarization  
D) Add a post-processing step that adds placeholder citations  

---

**Q7.** Two credible sources report conflicting AI adoption rates: Source A (2023 survey) says 40%, Source B (2023 market data) says 25%. During synthesis, what is the correct handling?

A) Average the two values and report 32.5%  
B) Use the higher value (40%) as it comes from a primary survey  
C) Use the lower value (25%) as it is more conservative  
D) Report both values with their source attribution and note the conflicting methodologies — let the reader or coordinator decide how to interpret the conflict  

---

**Q8.** After an extended codebase exploration session, the agent starts referencing "typical controller patterns" instead of the specific class names it identified earlier. What is the most likely cause and fix?

A) The agent's temperature is too high — lower it for codebase tasks  
B) The agent's context window filled with verbose file reads, causing context degradation — use a scratchpad file to persist key findings and inject it at the start of the next context window  
C) The model isn't powerful enough for large codebases — upgrade to a larger model  
D) The agent needs to be restarted fresh for each session  

---

**Q9.** Your document extraction system achieves 97% overall accuracy. A stakeholder proposes reducing human review for all documents above 90% model confidence. Before agreeing, what should you verify?

A) Nothing — 97% overall accuracy is sufficient evidence to proceed  
B) Verify that accuracy is consistently above 90% when segmented by document type AND by individual field, not just in aggregate — a high overall score can mask poor performance on specific segments  
C) Verify that the model's confidence scores are above 0.9 on average  
D) Verify that the system handles at least 1,000 documents before drawing conclusions  

---

**Q10.** Your multi-agent research system crashes mid-run after the web search agent completes but before the synthesis agent starts. When you restart, the web search agent runs again, duplicating API calls and delaying the report by 15 minutes. What architectural pattern prevents this?

A) Add retry logic to automatically restart failed agents from the beginning  
B) Implement structured state persistence: each agent exports its completed findings to a manifest file; on restart, the coordinator loads the manifest and injects each agent's prior output into its prompt, skipping already-completed work  
C) Increase the timeout so the workflow completes in a single run  
D) Use checkpointing by saving the full conversation history to disk after every turn  

---

## Answers

1. **B** — The "lost in the middle" effect causes models to miss content from the middle of long contexts. The fix is a case facts block: extract transactional values (amounts, dates, IDs) into a structured block placed at the TOP of every prompt, outside the summarized history.

2. **B** — Trimming verbose tool outputs before appending them to history is the correct approach. 47 fields accumulating across 10 turns consumes far more context than 6 fields × 10 turns.

3. **C** — Frustration and complaint duration are NOT escalation triggers. The issue is a standard damaged-goods refund — within the agent's capability. Acknowledge the frustration, resolve the issue. Escalate only if the customer explicitly re-requests a human.

4. **C** — When multiple customer records match, always ask for an additional identifier. Never heuristic-select (most recent activity, domain guessing) as this can lead to accessing the wrong account.

5. **D** — Structured error context with failure type, attempted query, partial results, and alternatives enables the coordinator to make an intelligent recovery decision. Generic status (A) hides context. Empty success (B) suppresses the error. Exception termination (C) ends the entire workflow unnecessarily.

6. **B** — Structured claim-source mappings that survive all downstream processing steps are the only reliable solution. Prompt instructions (A) don't prevent summarization from stripping metadata. Post-processing (C) can't reconstruct sources that were discarded.

7. **D** — Present both values with source attribution and note the methodological difference. The coordinator or synthesis agent decides how to reconcile. Never arbitrarily choose one value from conflicting credible sources.

8. **B** — Context degradation in extended sessions causes the agent to reference "typical patterns" instead of specific discovered facts. Scratchpad files persist key findings (specific class names, entry points) across context resets, and are injected back into the agent's context at the start of each new window.

9. **B** — Aggregate accuracy metrics mask segment failures. 97% overall could mean 100% on invoices but 60% on handwritten receipts. Verify accuracy by document type AND by individual field before reducing human review for any segment.

10. **B** — The structured manifest / crash recovery pattern: each agent exports its state to a known location on completion. The coordinator loads the manifest on resume and injects prior outputs into each agent's initial prompt, allowing the workflow to resume from the last completed step rather than restarting entirely.
