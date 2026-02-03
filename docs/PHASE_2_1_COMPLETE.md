# Phase 2.1 Complete — Derived Metrics Layer

## Status
**Phase 2.1 is complete and closed.**

This phase introduces the first post-snapshot computation layer in Equity Copilot.
All Phase 1 guarantees remain intact and enforced.

---

## Purpose of Phase 2.1

Phase 2.1 exists to answer one question only:

> What can be mechanically derived from immutable snapshots without introducing interpretation?

This phase deliberately limits scope to:
- deterministic math
- explicit provenance
- full recomputability

No opinions, judgments, or analytical conclusions are permitted.

---

## What Exists in Phase 2.1

### 1. DerivedMetricSet v1 (Data Contract)

A persisted, recomputable record describing:
- which snapshots were used
- what metrics were computed
- how they were computed
- when they were computed

Key properties:
- Read-only with respect to snapshots
- Fully traceable to snapshot IDs
- Safe to delete and regenerate

Schema location:
```bash
core/models/derived_metrics.py
```


---

### 2. Pure Computation Functions

Mechanical, deterministic math only.

Current metrics implemented:
- Revenue FY Year-over-Year Percent Change

Rules:
- No interpretation
- No rounding
- Null-safe
- Deterministic

Location:
```bash
core/derivations/compute.py
```

---

### 3. Deterministic Assembly Logic

Thin orchestration that:
- sorts snapshots by timestamp
- selects comparison pairs
- assembles a DerivedMetricSet

No intelligence or decision-making exists here.

Location:
```bash
core/derivations/assemble.py
```

---

### 4. Boundary-Enforcing Tests

Tests enforce:
- determinism
- null safety
- snapshot immutability
- schema discipline
- phase isolation

Phase 1 tests remain unchanged and continue to pass.

Locations:
```
tests/test_derived_metrics.py
tests/test_derivation_determinism.py
```

---

## Explicit Non-Goals (Enforced)

The following are **not allowed** in Phase 2.1:

- Valuation judgments
- Trend detection
- Scoring or rankings
- Labels such as “good”, “bad”, “strong”, “weak”
- Cross-company normalization
- Natural language analysis
- Agents or decision logic

Any of the above belongs to later phases.

---

## Relationship to Phase 1

- `StockSnapshot v1` remains immutable
- Snapshot creation is unchanged
- Phase 2.1 consumes snapshots strictly as inputs
- No snapshot fields are modified, enriched, or inferred upon

Phase 1 remains frozen and authoritative.

---

## Recomputability Guarantee

All Phase 2.1 outputs:
- can be deleted at any time
- can be recomputed solely from snapshots
- produce identical results for identical inputs

No historical knowledge is lost by deletion.

---

## Phase Exit Criteria (Satisfied)

- [x] One derived data object defined
- [x] One end-to-end metric implemented
- [x] Deterministic behavior enforced by tests
- [x] No interpretive leakage
- [x] Clean separation from Phase 1

---

## What Comes Next

Phase 2.2 will introduce **Analysis Views**, which allow structured interpretation
while still maintaining strict separation from factual records.

Phase 2.2 will begin with schema design only.

---

*Phase 2.1 is closed. No further changes should be made to this layer except
bug fixes or mechanical extensions following the same rules.*
