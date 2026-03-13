# Architecture — Structural Design

Purely technical. No philosophy. No marketing. **Status:** Implemented; reflects current closed slice.

---

## System Layers

```
Reality → Snapshot → Belief → Grounding → Review → Decision → Analytics
```

The system is temporal and log-structured. Time is a first-class dimension.

---

## Core Artifacts

| Artifact | Invariant |
|----------|-----------|
| **StockSnapshot** | Immutable. Deterministic ID. One company, one moment. |
| **ReasoningArtifact** | Immutable `claim.statement`. Thesis, risk, or question. |
| **BeliefLifecycleEvent** | Append-only. Payloads: `grounding_updated`, `review_outcome`, `decision`, `confidence`. |
| Decision event | Append-only; `event_kind: "decision"`. Type, rationale, linked snapshots, follow-up. |
| Confidence event | Append-only; `event_kind: "confidence"`. Level, rationale. |

No artifact is mutated by a later event. The log is canonical.

---

## Derived Projections

All computed from the lifecycle stream. Never stored as authoritative state.

| Projection | Source | Purpose |
|------------|--------|---------|
| Current decision state | Latest `event_kind: "decision"` per belief (by `occurred_at`) | “Where does this belief stand?” |
| Decision timeline | Ordered decision events per belief | Chronological story |
| Tension density | % of beliefs with current decision `slight_tension` or `strong_tension` | Systemic stress |
| Durability | Time from belief creation to first non-reinforced decision | Belief robustness |
| Trajectory pattern | Sequence of decision types per belief → stable / gradual_degradation / sudden_collapse / oscillatory | Pattern awareness |

If performance ever requires caching, the cache is read-only; the log remains canonical.

---

## Agents & Tools (Explicit Contracts)

Each agent/tool has a **contract** (inputs, outputs, side effects) and **guardrails** (what it must not do). No tool creates beliefs, records decisions, or mutates artifacts.

### Tool 1: Drafting Assistant

| Aspect | Contract |
|--------|----------|
| **Input** | `belief_id` (existing belief). |
| **Output** | Suggested refinement text only. Not saved. |
| **Side effects** | None. User may copy/paste; only user actions persist. |
| **Guardrails** | Must not create beliefs, record decisions, or write to artifact/lifecycle. Must not present output as stored fact. |

*Implementation:* `POST /api/llm/draft-belief-from-id`. Response is `{ text, attribution }`. No DB write.

### Tool 2: Proposal Explainer

| Aspect | Contract |
|--------|----------|
| **Input** | `proposal_type`, `belief_text`, `condition_state`, optional `proposal_id`. |
| **Output** | Explanation text only (why this proposal was generated). Not stored. |
| **Side effects** | None. For human review only. |
| **Guardrails** | Must not create beliefs, record decisions, or mutate artifacts. Must not accept/reject proposals; only explain. |

*Implementation:* `POST /api/llm/explain-proposal`. Response is `{ text }`. No DB write.

---

## LLM Role

- **Drafting** — Rephrase belief or question text; user approves or discards.
- **Structural analysis** — Delta since last review; tensions, questions raised; for review only.
- **Explanation** — Proposals, context; prepends concrete structural reason before LLM output.

LLM never:

- Creates beliefs automatically
- Records decisions automatically
- Mutates artifacts or lifecycle

---

## References

- [MASTER.md](MASTER.md) — Data model detail, repositories, API surface.
- [PHASE4_STRUCTURAL_POSITION.md](PHASE4_STRUCTURAL_POSITION.md) — Decision payload, `revised` semantics, analytics rules.
- [CHARTER.md](CHARTER.md) — Purpose, scope, technology constraints.
