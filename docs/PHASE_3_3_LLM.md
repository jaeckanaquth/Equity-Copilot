# Phase 3.3 — LLM Assistive Layer

## Principle

> An LLM should never be structural glue.

The system is structurally complete without it. LLM output = suggestion artifact, not system artifact.
All outputs are ephemeral until explicitly copied by the user.

---

## Epistemic Boundary

Option 1 (Drafting) and Option 2 (Structural Change Analysis) have different risk levels.
They have: different entry points, different prompts, different attribution labels, different UI framing.

---

## Option 1 — Drafting Assistant (Safe Mode)

**Where:** Belief detail, Question detail

**Button:** `[Draft Refinement]`

**Prompt discipline:**
- Do not introduce new factual claims not present
- Do not assume unseen data
- Only rephrase or clarify
- Preserve epistemic tone ("may", "could") if present
- Do not strengthen certainty or imply observed evidence unless explicitly stated

**Attribution:** "LLM Draft Suggestion (Not Saved)"

**Endpoints:** `POST /api/llm/draft-belief-from-id`, `POST /api/llm/draft-question-from-id`

---

## Option 2 — Structural Change Analysis (Controlled Risk)

**Where:** Belief detail (only when belief has newer snapshots)

**Button:** `[Analyze Changes Since Last Review]`

**Input:** Belief text, previous snapshot metrics, new snapshot metrics, last review timestamp. *Restricted to snapshots referenced by the belief only — no other companies.*

**Output:** Structured JSON — delta_summary, potential_tensions, questions_raised. If no material change: "No material change detected." Empty arrays when appropriate.

**Attribution:** "LLM Structural Analysis — For Review Only"

**Endpoint:** `POST /api/llm/analyze-belief/{belief_id}`

---

## Explain Proposal (Lightweight)

**Where:** Proposals (weekly review, proposal history)

**Action:** "Explain" — why this structural proposal was triggered

**Attribution:** "LLM Structural Explanation"

---

## What the LLM Must Never Do

- Create beliefs automatically
- Accept/reject proposals automatically
- Modify snapshot references
- Generate lifecycle events without confirmation
- Merge beliefs

---

## What to Test

**Test matrix (Option 2 — Structural Change Analysis):**

| Scenario | Expectation |
|----------|-------------|
| Belief where metrics unchanged | "No material change detected." Clean empty arrays for tensions/questions. |
| Belief where revenue up, margins flat | Delta mentions revenue only. No invented margin tension. |
| Belief unrelated to metrics (qualitative thesis) | Calm summary. Empty arrays when no structural tension. No hallucinated numbers. |
| Single-company belief | Only that company's snapshots. No cross-ticker. |
| Multi-company belief | All referenced companies, scoped correctly. No contamination. |

**Success criteria (both Option 1 and 2):**
- No hallucinated numbers
- No cross-ticker contamination
- Clean empty arrays when appropriate
- Calm, literal tone — preserve epistemic hedging ("may", "could")
- No implied evidence unless explicitly in input

---

## Epistemic Contract & 8B Drift Patterns

**Observed drift with 8B local models (non-catastrophic, but directional):**

| Pattern | Example | Mitigation |
|---------|---------|------------|
| Certainty strengthening | "have experienced" vs "losing share" | Preserve epistemic tone; do not imply evidence |
| Scope drift | Time horizons ("3–5 years") not in original | Prompt: only rephrase, no expansion |
| Cross-company bleed | Reliance in TCS/INFY belief analysis | Restrict input to belief-referenced snapshots only |
| JSON looseness | List-like output instead of strict JSON | Over-specify: no code blocks, no commentary |

**Why discipline matters:** These drifts are subtle. The deterministic spine (proposals, lifecycle, references) stays intact. The LLM layer is assistive and non-mutating. But drift accumulates. Catching it immediately means the system is epistemically alive.

**Cognitive influence threshold:** After reading Option 2 output, does it change your belief confidence—even slightly? If yes, Option 2 is exerting cognitive influence. Not wrong. Just important. That is the threshold where the system transitions from workflow engine to cognitive co-pilot.

**When to dig deeper:** Stay with current implementation unless:

- Option 2 hallucinates numbers
- JSON fails frequently
- Tone inflation persists despite prompt guards
- You feel cognitive drift during real use
- You suspect the model is shaping beliefs (not just assisting)

Otherwise, move on. The deterministic spine carries the weight.

---

## Configuration

**Backend:** Ollama (free, local). Fits 8GB VRAM. Strong instruction following. Good JSON compliance.

1. Install [Ollama](https://ollama.com) and run `ollama serve`
2. Pull a model: `ollama pull llama3.1` (or run `ollama list` to see installed models)
3. No API key. No Python ML deps (torch/transformers).

Env vars:
- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `OLLAMA_MODEL` — default `llama3.1:latest` (use a model from `ollama list`)
