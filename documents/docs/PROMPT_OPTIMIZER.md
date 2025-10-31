# 🎯 The Core Problem This Solves

A ReAct agent's performance is **extremely sensitive** to its system prompt. The agent's entire "thought" process—how it plans, which tools it chooses, and how it handles errors—is dictated by this initial instruction.

The problem: writing and refining this prompt is a manual, time-consuming, and guess-and-check process.

---

## Traditional Workflow (painful)

1. A developer writes a _v1_ prompt.  
2. They run the agent on a test task.  
3. The agent fails (gets stuck in a loop, uses the wrong tool, misses a step).  
4. The developer manually reads messy Thought/Action/Observation logs and **guesses** what went wrong.  
5. The developer tweaks the prompt (e.g., “You must use the search tool first”) and hopes it fixes things.  
6. Repeat.

This is slow, unscientific, and doesn’t scale.

---

# Solution Overview — “Simulate-Refine” Loop

The refactored code automates the entire guess-and-check loop. It uses a powerful Foundation Model (FM) as an “expert prompt engineer” to analyze agent failures and systematically improve the prompt.

At a high level:

- Use a **simulation** of the target agent to cheaply produce a trace of how the agent would think.
- Send that trace + original prompt + task context to an **optimizer FM** which critiques and rewrites the prompt.
- Iterate.

---

## ⚙️ How It Works: Step-by-step

### 1. The “Test Drive” (Simulation)  
**Function:** `_simulate_react_agent_thinking`  
**Purpose:** See how a "standard" agent (e.g., `qwen3:latest`) reasons when given the current prompt.  
**Process:**
- Perform a **dry run** of the agent for *N* steps (default: 5).
- **Do not** actually call external tools (like `search_the_web`). Instead, simulate tool usage by returning plausible “Simulated tool result” entries. This keeps runs fast and cheap.
- Capture the agent’s internal monologue: Thought → Action → Observation steps.  

**Output:** `simulation_trace` (string) — a log file of the agent’s thinking process.

> Example snippet of a simulation trace (conceptual):
```text
Thought: I'll search for latest cancer biomarkers.
Action: CALL_TOOL(search_the_web, "cancer biomarkers 2024")
Observation: [SIMULATED] search returned 3 results...
Thought: Now I'll synthesize...
```

### 2. The “Expert Review” (Refinement)

**Function:** `_get_refinement`  
**Purpose:** Analyze `simulation_trace`, identify flaws, and produce an improved prompt.  

#### Process
- Bundle three items:
  1. **Original Prompt** — the prompt under test  
  2. **Task Context** — the test data or scenario (e.g., "cancer research")  
  3. **Simulation Trace** — the captured reasoning log  

- Send all three to a powerful optimizer model (e.g., `gemini-1.5-pro`) using a designed `OPTIMIZER_SYSTEM_PROMPT`.

- The optimizer FM acts as a **world-class prompt engineer** with explicit instructions:
  - “Analyze this trace.”  
  - “Critique the original prompt.”  
  - “Rewrite an improved prompt that addresses the identified flaws.”  

#### Output
A JSON object containing structured feedback and the improved prompt:

```json
{
  "feedback": "List of critiques and suggestions",
  "optimized_prompt": "The rewritten system prompt"
}
```

### 3. The Iteration (The Loop)

**Function:** `optimize` (main orchestrator)

#### Workflow
1. Start with prompt `v1`.  
2. `simulate(v1)` → `trace_v1`.  
3. `refine(v1, trace_v1)` → `v2` (`optimized_prompt`).  
4. `simulate(v2)` → `trace_v2`.  
5. `refine(v2, trace_v2)` → `v3`.  
6. Repeat until `MAX_OPTIMIZATION_ITERATIONS` or convergence.

Each iteration produces progressively more robust and logically sound prompts.

---

## 💡 Why This Approach Is Powerful

- **Automates tedious human work:** Replaces slow manual tuning with a fast, programmatic loop.  
- **Turns the black box into a glass box:** Captures the agent’s internal reasoning and feeds it to a stronger model that can understand and fix it.  
- **Uses the right tool for the job:**  
  - Use the *target model* (e.g., `qwen3`) to **simulate** how the agent will behave under the current prompt.  
  - Use a *powerful optimizer FM* (e.g., `gemini-1.5-pro`) to handle complex critique and creative rewriting.  
- **Data-driven refinement:** Changes to the prompt are grounded in observed failures from the simulation trace — a form of **offline reinforcement learning** for prompts.

---

## ⚙️ Implementation Notes & Best Practices

- **Simulated tools** must return realistic, constrained outputs so the simulation resembles the real agent’s downstream reasoning.  
- **Optimizer meta-prompt** should instruct the FM to:
  - Identify specific failure modes (loops, hallucinations, wrong tool choice).  
  - Propose minimal, targeted changes (avoid over-rewrites).  
  - Output JSON with `feedback` and `optimized_prompt`.  
- **Safety & guardrails:**  
  - Keep instructions for tool usage, privacy, and rate limits explicit in the system prompt.  
  - Avoid unsafe or unintended tool execution.  
- **Convergence criteria:** Stop when:
  - No meaningful changes are suggested, **or**  
  - Simulation traces show stable, desired behavior, **or**  
  - `MAX_OPTIMIZATION_ITERATIONS` reached.  

---

## 🧩 Example (Conceptual) Flow

```text
react_researcher_v1 → simulate → trace_v1  
_get_refinement(react_researcher_v1, cancer_research_context, trace_v1) → returns react_researcher_v2 + feedback  
simulate react_researcher_v2 → trace_v2  
refine again → react_researcher_v3  
output best prompt + audit trail of feedback and traces  
```

### Quick Checklist for adoption

- Provide representative task contexts for testing (diverse scenarios).
- Tune simulation length (5 steps is a good default).
- Choose an optimizer FM that excels at reasoning & instruction-writing
- Validate final prompt with real tool-enabled runs (not simulated) before production.
- Keep logs of traces and feedback for auditability.

