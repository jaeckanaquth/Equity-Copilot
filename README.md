# Equity Copilot

Local equity research app: immutable snapshots, beliefs, questions, and structured review. Optional LLM (Ollama) for drafting and delta analysis only; you own the epistemology.

## Run

```bash
conda activate snow
uvicorn main:app --reload
```

Open [http://localhost:8000/weekly-review](http://localhost:8000/weekly-review).

## Main entry points

| Where | What |
|-------|------|
| `/weekly-review` | Open questions, beliefs needing review, all beliefs, orphans, structural proposals. |
| `/beliefs/new` | Add a belief (thesis or risk). |
| `/questions/new` | Add a question. |
| `/beliefs/{id}` | Belief detail: Option 1 (draft), Option 2 (delta analysis), **record review outcome**, snapshots, lifecycle events. |
| `/questions/{id}` | Question detail. |

## Where to add lifecycle (review outcome)

**Lifecycle** is recorded on the **belief detail** page when that belief has **newer snapshots** (i.e. it appears in “Beliefs Needing Review” on the weekly review).

1. Go to **Weekly Review** → open a belief under “Beliefs Needing Review”, or open any belief that has newer data.
2. On the **belief detail** page (`/beliefs/{id}`), use **Option 2** (Analyze Changes Since Last Review) if you want the delta summary first.
3. In the **“Record review outcome (optional)”** block, choose:
   - **Reinforced** — data aligns with the belief  
   - **Slight tension** — some friction; belief held with caveats  
   - **Strong tension** — material contradiction or pressure  
   - **Inconclusive** — not decisive yet  
4. Optionally add a short note, then click **Record outcome**.

The choice is stored as a **lifecycle event** on that belief and shown under “Lifecycle Events” on the same page. Belief health stays **human-judged**; the system does not auto-score.

- Full spec: [docs/REVIEW_OUTCOME_SPEC.md](docs/REVIEW_OUTCOME_SPEC.md)  
- Proposal lifecycle (accept/reject): [docs/PHASE_3_2_LIFECYCLE.md](docs/PHASE_3_2_LIFECYCLE.md)

## Docs

- [Adding beliefs and questions](docs/ADDING_BELIEFS_QUESTIONS.md) — UI and CLI  
- [Beliefs example (markdown format)](docs/BELIEFS_EXAMPLE.md) — template for drafting beliefs  
- [Data ingestion](docs/DATA_INGESTION.md) — import snapshots (Yahoo → StockSnapshot)  
- [Phase 3.2 Lifecycle](docs/PHASE_3_2_LIFECYCLE.md) — proposal states and engine  
- [Phase 3.3 LLM](docs/PHASE_3_3_LLM.md) — Ollama, drafting, Option 2 analysis  
