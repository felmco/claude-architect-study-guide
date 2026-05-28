# Domain 1: Agentic Architecture & Orchestration (27%)

This domain covers the core patterns for building agents that autonomously execute multi-step tasks. It is the highest-weighted domain on the exam.

---

## Task Statements → Files

| Task | Description | File |
|------|-------------|------|
| 1.1 | Agentic loop lifecycle: stop_reason, tool execution, iteration | `1_1_agentic_loop.py` |
| 1.2 | Multi-agent coordinator-subagent patterns | `1_2_coordinator_subagent.py` |
| 1.3 | Subagent invocation, context passing, parallel spawning | `1_3_subagent_spawning.py` |
| 1.4 | Multi-step workflows with enforcement and handoff | `1_4_workflow_enforcement.py` |
| 1.5 | Agent SDK hooks for tool call interception | `1_5_hooks.py` |
| 1.6 | Task decomposition: chaining vs dynamic | `1_6_task_decomposition.py` |
| 1.7 | Session state, resumption, forking | `1_7_session_management.py` |

---

## Key Concepts

### The Agentic Loop
An agentic loop sends requests to Claude, inspects `stop_reason`, executes tools, appends results to conversation history, and continues until `stop_reason == "end_turn"`.

**Critical:** The loop terminates on `"end_turn"`, NOT on detecting text patterns in the response.

### stop_reason Values
| Value | Meaning | Action |
|-------|---------|--------|
| `"tool_use"` | Claude wants to call one or more tools | Execute the tools, append results, continue loop |
| `"end_turn"` | Claude has finished reasoning | Extract text response, terminate loop |
| `"max_tokens"` | Token limit reached | Handle gracefully (summarize/truncate) |

### Hub-and-Spoke Architecture
The coordinator is the only agent that communicates between subagents. No direct subagent-to-subagent communication. This provides:
- Observability (all traffic flows through one point)
- Consistent error handling
- Controlled information flow

### Subagent Context Isolation
Subagents do NOT automatically inherit the coordinator's conversation history. The coordinator must explicitly pass all required context in the subagent's prompt.

---

## Sequence Diagrams

### 1. Agentic Loop with stop_reason Branching

```mermaid
sequenceDiagram
    participant App
    participant Claude
    participant Tools

    App->>Claude: messages.create(tools=[...], messages=[...])
    
    loop Until stop_reason == "end_turn"
        Claude-->>App: response (stop_reason="tool_use")
        App->>App: Extract tool_use blocks from response
        App->>Tools: Execute each requested tool
        Tools-->>App: Tool results
        App->>App: Append assistant response to messages
        App->>App: Append tool_result blocks to messages
        App->>Claude: messages.create(..., messages=[...with results])
    end
    
    Claude-->>App: response (stop_reason="end_turn")
    App->>App: Extract text from response.content
```

### 2. Hub-and-Spoke Coordinator

```mermaid
sequenceDiagram
    participant User
    participant Coordinator
    participant SearchAgent
    participant AnalysisAgent
    participant SynthesisAgent

    User->>Coordinator: "Research topic X"
    Coordinator->>Coordinator: Decompose query into subtasks
    
    par Parallel subagent execution
        Coordinator->>SearchAgent: Task(prompt="Search for X, return {claim, source, date}")
        Coordinator->>AnalysisAgent: Task(prompt="Analyze docs about X")
    end
    
    SearchAgent-->>Coordinator: Structured findings + sources
    AnalysisAgent-->>Coordinator: Analysis results + partial errors
    
    Coordinator->>SynthesisAgent: Task(prompt="Synthesize: [search results] + [analysis]")
    SynthesisAgent-->>Coordinator: Draft report
    
    Coordinator->>Coordinator: Evaluate coverage gaps
    alt Gaps found
        Coordinator->>SearchAgent: Task(prompt="Targeted follow-up query for gap area")
        SearchAgent-->>Coordinator: Additional findings
        Coordinator->>SynthesisAgent: Task(prompt="Refine report with new findings")
        SynthesisAgent-->>Coordinator: Final report
    end
    
    Coordinator-->>User: Final comprehensive report
```

### 3. PostToolUse Hook Interception

```mermaid
sequenceDiagram
    participant Claude
    participant AgentSDK
    participant Hook
    participant Tool

    Claude->>AgentSDK: Tool call: process_refund(amount=750)
    AgentSDK->>Hook: PreToolUse hook check
    
    alt Amount > $500 (policy violation)
        Hook-->>AgentSDK: Block + redirect to escalation
        AgentSDK-->>Claude: Tool result: {isError: true, escalation_required: true}
        Claude->>AgentSDK: Tool call: escalate_to_human(reason="Refund exceeds $500 limit")
    else Amount <= $500
        Hook-->>AgentSDK: Allow
        AgentSDK->>Tool: Execute process_refund(amount=750)
        Tool-->>AgentSDK: Raw result {ts: 1748476800, status: 1}
        AgentSDK->>Hook: PostToolUse hook (normalization)
        Hook-->>AgentSDK: Normalized result {timestamp: "2025-05-28T12:00:00Z", status: "success"}
        AgentSDK-->>Claude: Normalized tool result
    end
```

### 4. Session Fork for Divergent Approaches

```mermaid
sequenceDiagram
    participant Dev
    participant MainSession
    participant ForkA
    participant ForkB

    Dev->>MainSession: Explore codebase, understand dependencies
    MainSession->>MainSession: Analyze architecture, identify refactor points
    
    Dev->>MainSession: fork_session("approach-a")
    Dev->>MainSession: fork_session("approach-b")
    
    MainSession-->>ForkA: Copy of session state
    MainSession-->>ForkB: Copy of session state
    
    par Explore divergent approaches
        Dev->>ForkA: "Implement microservices approach"
        ForkA->>ForkA: Plan and implement approach A
        ForkA-->>Dev: Results of approach A
    and
        Dev->>ForkB: "Implement modular monolith approach"
        ForkB->>ForkB: Plan and implement approach B
        ForkB-->>Dev: Results of approach B
    end
    
    Dev->>Dev: Compare approaches, choose winner
```

---

## Anti-Patterns to Avoid (Exam Traps)

| Anti-Pattern | Why It's Wrong | Correct Approach |
|-------------|----------------|-----------------|
| Check `response.content[0].text` contains "done" to end loop | LLM text is unreliable for control flow | Check `stop_reason == "end_turn"` |
| Set `max_iterations = 10` as primary stopping mechanism | Arbitrary cap causes silent failures | Use `stop_reason`, cap only as safety net |
| Parse natural language in tool results to detect errors | Fragile, language-dependent | Use structured `isError` flag |
| Subagent inherits coordinator context automatically | False — isolation is by design | Pass full context explicitly in subagent prompt |
| Use prompt-only for mandatory tool ordering | Non-zero failure rate | Use programmatic prerequisites |

---

## Exam Sample Questions Mapped Here

- **Q1** (Sample): Programmatic prerequisite vs prompt-only → `1_4_workflow_enforcement.py`
- **Q7** (Sample): Coordinator task decomposition too narrow → `1_2_coordinator_subagent.py`
- **Q8** (Sample): Structured error propagation → `1_3_subagent_spawning.py` + Domain 5
- **Q9** (Sample): Scoped verify_fact tool → `2_3_tool_distribution.py`
