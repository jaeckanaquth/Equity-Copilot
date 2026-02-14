# LLM Assist — What It Does and What It Doesn’t

The LLM layer is **assistive only**. The system is structurally complete without it. LLM output is a **suggestion artifact**, not a system artifact; nothing is saved until the user explicitly copies or applies it.

---

## Features

### 1. Drafting assistant (safe mode)

**Where:** Belief detail, Question detail  
**Action:** `[Draft Refinement]`

- Rephrases or clarifies existing text.
- Does not introduce new factual claims or assume unseen data.
- Preserves epistemic tone (“may”, “could”) when present.
- **Attribution:** “LLM Draft Suggestion (Not Saved)”

**Endpoints:** `POST /api/llm/draft-belief-from-id`, `POST /api/llm/draft-question-from-id`

### 2. Structural change analysis (controlled risk)

**Where:** Belief detail, only when the belief has newer snapshots  
**Action:** `[Analyze Changes Since Last Review]`

- **Input:** Belief text, previous snapshot metrics, new snapshot metrics, last review timestamp. Restricted to snapshots referenced by the belief (no other companies).
- **Output:** Structured JSON: `delta_summary`, `potential_tensions`, `questions_raised`. If no material change: “No material change detected.” Empty arrays when appropriate.
- **Attribution:** “LLM Structural Analysis — For Review Only”

**Endpoint:** `POST /api/llm/analyze-belief/{belief_id}`

### 3. Explain proposal

**Where:** Proposals (weekly review, proposal history)  
**Action:** “Explain” — why this structural proposal was triggered  
**Attribution:** “LLM Structural Explanation”

---

## What the LLM Must Never Do

- Create beliefs automatically
- Accept or reject proposals automatically
- Modify snapshot references
- Generate lifecycle events without confirmation
- Merge beliefs

---

## Configuration

**Backend:** Ollama (local). No API key; no Python ML deps (torch/transformers).

1. Install [Ollama](https://ollama.com) and run `ollama serve`
2. Pull a model: `ollama pull llama3.1` (or run `ollama list` for installed models)

**Env vars:**

- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `OLLAMA_MODEL` — default `llama3.1:latest` (use a model from `ollama list`)

---

## Testing and Guardrails

- **Drafting:** No new facts, no strengthened certainty, no implied evidence; preserve hedging.
- **Structural analysis:** No hallucinated numbers; no cross-ticker data; only belief-referenced snapshots; calm, literal tone; empty arrays when there is no material change.
- **JSON:** Prompts over-specify format (no code blocks, no extra commentary) to keep output parseable.

If the model starts to shape beliefs rather than assist (e.g. tone inflation, invented numbers, cognitive drift in use), treat that as the threshold to tighten prompts or revisit the feature. The deterministic spine (proposals, lifecycle, references) carries the weight; the LLM stays non-mutating.
