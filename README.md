# Equity Copilot

A **log-structured reasoning system** for equity investing.

**Project status:** Phase 4 and current roadmap slice (A.1–A.3, B.1, C.1–C.2) are complete. Documentation and runbooks are final; see [docs/README.md](docs/README.md).

**Goal:** Better long-term, risk-adjusted returns through improved reasoning discipline.

The system does not predict markets or optimize trades. It enforces structured thinking, explicit beliefs, structured review, and explicit outcomes. Returns are a downstream consequence of disciplined reasoning. The system optimizes process, not outcomes.

---

## Run

```bash
conda activate snow
uvicorn main:app --reload
```

Open [http://localhost:8000/weekly-review](http://localhost:8000/weekly-review).

---

## Entry points

| Where | What |
|-------|------|
| `/weekly-review` | Open questions, beliefs needing review, all beliefs, proposals. |
| `/beliefs/new` | Add a belief (thesis or risk). |
| `/beliefs/{id}` | Belief detail: draft, delta analysis, record outcome / decision, lifecycle. |
| `/questions/new`, `/questions/{id}` | Add or answer questions. |

---

## Documentation

**Index:** [docs/README.md](docs/README.md) — purpose, who it’s for, what it’s not, and full doc list.

**Core:** [PHILOSOPHY](docs/PHILOSOPHY.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [INVARIANTS](docs/INVARIANTS.md) · [ROADMAP](docs/ROADMAP.md) · [CHARTER](docs/CHARTER.md) · [PHASE4_STRUCTURAL_POSITION](docs/PHASE4_STRUCTURAL_POSITION.md)  
**Runbook:** [MASTER](docs/MASTER.md)  
**Specs:** [LIVE_FIRE](docs/LIVE_FIRE.md) · [PROPOSALS](docs/PROPOSALS.md) · [LLM_ASSIST](docs/LLM_ASSIST.md) · [DATA_INGESTION](docs/DATA_INGESTION.md) · [ADDING_BELIEFS_QUESTIONS](docs/ADDING_BELIEFS_QUESTIONS.md) · [BELIEFS_EXAMPLE](docs/BELIEFS_EXAMPLE.md) · [REVIEW_OUTCOME_SPEC](docs/REVIEW_OUTCOME_SPEC.md) · [BELIEF_CONFIDENCE_SPEC](docs/BELIEF_CONFIDENCE_SPEC.md) · [REVIEW_CADENCE_SPEC](docs/REVIEW_CADENCE_SPEC.md) · [stock_snapshot_v_1](docs/stock_snapshot_v_1.md)  
**Reflection:** [SYSTEM_INTENT](docs/SYSTEM_INTENT.md)
