# System Intent — Reflective Design Memo

**Reflective design memo, not canonical doctrine.** The 5 Ws, 5 Hs, phase map, and “hard question” below capture system intent and design narrative. Canonical positions live in [PHILOSOPHY.md](PHILOSOPHY.md), [CHARTER.md](CHARTER.md), [INVARIANTS.md](INVARIANTS.md), and [ROADMAP.md](ROADMAP.md). Use this doc for narrative and reflection.

---

# 5 Ws

## 1️⃣ Who is this for?

Primary user: a disciplined, long-horizon equity investor who wants:

* Explicit beliefs
* Explicit grounding
* Explicit review
* Explicit outcomes

Not for:

* High-frequency traders
* Passive index allocators
* People who want stock tips

This is for someone who wants to track how their thinking evolves. It is an epistemic instrument.

---

## 2️⃣ What is it?

It is **a log-structured reasoning engine for equity investing**.

Not:

* A stock screener
* A research aggregator
* A price prediction tool
* An LLM stock advisor

It tracks: immutable snapshots, immutable beliefs, structured grounding, structured review prompts, structured decisions, derived projections.

It answers:

> What did I believe, why, and how did reality respond?

---

## 3️⃣ When does it operate?

Across time layers: snapshot time (as_of), belief creation time, proposal generation time, decision time, review cadence time. The system is fundamentally temporal. Without time discipline, it collapses.

---

## 4️⃣ Where does it sit?

Between raw market data and capital allocation. It sits in the reasoning layer. Not execution, not brokerage, not portfolio accounting. It is upstream of money. That separation protects it from emotional mutation.

---

## 5️⃣ Why does it exist?

Because human memory lies. Investors routinely rewrite past beliefs, forget why they bought, rationalize outcomes, blur assumptions. This system exists to prevent narrative rewriting. It enforces immutable claims, immutable snapshots, append-only judgments. It is anti-self-deception software.

---

# 5 Hs (how it works structurally)

## 1️⃣ How are facts handled?

Via immutable `StockSnapshot`. Deterministic IDs, no mutation, all math derived from snapshot. Facts are fixed in time.

## 2️⃣ How are beliefs handled?

Via immutable `ReasoningArtifact`. Claim text never changes; no auto-rewrite; new belief = new artifact. Beliefs are statements, not states.

## 3️⃣ How are changes handled?

Through append-only lifecycle events: `grounding_updated`, `review_outcome`, `decision`, `confidence`. Nothing edits the past. Everything adds to the log.

## 4️⃣ How is uncertainty preserved?

By not collapsing decisions into single state, not auto-creating successor beliefs, not enforcing state machines, not auto-evaluating correctness. The system records judgment. It does not declare truth.

## 5️⃣ How does it stay coherent?

Through hard invariants: no mutation of snapshots or beliefs, no auto semantic generation, LLM assistive only, all projections derived. Every phase so far has preserved those invariants.

---

# Where You Are Now (Phase Map)

Phase 1 → Immutable reality  
Phase 2 → Separation of fact vs belief  
Phase 3 → Operational review discipline  
Phase 4 → Explicit decision recording  
Phase 4.2 → Derived decision projections  
Phase 4.3 → Analytics (pattern awareness)

You have completed the epistemic loop: Reality → Belief → Review → Decision → Pattern.

---

# The Hard Question

Are you still building:

> A system to improve reasoning?

Or drifting toward:

> A system to optimize investment performance?

Those are not identical goals. The moment performance enters, incentives distort. Right now, the system is about epistemic integrity. That’s rare, and powerful.

---

What is the ultimate success condition of this project? Not feature-wise. But philosophically.
