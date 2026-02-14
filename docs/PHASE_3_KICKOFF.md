# Phase 3.1 — Kickoff: Uncertainty Preservation Layer

## Status
**Active – Scope Frozen**

This document defines the kickoff, scope, and non-negotiable boundaries of **Phase 3.1** of the Equity Copilot project.

Phase 3.1 is the first phase that introduces *assistance* on top of Phase 2 artifacts. It does so without introducing intelligence, synthesis, or automation.

---

## Purpose

Phase 3.1 exists to **prevent uncertainty from being forgotten**.

It provides structured, read-only visibility across existing artifacts so that the human user can:
- see what questions remain unanswered,
- notice when beliefs have not been revisited despite new facts,
- detect missing or weak grounding between beliefs and facts,
- maintain epistemic hygiene over time.

Phase 3.1 does **not** think, decide, summarize, or guide.

---

## Core Principle

> Phase 3.1 surfaces structure, not meaning.

It reveals *what exists*, *how it is connected*, and *when it last changed*—and nothing more.

---

## Canonical Interaction Surface

- **Primary surface:** Local Web UI
- **Cadence:** Weekly review

The UI is the canonical expression of Phase 3.1 behavior. Any secondary interfaces must conform to the same contracts and invariants.

---

## Hard Invariants (Non‑Negotiable)

Phase 3.1 MUST:
- be strictly read-only
- operate only on Phase 1 and Phase 2 artifacts
- preserve full provenance and attribution
- reflect *current upstream state* at query time

Phase 3.1 MUST NEVER:
- mutate facts, metrics, views, beliefs, or lifecycle events
- create, update, or retire beliefs or questions
- summarize or synthesize in natural language
- rank, score, label, or recommend
- imply correctness, validity, or action

---

## Updated Referrals Rule (Project-Critical)

Every surfaced element in Phase 3.1 **must always be traceable to the latest relevant upstream artifacts**.

This implies:
- no cached conclusions
- no stale references
- no implicit context

All referrals must be:
- live
- inspectable
- expandable to exact artifact IDs

Failure to uphold updated referrals compromises the project.

---

## Phase 3.1 Query Primitives (Frozen Set)

Only the following primitives are in scope.

### Q6 — Unanswered Question Registry (Primary)

**Purpose**
Expose unresolved uncertainty so it cannot silently disappear.

**Returns**
- Question-type ReasoningArtifacts
- Associated company (if any)
- Age since creation
- Related beliefs (if linked)

**UI Characteristics**
- Grouped by company
- Sorted by oldest first
- No auto-resolution
- No merging or deduplication

---

### Q3 — Belief Review Staleness

**Purpose**
Reveal beliefs that have not been revisited since newer facts appeared.

**Returns**
- Belief ID
- Last lifecycle event timestamp
- Newer snapshot timestamps

**Constraints**
- Temporal comparison only
- No judgment about belief quality

---

### Q1 — Belief → Snapshot Coverage

**Purpose**
Make factual grounding (or lack thereof) explicit.

**Returns**
- Belief ID
- Referenced snapshot IDs
- Snapshot timestamps
- Explicit gaps

**UI Rule**
This query must be visible whenever a belief is viewed in detail.

---

### Q7 — Orphaned Artifacts

**Purpose**
Maintain epistemic hygiene.

**Returns**
- Beliefs without snapshots
- Snapshots without downstream use
- AnalysisViews never referenced

**Constraints**
- No prioritization
- No dismissal

---

## Noise Policy

- Light grouping is allowed (by company, belief, or age)
- No aggregation by importance or severity
- No default collapsing that hides artifacts

---

## Explicit Non‑Goals (Phase 3.1)

Phase 3.1 does not include:
- summaries or highlights
- "what changed" narratives
- answers to questions
- proposal generation
- agents or automation

All of the above are deferred to later Phase 3 sub‑phases.

---

## Phase Boundary

This document freezes Phase 3.1.

Any system that:
- proposes new artifacts,
- synthesizes meaning,
- or assists decision-making

belongs to **Phase 3.2 or later** and must not back‑propagate into this phase.

---

## Summary

Phase 3.1 is deliberately quiet.

Its success is measured by one outcome:

> Uncertainty remains visible until a human explicitly resolves it.

If Phase 3.1 ever feels helpful, persuasive, or smart—it has already failed.

