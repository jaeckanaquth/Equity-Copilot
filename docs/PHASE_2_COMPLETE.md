# Phase 2 — Epistemic Scaffolding

## Status
**Phase 2 is complete.**

Phase 2 defines all layers that sit *on top of immutable facts* and *below agents or automation*.
Its purpose is to make later intelligence possible **without corrupting truth, history, or belief**.

---

## What Phase 2 Is

Phase 2 is not “analysis”.

Phase 2 is **epistemic scaffolding** — the set of layers that answer:

- What can be computed from facts?
- How can facts be interpreted without belief?
- How can belief be recorded without pretending it is truth?
- How do beliefs change over time?
- How can the system reflect on itself without reasoning for the user?

Only after these questions are answered is it safe to introduce agents.

---

## Phase 2 Design Principles

All sub-phases adhere to the following principles:

- **Strict separation of concerns**
- **Append-only history**
- **Explicit assumptions**
- **No hidden inference**
- **Auditability over convenience**
- **Local-first and individual-first**

Phase 2 deliberately avoids:
- prediction
- recommendation
- automation
- optimization

---

## Phase 2 Overview

Phase 2 consists of **five conceptual sub-phases**:
```bash
2.1 → Derivation
2.2 → Interpretation
2.3 → Belief
2.4 → Time
2.5 → Introspection
```

Each sub-phase answers a different epistemic question and introduces exactly one new capability.

---

## Phase 2.1 — Derivation (Math)

### Question Answered
> What can be computed mechanically from immutable facts?

### Core Object
**DerivedMetricSet v1**

### Characteristics
- Deterministic
- Fully recomputable
- No interpretation
- No labels or judgments
- Safe to delete and regenerate

### Examples
- Revenue YoY percent change
- Balance sheet ratios
- Simple deltas and proportions

### What Is Explicitly Not Allowed
- Scoring
- Trend labeling
- “Good / bad” classification
- Cross-entity normalization

**Phase 2.1 produces math, not meaning.**

---

## Phase 2.2 — Interpretation (Views)

### Question Answered
> How can facts be examined without asserting belief?

### Core Object
**AnalysisView v1**

### Characteristics
- Structured interpretive lenses
- Explicit assumptions and exclusions
- Bounded outputs
- Safely discardable
- No persistence of belief

### Designed View Types
- `valuation_multiple`
- `financial_health_lens`
- `growth_consistency_lens`

### Implemented Builder
- `valuation_multiple` (single concrete implementation)

### What Is Explicitly Not Allowed
- Recommendations
- Scores
- Rankings
- Forecasts
- Natural-language conclusions

**Phase 2.2 allows interpretation, but forbids belief.**

---

## Phase 2.3 — Belief (Reasoning)

### Question Answered
> How can belief be recorded without pretending it is true?

### Core Object
**ReasoningArtifact v1**

### Supported Artifact Types
- `thesis` — directional belief
- `risk` — structural vulnerability
- `question` — unresolved uncertainty

### Characteristics
- Explicit stance (where applicable)
- Plain-language claims
- Visible assumptions and counterpoints
- Epistemic confidence (not probability)
- Reviewable and revisable

### What Is Explicitly Not Allowed
- Silent belief updates
- Belief masquerading as fact
- Automated correctness judgments

**Phase 2.3 is the first layer where the system is allowed to be wrong.**

---

## Phase 2.4 — Time (Lifecycle)

### Question Answered
> What happens to beliefs after they exist?

### Core Object
**BeliefLifecycleEvent v1**

### Belief States
- `active`
- `under_review`
- `superseded`
- `invalidated`
- `retired`

### Characteristics
- Append-only
- Orthogonal to belief content
- Supersession is first-class
- No rewriting history

### What Is Explicitly Not Allowed
- Deleting beliefs
- Editing past beliefs
- Auto-invalidation
- Scoring belief quality

**Phase 2.4 ensures beliefs evolve without disappearing.**

---

## Phase 2.5 — Introspection (Reflection)

### Question Answered
> How does the system read itself without reasoning for the user?

### Core Concept
**Read-only introspection queries**

### Query Families
- Belief timelines
- Supersession graphs
- Active belief inventory
- Assumption frequency surfacing
- Unresolved uncertainty tracking

### Characteristics
- Read-only
- No synthesis
- No recommendations
- No new stored objects

### What Phase 2.5 Does Not Introduce
- New schemas
- New beliefs
- Any form of intelligence

**Phase 2.5 provides visibility, not guidance.**

---

## What Phase 2 Explicitly Avoids

Across all sub-phases, Phase 2 avoids:

- Trading logic
- Portfolio optimization
- Agent autonomy
- Forecasting
- Scoring or ranking
- “Smart” summaries

These are deferred to Phase 3 — and only after Phase 2 exists.

---

## Phase 2 in One Table

| Layer | Purpose | Can Be Wrong | Mutable |
|----|----|----|----|
| StockSnapshot (P1) | Facts | ❌ | ❌ |
| DerivedMetricSet | Math | ❌ | ✅ |
| AnalysisView | Interpretation | ❌ | ✅ |
| ReasoningArtifact | Belief | ✅ | ✅ |
| BeliefLifecycleEvent | Time | ❌ | ❌ |
| Introspection Queries | Reflection | ❌ | ❌ |

---

## Why Phase 2 Matters

Without Phase 2:
- Agents hallucinate authority
- Beliefs leak into facts
- History gets rewritten
- Confidence replaces truth

With Phase 2:
- Truth is anchored
- Belief is explicit
- Disagreement is preserved
- Mistakes are learnable

Phase 2 is what makes later intelligence **safe**.

---

## Phase 2 Status

✅ All Phase 2 sub-phases are complete  
✅ All boundaries are enforced structurally  
✅ No agents or automation introduced  
✅ System is audit-ready  

---

## What Comes Next

Phase 3 will build **on top of Phase 2**, not through it.

Two possible directions:

- **Phase 3A — Agentic Systems**
- **Phase 3B — Human-First Interfaces**

Phase 2 guarantees that either path remains honest.

---

*Phase 2 is complete. No further changes should be made to this phase except
bug fixes or schema corrections. All new capability must be introduced in
subsequent phases.*