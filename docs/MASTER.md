# Equity Copilot — Master Reference

Single compressed reference for the system. Use this to start Phase 4; deep-dive specs remain in `docs/` for implementation detail.

---

## 1. Charter (compressed)

- **Purpose:** Log-structured reasoning system for equity investing. Goal: better long-term, risk-adjusted returns through improved reasoning discipline.
- **Principles:** Individual-first, local-first, agentic (narrow agents + orchestrator), decision support not replacement, reproducible (clone and run). Facts immutable; beliefs immutable; lifecycle append-only.
- **In scope:** Stock snapshots, financial analysis, quarter-over-quarter change, thesis/risk management, decision logs, agentic architecture.
- **Out of scope:** Automated trading, price prediction, high-frequency logic, mandatory paid data, black-box reasoning, belief-rewriting.
- **Tech:** Free/open tooling, local LLMs (Ollama), SQLite/simple storage, no hard dependency on proprietary APIs.

Full charter: [docs/CHARTER.md](CHARTER.md).

---

## 2. Run & entry points

```bash
conda activate snow
uvicorn main:app --reload
```

| Where | What |
|-------|------|
| `/weekly-review` | Open questions, beliefs needing review, all beliefs, **due for review (cadence)**, orphans, structural proposals. Runs proposal engine on load. |
| `/create` | Combined form: Add belief or Add question. |
| `/beliefs/new` | Add belief (thesis or risk). |
| `/questions/new` | Add question. |
| `/beliefs/{id}` | Belief detail: Draft refinement, Analyze changes since last review, **Record review outcome**, **Set confidence**, **Review cadence**, **Record decision**, referenced snapshots (Ticker \| As of \| Grounded), decision timeline, lifecycle events. |
| `/questions/{id}` | Question detail, answer. |
| `/proposals/history` | All proposals by type and status (audit). |

**Lifecycle (review outcome):** On belief detail when the belief has newer snapshots: choose Reinforced / Slight tension / Strong tension / Inconclusive + optional note → Record outcome. Stored as lifecycle event; no auto-scoring.

---

## 3. Data model (compressed)

- **StockSnapshot:** Immutable, one company + one moment. Metadata (snapshot_id, as_of), company (ticker, etc.), market_state, financials, balance_sheet. Deterministic snapshot_id from ticker+period; same ticker+quarter → skip on import.
- **ReasoningArtifact:** thesis, risk, or question. Has `claim.statement`, `references.snapshot_ids`. Beliefs = thesis + risk.
- **Proposal:** proposal_id, proposal_type (`review_prompt` \| `missing_grounding`), status (pending \| accepted \| rejected \| expired), payload (belief_id, belief_text, newer_snapshot_ids for review_prompt, condition_state). No deletion; TTL 30 days.
- **Lifecycle events:** `belief_lifecycle_events` table. Payloads: `review_outcome` (outcome, note), `grounding_updated` (attached_snapshot_ids), **`decision`** (type, rationale, linked_snapshot_ids, follow_up, …), **`confidence`** (confidence_level, rationale). Append-only.

---

## 4. Data ingestion

- **Rule:** Produces StockSnapshot only. Never auto-creates beliefs/proposals/LLM. Snapshots immutable (ticker+quarter exists → skip).
- **Script:** `scripts/import_snapshots.py`. Source: Yahoo (yfinance). Fetches quarterly income → maps to StockSnapshot.
- **Commands:**  
  `python scripts/import_snapshots.py` (default MSFT, AMZN, JPM; 8 quarters)  
  `python scripts/import_snapshots.py --clear` (wipe then import)  
  `python scripts/import_snapshots.py AAPL GOOGL -q 4`  
- **List snapshots:** `python scripts/add_artifact.py list-snapshots`

---

## 5. Beliefs & questions

