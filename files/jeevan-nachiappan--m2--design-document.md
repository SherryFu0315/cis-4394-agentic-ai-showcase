# ScopeGuard — Milestone II: Multi-Agent Workflow Design Document

**CIS4394 · Multi-Agent AI System**
**Milestone II — Multi-Agent Workflow (5%)**

---

## 1. System Architecture Overview

ScopeGuard uses a **fixed sequential pipeline** with a **Critic-driven revision loop** as its coordination mechanism. Four specialized agents process user input in order, with the Critic agent acting as a quality gate that can trigger re-evaluation when outputs fail clarity thresholds.

**Pipeline flow:**

User Input → Agent 1 (Intake) → Agent 2 (Scope Cutter) → Agent 3 (Feasibility) → Agent 4 (Critic) → MVP Scope Contract

If the Critic rejects the outputs (clarity score below 70 or critical issues detected), the pipeline loops back to Agent 2 (Scope Cutter) for a second pass. A maximum of 2 revision loops prevents infinite cycling.

**Why sequential over orchestrated:** MVP scoping is inherently a layered process — you cannot assess feasibility without first knowing the feature set, and you cannot critique outputs that don't exist yet. A sequential pipeline reflects how real product discussions unfold. The Critic's revision loop adds the iterative refinement that a purely linear pipeline lacks.

---

## 2. Agent Specifications

### Agent 1: Intake & Clarifier

**Role:** Task Decomposer — transforms unstructured user input into a structured, analyzable format.

**Input format:**
```json
{
    "project_name": "StudyBuddy",
    "description": "An app that helps students find study partners...",
    "features": ["User profiles", "Chat", "Calendar integration"],
    "timeline": "4 weeks",
    "team_size": "2"
}
```

**Output format:**
```json
{
    "project_brief": {
        "project_name": "StudyBuddy",
        "team_size": "2 developers",
        "timeline": "4 weeks",
        "proposed_features": ["User profiles", "Chat", "Calendar integration"]
    },
    "assumptions": [
        "Assumes 2 developers working part-time (~15 hrs/week).",
        "No existing codebase or infrastructure in place.",
        "User authentication is implied but not listed."
    ],
    "ambiguities": [
        "\"Chat\" needs a clearer definition — real-time or async?",
        "Calendar integration scope unclear — read-only or create events?"
    ]
}
```

**Behavior:** This agent runs exactly once per pipeline execution. It does not participate in revision loops because the raw user input does not change. Its primary value is surfacing the gap between what the user *said* and what they *meant* — hidden assumptions and vague requirements that would otherwise cause problems downstream.

---

### Agent 2: Scope Cutter (Product Perspective)

**Role:** Domain Expert — applies product management judgment to reduce the feature set to the minimum viable set.

**Input:** The structured brief from Agent 1, including surfaced assumptions and ambiguities.

**Output format:**
```json
{
    "in_scope": ["User profiles", "Course listing"],
    "out_scope": [
        {"feature": "Chat messaging", "reason": "Adds 20+ hours of complexity for a non-core feature"}
    ],
    "rationale": "Given 4 weeks with 2 developers, the MVP should focus on...",
    "scope_reduction_ratio": 0.5
}
```

**Behavior:** The Scope Cutter is the primary target of revision loops. When the Critic identifies issues (e.g., a kept feature is too vague, or the rationale is weak), the Scope Cutter receives the Critic's feedback implicitly through re-evaluation of the same inputs, potentially producing different cuts on a second pass.

**Key constraint:** Must keep at least 1 feature and defer at least 1 (unless only 1 feature was submitted). The `scope_reduction_ratio` directly feeds into the evaluation metrics.

---

### Agent 3: Feasibility Analyst (Engineering Perspective)

**Role:** Technical Evaluator — assesses implementation complexity of in-scope features.

**Input:** The Scope Cutter's output (in-scope feature list) plus the original project constraints from Agent 1.

**Output format:**
```json
{
    "assessments": [
        {
            "feature": "User profiles",
            "tier": "Medium",
            "estimate": "8-12 hours",
            "risks": "Profile image upload adds storage complexity"
        }
    ],
    "hidden_challenges": [
        "State management across features needs architectural planning",
        "Testing typically consumes 30-40% of estimated dev time"
    ],
    "recommended_stack": "React frontend + Flask backend. SQLite for MVP persistence."
}
```

**Behavior:** Evaluates only the features that survived the Scope Cutter. Complexity tiers range from Low to High and are calibrated for student developers (10-15 hours/week). The "hidden challenges" field is designed to catch integration risks that individual feature assessments miss.

---

### Agent 4: Critic & Quality Verifier

**Role:** Verifier / Quality Gate — reviews all prior agent outputs for clarity, consistency, and actionability.

**Input:** The complete outputs of all three prior agents.

