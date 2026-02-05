# Phase 2.3 Complete — Reasoning / Thesis Layer

## Status
**Phase 2.3 is complete and closed.**

This phase introduces explicit belief, uncertainty, and disagreement into
Equity Copilot while preserving strict separation from facts, derivations,
and interpretive views.

---

## Purpose of Phase 2.3

Phase 2.3 exists to answer:

> How can belief be recorded, revised, and audited without rewriting history
> or contaminating factual truth?

This phase introduces **ReasoningArtifact**, a first-class representation of
human (or system) judgment under uncertainty.

Beliefs are allowed to be wrong in this layer — and that wrongness is preserved.

---

## What Exists in Phase 2.3

### 1. ReasoningArtifact v1 (Data Contract)

`ReasoningArtifact` is a schema-only construct representing:

- explicit beliefs, risks, or unresolved questions
- grounded in snapshots, metrics, and views
- attributable to an author
- time-bound and reviewable

Key properties:
- Never treated as fact
- Never recomputed automatically
- Never silently updated
- Designed to age and be challenged

Schema location:
```bash
core/models/reasoning_artifact.py
```

---

### 2. Supported Artifact Types

Phase 2.3 defines three orthogonal artifact types:

#### `thesis`
- A directional belief or position
- Explicit stance (bullish / bearish / neutral)
- Backed by reasoning, assumptions, and counterpoints

#### `risk`
- Identification of structural vulnerability
- No directional stance
- Focused on exposure, not prediction

#### `question`
- Explicit acknowledgement of unresolved uncertainty
- No belief or direction
- Designed to guide further investigation

All three share a common schema and differ only by intent and semantics.

---

### 3. Explicit Reasoning Structure

Each ReasoningArtifact contains:

- **Claim**
  - Plain-language statement of belief, risk, or uncertainty
- **Rationale**
  - Why this artifact exists
- **Assumptions**
  - What must be true for the reasoning to hold
- **Counterpoints**
  - Known weaknesses or alternative interpretations
- **Confidence**
  - Epistemic confidence, not probability
- **Review**
  - When and why the artifact should be revisited

This structure prevents hindsight rewriting and overconfidence.

---

## Explicit Non-Goals (Enforced)

Phase 2.3 does **not** allow:

- automated decisions or actions
- trading recommendations
- probabilistic forecasting
- belief masquerading as fact
- silent belief updates
- retroactive justification

Beliefs are recorded, not enforced.

---

## Relationship to Earlier Phases

- Phase 1 (`StockSnapshot v1`): immutable factual record
- Phase 2.1 (`DerivedMetricSet`): mechanical, recomputable math
- Phase 2.2 (`AnalysisView`): structured interpretation without belief
- Phase 2.3 (`ReasoningArtifact`): explicit belief and uncertainty

Deleting all ReasoningArtifacts leaves facts, metrics, and views intact.

---

## Auditability & Historical Integrity

ReasoningArtifacts are:

- time-stamped
- author-attributed
- explicitly scoped
- preserved even when invalidated

This ensures that:
- past beliefs remain visible
- mistakes are learnable
- decisions can be reconstructed honestly

---

## Phase Exit Criteria (Satisfied)

- [x] Belief is explicitly represented
- [x] Uncertainty is first-class
- [x] Disagreement is allowed and recorded
- [x] Review and revision are structural
- [x] No computation or inference leaked in

---

## What Comes Next

Phase 2.4 will introduce **temporal evolution mechanics**, including:

- belief review workflows
- supersession and invalidation
- thesis drift over time
- longitudinal reasoning analysis

Phase 2.4 will not introduce new belief types, only lifecycle mechanics.

---

*Phase 2.3 is closed. No further changes should be made to this layer except
schema corrections or lifecycle extensions introduced in later phases.*