- **Add belief (UI):** Weekly Review → Add belief, or `/beliefs/new`. Statement, “Treat as risk”, select snapshots.
- **Add question (UI):** Add question, statement, select snapshots. Frame mechanism-driven, snapshot-connected, structurally reviewable (see framing below).
- **CLI:**  
  `python scripts/add_artifact.py belief "Statement." [--snapshots ID1 ID2] [--risk]`  
  `python scripts/add_artifact.py question "Question?" [--snapshots ID]`  
- **Seed (8 beliefs):** `python scripts/seed_beliefs.py` — hardcoded MSFT/AMZN/JPM theses and risks + comparative; each linked to all snapshots for its ticker(s).
- **Framing questions:** Mechanism-driven (leading indicators, not one-off predictions); snapshot-connected; structurally reviewable. Prefer “What would signal X?” over “What is next week’s prediction?”

---

## 6. Live fire runbook (compressed)

1. **Import:** `python scripts/import_snapshots.py` (optionally `--clear`, custom tickers, `-q N`).
2. **Beliefs:** `python scripts/seed_beliefs.py` or add via UI/CLI. Target ~7–8 (2–3 per company, 1–2 comparative).
3. **Run app:** `uvicorn main:app --reload` → open `/weekly-review`. See open questions, beliefs needing review (days since last grounded snapshot), orphans, structural proposals.
4. **Proposals:** Accept (for review_prompt: “Accept & Attach Latest Data” — attaches newest snapshot per ticker, appends grounding_updated event, redirect with “Grounding updated with TICKER date.”) or Reject. Reject = acknowledgment only.
5. **Cleanup:** `python scripts/delete_question.py --match "word"` (optional `--dry-run`); `python scripts/delete_duplicate_beliefs.py`; `python scripts/trim_beliefs.py` (optional `--dry-run`, `--per-company 3 --comparative 2 --total 8`).
6. **Answer questions:** Question detail → Answer → Save. Open questions = unanswered only.

---

## 7. Proposals (lifecycle & behavior)

- **Statuses:** pending (engine), accepted/rejected (user), expired (engine when condition false or TTL). No deletion.
- **Accept for review_prompt:** Attaches newest snapshot per ticker to belief, appends grounding_updated event, marks accepted. Stale condition resolves; proposal can expire on next engine run.
- **Accept for missing_grounding:** Acknowledgment only; no auto-attach.
- **Reject:** Status only; no structural change.
- **Creation:** Engine runs on each `/weekly-review` load. Creates review_prompt when belief has newer snapshots than its refs (and no non-expired proposal for that belief+type); creates missing_grounding when belief has no snapshot refs. Expires when condition false or TTL (30 days). `exists_for_belief(belief_id, type)` prevents duplicate pending.
- **Explain:** UI sends proposal_id; backend prepends “This proposal exists because newer snapshot(s) dated TICKER date, … were detected.” then LLM explanation.

---

## 8. LLM assist

- **Assistive only.** No auto-create beliefs, no auto accept/reject, no mutation of refs or lifecycle without user action.
- **Draft:** Belief/Question detail → Draft Refinement. Rephrase only; no new facts. Attribution: “LLM Draft Suggestion (Not Saved)”. Endpoints: `POST /api/llm/draft-belief-from-id`, `draft-question-from-id`.
- **Analyze:** Belief detail (when belief has newer snapshots) → Analyze Changes Since Last Review. Input: belief, previous/new snapshot summaries, last review. Output: delta_summary, potential_tensions, questions_raised. Attribution: “LLM Structural Analysis — For Review Only”. `POST /api/llm/analyze-belief/{belief_id}`.
- **Explain proposal:** Weekly review / proposal history → Explain. Prepends concrete “newer snapshot(s) dated X” line + LLM explanation. `POST /api/llm/explain-proposal` (proposal_id optional).
- **Config:** Ollama. `ollama serve`, `ollama pull llama3.1`. Env: `OLLAMA_BASE_URL`, `OLLAMA_MODEL` (default llama3.1:latest).

---

## 9. Review outcome (implemented)