**Output format:**
```json
{
    "clarity_score": 82,
    "issues": [
        "\"User profiles\" lacks a measurable definition of done.",
        "Time estimates may be optimistic for a 2-person team."
    ],
    "revision_requested": false,
    "revision_reason": null,
    "recommendation": "Define a measurable DoD for each MVP feature before starting."
}
```

**Behavior:** The Critic is the only agent that can trigger a revision loop. The decision logic is:
- If `clarity_score < 70` → revision requested (quality too low)
- If critical issues found (vague features, contradictions, missing success criteria) → revision requested
- If this is already revision attempt 2+ → more lenient on minor issues, only flags critical problems
- Maximum 2 revision loops to prevent infinite cycling

**Stopping conditions:**
1. Critic approves (clarity_score ≥ 70 and no critical issues)
2. Maximum revision loops reached (currently set to 2)

---

## 3. Communication Protocol

All agents communicate through **structured JSON objects** passed sequentially through the pipeline. There is no shared memory or message bus — each agent receives the output of its predecessor(s) as function arguments.

**Data flow:**

```
UserInput ──→ IntakeAgent.run(user_input) ──→ IntakeOutput
                                                   │
IntakeOutput ──→ ScopeCutterAgent.run(intake) ──→ ScopeCutterOutput
                                                        │
IntakeOutput + ScopeCutterOutput ──→ FeasibilityAgent.run(scope, intake) ──→ FeasibilityOutput
                                                                                    │
All three outputs ──→ CriticAgent.run(intake, scope, feasibility, revision_count) ──→ CriticOutput
```

The Critic receives all prior outputs so it can check for contradictions across agents (e.g., Scope Cutter keeps a feature the Feasibility Agent flags as High complexity with no mitigation).

**Revision context:** When a revision loop occurs, the Critic's revision count is passed to subsequent agents. On revision attempt 2, the Critic's system prompt instructs it to be more lenient on minor issues while still catching critical problems. This prevents the system from ping-ponging between "too strict" and "still not good enough."

---

## 4. Failure Handling

### LLM Response Failures

**Invalid JSON:** Each agent call uses a `call_gemini_json()` helper that includes retry logic. If the first LLM response isn't valid JSON (e.g., includes markdown fences or preamble text), the helper:
1. Strips common formatting artifacts (```json fences)
2. Attempts JSON parsing
3. If parsing fails, sends a correction prompt asking the model to output only valid JSON
4. If the retry also fails, raises an exception caught by the Flask API

**API errors:** Network failures or Gemini API errors are caught at the Flask route level and returned as structured error responses (`{"success": false, "error": "..."}`). The frontend displays these gracefully rather than crashing.

### Low-Quality Agent Outputs

**Vague or unhelpful outputs:** The Critic agent is specifically designed to catch this. Its clarity scoring rubric evaluates whether outputs are specific enough to act on. Scores below 70 trigger a revision loop.

**Overly aggressive scope cutting:** If the Scope Cutter removes all features except one trivial item, the Critic should flag this as an issue (the MVP doesn't demonstrate enough value). The revision loop gives the Scope Cutter a chance to recalibrate.

**Contradictions between agents:** The Critic reviews all outputs simultaneously and can identify when, for example, the Scope Cutter keeps a feature that the Feasibility Agent rates as "High" complexity with significant risks. The Critic flags this as an issue.

### Infinite Loop Prevention

The `MAX_REVISION_LOOPS` constant (default: 2) hard-caps the number of times the Critic can send outputs back for revision. After 2 loops, the pipeline proceeds with whatever outputs exist, even if the Critic isn't fully satisfied. This ensures the system always terminates.

### Frontend Resilience

If the Flask backend is unreachable (e.g., during development when only the frontend is running), the React frontend falls back to mock data responses. A "Mock Mode" badge indicates to the user that they're seeing simulated outputs rather than real agent analysis.

---

## 5. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Backend | Google Gemini 1.5 Flash | Powers all 4 agents via structured prompting |
| Agent Framework | Custom Python (dataclasses) | Lightweight; no heavy framework needed for a 4-agent pipeline |
| API Server | Flask + Flask-CORS | REST API connecting frontend to pipeline |
| Frontend | React (JSX, Hooks) | User interface for input and results display |
| Data Format | JSON throughout | Consistent structured communication between all layers |

---

## 6. Evaluation Metrics (Carried from Proposal)

The multi-agent pipeline enables three quantitative metrics:

1. **Scope Reduction Ratio** — measures proportion of features deferred. Directly output by the Scope Cutter agent.
2. **Clarity Pass Rate** — percentage of MVP features with measurable "Definition of Done." Assessed by the Critic agent.
3. **Critic Rejection Rate** — how often the Critic triggers revision loops. Tracked via `revision_count` in the pipeline result.

These metrics will be compared between a single-agent baseline and the full multi-agent system in Milestone III.
