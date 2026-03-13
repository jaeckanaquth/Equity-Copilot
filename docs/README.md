# Equity Copilot — Documentation

Single entry point for all project documentation. Each file has one job. No duplication.

**Project status:** Complete for the current roadmap slice (Phases 1–4, 4.2, 4.3; portions A.1–A.3, B.1, C.1–C.2). Shop closed; docs are final.

---

## Purpose

Equity Copilot is a **log-structured reasoning system** for equity investing.

Its objective is:

> **Better long-term, risk-adjusted returns through improved reasoning discipline.**

The system does not predict markets or automate trades. It enforces structured thinking, explicit beliefs, structured review, and explicit outcomes. **Returns are a downstream consequence of disciplined reasoning. The system optimizes process, not outcomes.**

---

## Who It Is For

- Long-horizon equity investors
- Process-oriented thinkers
- Investors who want auditability of their reasoning

---

## What It Is Not

- Not a stock screener
- Not a trading bot
- Not an LLM investment advisor
- Not a belief-rewriting engine

---

## Documentation Index

### Core (position & guardrails)

| Document | Role |
|----------|------|
| [PHILOSOPHY.md](PHILOSOPHY.md) | Intent, problem, design philosophy, causal chain |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, artifacts, derived projections, LLM role |
| [INVARIANTS.md](INVARIANTS.md) | Non-negotiable constraints — the constitution |
| [ROADMAP.md](ROADMAP.md) | Phase-by-phase evolution plan |
| [CHARTER.md](CHARTER.md) | Operational scope, audience, technology, success criteria |
| [PHASE4_STRUCTURAL_POSITION.md](PHASE4_STRUCTURAL_POSITION.md) | Decision layer: what `revised` means, what we never do |

### Runbook & reference

| Document | Role |
|----------|------|
| [MASTER.md](MASTER.md) | Runbook, data model, commands, implemented vs spec'd — single compressed reference |

### Specs & runbooks (deep-dive)

| Document | Role |
|----------|------|
| [LIVE_FIRE.md](LIVE_FIRE.md) | End-to-end operation runbook |
| [PROPOSALS.md](PROPOSALS.md) | Proposal types, lifecycle, accept/reject behavior |
| [LLM_ASSIST.md](LLM_ASSIST.md) | Ollama, drafting, Option 2 analysis, explain proposal |
| [DATA_INGESTION.md](DATA_INGESTION.md) | Import snapshots (e.g. Yahoo → StockSnapshot) |
| [ADDING_BELIEFS_QUESTIONS.md](ADDING_BELIEFS_QUESTIONS.md) | UI and CLI for beliefs and questions |
| [BELIEFS_EXAMPLE.md](BELIEFS_EXAMPLE.md) | Template and format for drafting beliefs |
| [REVIEW_OUTCOME_SPEC.md](REVIEW_OUTCOME_SPEC.md) | Review outcome lifecycle payload and UI |
| [BELIEF_CONFIDENCE_SPEC.md](BELIEF_CONFIDENCE_SPEC.md) | Confidence lifecycle event (spec) |
| [REVIEW_CADENCE_SPEC.md](REVIEW_CADENCE_SPEC.md) | Review cadence table and API (spec) |
| [stock_snapshot_v_1.md](stock_snapshot_v_1.md) | StockSnapshot v1 schema and invariants |

### Reflection & intent

| Document | Role |
|----------|------|
| [SYSTEM_INTENT.md](SYSTEM_INTENT.md) | Reflective design memo: 5 Ws, 5 Hs, phase map, epistemic vs performance — narrative, not canonical doctrine |

---

Keep this file tight. It sets tone and is the single index.