- **Where:** Belief detail, “Record review outcome (optional)”. Outcomes: Reinforced, Slight tension, Strong tension, Inconclusive + optional note.
- **API:** `POST /api/beliefs/{belief_id}/review-outcome` body `{ "outcome": "reinforced"|"slight_tension"|"strong_tension"|"inconclusive", "note": "..." }`. Appends lifecycle event with `event_kind: "review_outcome"`.
- **Display:** Lifecycle events list shows “Review outcome: &lt;label&gt;” and note. Human-judged only; no auto-scoring.

---

## 10. StockSnapshot v1 (invariants)

- One company, one moment. Factual only; no opinions/predictions. Immutable. Time-bound (as_of). Source-aware (data_sources).
- Structure: metadata (snapshot_id, as_of, schema_version, data_sources), company (ticker, exchange, name, sector, industry, country), market_state (price, currency, market_cap, shares, 52w high/low), financials (revenue, profit, margin, quarterly), balance_sheet (assets, liabilities, debt, cash), user_notes (optional). No buy/sell, risk scores, forecasts, sentiment, portfolio context.

---

## 11. Phase 4 readiness

### Implemented (current system)

- Ingestion: Yahoo → StockSnapshot (import_snapshots.py), immutable, deterministic ID.
- Artifacts: Beliefs (thesis/risk), questions; references to snapshots.
- Weekly review: Open questions, beliefs needing review (days since last grounded snapshot), all beliefs, orphans, structural proposals; proposal engine on load.
- Proposals: review_prompt (newer snapshots), missing_grounding (no refs); create/expire rules; TTL 30d.
- Accept/Reject: review_prompt Accept attaches newest snapshot per ticker, grounding_updated event, redirect with “Grounding updated with TICKER date.”; Reject and missing_grounding Accept are acknowledgment only.
- UI copy: “Days since last grounded snapshot”; “Accept & Attach Latest Data” for review_prompt; Explain prepends “newer snapshot(s) dated X”; belief detail referenced snapshots table (Ticker | As of | Grounded) with latest-attached highlighted.
- Lifecycle: review_outcome (record on belief detail), grounding_updated (on Accept). **Decisions:** Record decision on belief detail (reinforced, slight/strong tension, revised, abandoned, confidence ↑/↓, deferred, other); append-only `event_kind: "decision"`. **Decision follow-up:** When recording a decision with `follow_up.action == "set_cadence"`, cadence row is set/updated; no other mutation. **Derived state:** current decision and decision timeline are computed from the log (not stored). Reports: `GET /api/reports/beliefs?decision=...`, `GET /api/reports/decision-summary?since=...`. **Analytics:** `GET /api/reports/durability`, `GET /api/reports/tension-density`, `GET /api/reports/trajectories` — descriptive only, never stored. **Observed outcomes:** `GET /api/reports/observed-outcomes` (JSON or `?format=csv`) — beliefs with current decision; includes `portfolio_returns` (ingested periods) and per-belief `returns_placeholder` when linked. **Returns ingestion:** Table `observed_return_periods` (period_start, period_end, return_pct, risk_metric, notes). Table `belief_return_observations` links beliefs to periods. `GET /api/reports/portfolio-returns` (list), `POST /api/reports/portfolio-returns` (add period), `POST /api/beliefs/{id}/return-observation` (link belief to period), `DELETE /api/beliefs/{id}/return-observation/{period_id}` (unlink). Read-only layer; does not mutate beliefs or decisions.
- **Belief confidence:** Human-set (low/medium/high) + optional rationale; stored as lifecycle event `event_kind: "confidence"`. API: `POST /api/beliefs/{id}/confidence`. Current confidence and “Set confidence” on belief detail; lifecycle list shows confidence events. See [BELIEF_CONFIDENCE_SPEC.md](BELIEF_CONFIDENCE_SPEC.md).
- **Review cadence:** Table `belief_review_cadence`. API: POST/DELETE `/api/beliefs/{id}/cadence`. “Due for review (cadence)” on weekly review when next_review_by ≤ today; set/clear on belief detail. next_review_by advances when recording review outcome if cadence_days set; decision follow-up can set cadence via `follow_up.action: "set_cadence"`. See [REVIEW_CADENCE_SPEC.md](REVIEW_CADENCE_SPEC.md).
- LLM: Draft, Analyze (delta), Explain (proposal) with Ollama; no mutation. **Agents/tools:** Drafting Assistant and Proposal Explainer documented in ARCHITECTURE with explicit contracts and guardrails (no belief creation, no decision recording, no artifact mutation); INVARIANTS #8.

