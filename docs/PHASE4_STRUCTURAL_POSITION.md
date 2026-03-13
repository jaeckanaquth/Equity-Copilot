# Phase 4 — Final Structural Position

**Purpose:** Lock the epistemic invariants of the decision layer so they do not drift. This document is the single source of truth for what Phase 4 is and is not allowed to do.

---

## 1. What `revised` Means

**Definition:**

> “The original belief no longer reflects my thinking.”

**It is a historical marker only.**

It does **not** mean:

- Create a new belief automatically
- Edit belief text
- Replace the old claim
- Transition belief state in a workflow

Recording `revised` appends a decision event. The original belief artifact and its `claim.statement` remain unchanged. The timeline tells the story; no state mutation is required.

---

## 2. Architectural Invariants

### 2.1 Beliefs remain immutable

- `ReasoningArtifact.claim.statement` **never** changes after creation.
- Even when “revised” or “abandoned” is recorded, the original belief remains intact.
- The system preserves what the human believed at the time of creation.

That is intellectual honesty.

### 2.2 Decisions remain append-only

- New rows in `belief_lifecycle_events` with `event_kind: "decision"`.
- No updates or deletes to existing decision events.
- A belief’s history may look like:

  ```
  2026-01-10 — Reinforced
  2026-03-01 — Slight tension
  2026-05-20 — Revised
  ```

No state mutation required. The log is the source of truth.

### 2.3 No state machine

We deliberately **do not** model beliefs as:

```
Active → Under Tension → Abandoned
```

Beliefs are not workflow tickets. Instead we have:

- A **historical decision log** (append-only)
- A **derived current projection** (computed from the log, not stored)
- **No enforced exclusivity** between decision types over time

That keeps nuance intact and avoids collapsing uncertainty into a single “state”.

### 2.4 Snapshots remain immutable

- StockSnapshot rows are never updated or deleted by the decision or lifecycle layer.
- Snapshot attachment (grounding) changes only via the existing “Accept & Attach” flow, which appends a `grounding_updated` event and updates belief references in the one allowed way. Decision recording does not touch snapshots.

---

## 3. When the Analyst Wants a New Belief

If the analyst’s thinking has changed and they want a new statement of belief:

1. They **explicitly create a new belief** (UI or CLI).
2. They may **optionally reference the old belief** in rationale or notes (in the new belief or in a decision event).
3. They may **record a decision** on the old belief: `revised` or `abandoned`.

**Intentional cognition only. No inference by the system.**

The system does not:

- Auto-create a new belief when “revised” is recorded
- Copy or rewrite the old belief text into a new artifact
- Link beliefs automatically based on decisions

---

## 4. Why This Is the Correct Move

Systems that auto-rewrite beliefs based on decisions slowly become **narrative engines**, not **epistemic systems**.

Once the system starts creating or editing beliefs from decision labels, you blur:

- What the human thought  
- vs  
- What the system inferred  

That is where auditability quietly dies.

Phase 4 avoids that by keeping:

- Beliefs immutable
- Decisions append-only and human-recorded
- “Current state” as a derived view only

---

## 5. Current Architecture Summary

| Layer            | Invariant                          |
|------------------|------------------------------------|
| Snapshots        | Immutable                          |
| Beliefs          | Immutable (`claim.statement` fixed)|
| Lifecycle events | Append-only                        |
| Decisions        | Append-only (lifecycle, `event_kind: "decision"`) |
| Current state    | Derived (projection from log)      |

This is a **log-structured reasoning system**. The log is canonical; projections are views.

---

## 6. Out of Scope for Phase 4 (Do Not Add Without Explicit Design)

- **Automatic creation of beliefs** from a “revised” or any other decision.
- **Editing or replacing** `ReasoningArtifact.claim.statement` based on decisions.
- **State machine or workflow states** (e.g. active / under_review / abandoned) that override or replace the decision log.
- **Automatic inference** of belief relationships or “successor” beliefs from decision labels.

---

## 7. Future Directions (After Phase 4)

### Option A — Decision analytics layer ✅ Implemented (Phase 4.3)

- Trend analysis: reinforcement rate over time, abandonment ratio, tension clustering, belief durability.
- Deepens introspection without changing the above invariants.
- Remains read-only projections over the same log.
- **Never store derived metrics in DB.** If performance demands it, use a read-only cache/materialized view; the log remains canonical.

### Option B — Portfolio interaction layer

- Link decisions to position sizing, capital allocation, risk flags.
- Powerful but introduces real-world consequences; requires explicit product and risk design.
- Must not compromise belief immutability or decision append-only semantics.

---

## 8. References

- [MASTER.md](MASTER.md) — runbook and high-level reference
- [REVIEW_OUTCOME_SPEC.md](REVIEW_OUTCOME_SPEC.md) — review outcome lifecycle
- Decision API and derived state: Phase 4.1 (record decision, list decisions), Phase 4.2 (current decision state, timeline, reports), Phase 4.3 (analytics: durability, tension-density, trajectories)

---

## 9. Phase 4.3 — Decision Analytics (Descriptive Only)

Analytics endpoints are **descriptive, not judgmental**. They do not:

- Score belief quality
- Rank or evaluate the analyst
- Predict returns or infer correctness

They answer:

- **Decision distribution** — Counts by type over time (`GET /api/reports/decision-summary?since=...`).
- **Belief durability** — Time from creation to first non-reinforced decision; median, mean, distribution (`GET /api/reports/durability`).
- **Tension density** — % of beliefs currently under slight or strong tension (`GET /api/reports/tension-density`).
- **Trajectory patterns** — Per-belief sequence classified as stable / gradual_degradation / sudden_collapse / oscillatory; labels are **derived only, never persisted** (`GET /api/reports/trajectories`).

All metrics are recomputed from the lifecycle log. No `belief.durability_score` or similar stored field. If we ever add a materialized view for performance, it is cache only — never canonical.

---

*Document establishes the final structural position for Phase 4. When in doubt, preserve epistemic integrity: no mutation of belief text, no auto-creation of beliefs from decisions, append-only lifecycle and decisions, derived views only.*
