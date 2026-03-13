# Roadmap — Evolution Plan

Phase-by-phase outline. This file changes over time. The invariants file should not.

---

## Phase 1 – Immutable Snapshot Layer

- StockSnapshot model and storage
- Deterministic IDs (ticker + period)
- Import from external source (e.g. Yahoo); no mutation of existing snapshots

---

## Phase 2 – Fact / Belief Separation

- ReasoningArtifact (thesis, risk, question)
- References to snapshots (grounding)
- Clear separation: facts vs beliefs

---

## Phase 3 – Operational Review Discipline

- Proposals (review_prompt, missing_grounding)
- Accept / Reject flows
- Grounding update and `grounding_updated` lifecycle event
- Review outcome recording (`review_outcome` event)
- Staleness and “beliefs needing review” derived from data

---

## Phase 4 – Decision Layer

- Append-only decision events (`event_kind: "decision"`)
- Decision types: reinforced, slight_tension, strong_tension, revised, abandoned, confidence ↑/↓, deferred, other
- API: record decision, list decisions
- No mutation of belief text; no auto-creation of beliefs from decisions

---

## Phase 4.2 – Derived Decision State

- Current decision state (projection)
- Decision timeline (projection)
- Reports: beliefs by current decision, decision summary

---

## Phase 4.3 – Process Analytics

- Durability (time to first non-reinforced decision)
- Tension density (% under slight/strong tension)
- Trajectory patterns (stable, gradual_degradation, sudden_collapse, oscillatory)
- Descriptive only; never stored; no quality scoring or prediction

---

## Phase 5 – Performance Observation Layer

- Read-only, decoupled
- Observe returns / risk in relation to beliefs and decisions
- Does not drive automatic behavior; does not mutate reasoning layer

---

## Phase 6 – Process–Performance Correlation (Careful Boundary)

- Optional: link reasoning discipline metrics to outcomes
- Requires explicit design so performance never becomes the driver of semantic or structural change
- **Correlation analysis must never trigger automatic semantic or structural mutation.**
- Invariants remain non-negotiable

---

## Next Steps — Portion by Portion

All three directions (process depth, performance observability, agent sophistication) in small slices. B stays minimal.

### A) Process depth (first)

| Portion | What | Spec / ref |
|---------|------|------------|
| **A.1** | Review cadence — table, POST/DELETE cadence API, “Due for review (cadence)” on weekly review, set/clear on belief detail | [REVIEW_CADENCE_SPEC.md](REVIEW_CADENCE_SPEC.md) |
| **A.2** | Belief confidence — `confidence` lifecycle event, POST confidence API, current confidence on belief detail | [BELIEF_CONFIDENCE_SPEC.md](BELIEF_CONFIDENCE_SPEC.md) |
| **A.3** | Decision follow-up — when recording a decision, optional “set cadence” (creates/updates cadence row); no other auto-mutation | Phase 4 structural position |

### B) Performance observability (minimal)

| Portion | What | Constraint |
|---------|------|------------|
| **B.1** | One read-only view or export — e.g. “Observed outcomes” page or CSV export of beliefs + decisions + optional placeholder for returns. No writes. No automatic behavior. | Phase 5: read-only, decoupled. Does not mutate reasoning layer. |

### C) Agent sophistication (after A and B)

| Portion | What | Constraint |
|---------|------|------------|
| **C.1** | One agent or tool — define contract (inputs, outputs), implement, document guardrails (no belief creation, no decision recording, no artifact mutation) in ARCHITECTURE or INVARIANTS | LLM assistive only; extend only with explicit “what this agent must not do” |
| **C.2** | Next agent/tool — same pattern | — |

**Current slice status:** A.1–A.3, B.1, C.1–C.2 are implemented. Project closed for this slice.

**Order:** A.1 → A.2 → A.3 → B.1 (minimal) → C.1 → C.2 …  
After each portion: run live fire or smoke test; update MASTER “implemented” if needed.