### Spec’d but not implemented (for Phase 4 or later)

- None for the current slice (A.1–A.3, B.1, C.1–C.2 are implemented).

### Doc references (deep-dive)

| Topic | Doc |
|-------|-----|
| **Doc hub & index** | [README.md](README.md) |
| **Philosophy** | [PHILOSOPHY.md](PHILOSOPHY.md) |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Invariants** | [INVARIANTS.md](INVARIANTS.md) |
| **Roadmap** | [ROADMAP.md](ROADMAP.md) |
| **Charter (consolidated)** | [CHARTER.md](CHARTER.md) |
| **Phase 4 structural position** | [PHASE4_STRUCTURAL_POSITION.md](PHASE4_STRUCTURAL_POSITION.md) |
| Live fire (full) | [LIVE_FIRE.md](LIVE_FIRE.md) |
| Proposals (full) | [PROPOSALS.md](PROPOSALS.md) |
| LLM (full) | [LLM_ASSIST.md](LLM_ASSIST.md) |
| Data ingestion (full) | [DATA_INGESTION.md](DATA_INGESTION.md) |
| Adding beliefs/questions (full) | [ADDING_BELIEFS_QUESTIONS.md](ADDING_BELIEFS_QUESTIONS.md) |
| Beliefs example (template) | [BELIEFS_EXAMPLE.md](BELIEFS_EXAMPLE.md) |
| Review outcome spec | [REVIEW_OUTCOME_SPEC.md](REVIEW_OUTCOME_SPEC.md) |
| StockSnapshot v1 (full) | [stock_snapshot_v_1.md](stock_snapshot_v_1.md) |
| Belief confidence (spec) | [BELIEF_CONFIDENCE_SPEC.md](BELIEF_CONFIDENCE_SPEC.md) |
| Review cadence (spec) | [REVIEW_CADENCE_SPEC.md](REVIEW_CADENCE_SPEC.md) |
| System intent (reflective memo) | [SYSTEM_INTENT.md](SYSTEM_INTENT.md) |

---

## 12. Quick reference

| Action | Command / URL |
|--------|----------------|
| Run app | `conda activate snow` then `uvicorn main:app --reload` |
| Weekly review | http://localhost:8000/weekly-review |
| Import snapshots | `python scripts/import_snapshots.py` [--clear] [AAPL ...] [-q N] |
| List snapshots | `python scripts/add_artifact.py list-snapshots` |
| Seed beliefs | `python scripts/seed_beliefs.py` |
| Add belief CLI | `python scripts/add_artifact.py belief "..." [--snapshots id...] [--risk]` |
| Add question CLI | `python scripts/add_artifact.py question "..." [--snapshots id]` |
| Trim beliefs | `python scripts/trim_beliefs.py` [--dry-run] |
| Delete question | `python scripts/delete_question.py --match "word"` [--dry-run] |
| Proposal history | http://localhost:8000/proposals/history |
| Observed outcomes (JSON/CSV) | GET /api/reports/observed-outcomes [?format=csv] |
| Portfolio returns (list) | GET /api/reports/portfolio-returns |
| Add return period | POST /api/reports/portfolio-returns body: period_start, period_end, return_pct?, risk_metric?, notes? |
| Link belief to return period | POST /api/beliefs/{id}/return-observation body: return_period_id |
| Accept proposal | POST /proposals/{id}/accept |
| Reject proposal | POST /proposals/{id}/reject |
