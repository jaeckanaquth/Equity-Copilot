# StockSnapshot v1 — Specification

## 1. Purpose

A **StockSnapshot v1** is an immutable, time-stamped factual record describing the observable state of **one publicly listed company**, captured at a specific point in time.

The snapshot exists to:
- Enable comparison across time (same company, different dates)
- Enable comparison across entities (different companies)
- Anchor future analysis, theses, and agent reasoning in verifiable facts
- Preserve what was *actually known* at the time of capture

This document defines the **contract**, not the implementation.

---

## 2. Design Principles

- **Factual, not interpretive**  
  Only observable or directly computable facts are allowed. No opinions, predictions, or recommendations.

- **Immutable by design**  
  Once generated, a snapshot must never be modified. New information requires a new snapshot.

- **Time-bound truth**  
  Every value is valid only as-of the snapshot timestamp.

- **Source-aware**  
  Every snapshot must record where its data came from.

- **Intentionally shallow (v1)**  
  Enough detail to support reasoning later, not enough to embed assumptions now.

---

## 3. Snapshot Invariants (Non‑Negotiable Rules)

- A snapshot represents **one company, one moment in time**
- All fields are either:
  - Explicitly populated, or
  - Explicitly null / unavailable
- No field may encode judgment, sentiment, or intent
- Derived ratios are allowed only if they are mathematically trivial and source-transparent
- v1 fields must remain stable; additions require a new version

---

## 4. Snapshot Structure

### 4.1 Snapshot Metadata

Anchors the snapshot in time and provenance.

- `snapshot_id`  
  Unique identifier for this snapshot (e.g., UUID)

- `as_of`  
  ISO-8601 timestamp indicating when the snapshot was generated

- `schema_version`  
  Fixed value: `"v1"`

- `data_sources`  
  List of data sources used (e.g., `yahoo_finance`, `manual_csv`)

---

### 4.2 Company Identity

Stable identifiers describing what entity the snapshot refers to.

- `ticker`
- `exchange`
- `company_name`
- `sector`
- `industry`
- `country`

---

### 4.3 Market State (Observed)

Market facts as observed at snapshot time.

- `current_price`
- `currency`
- `market_cap`
- `shares_outstanding`
- `fifty_two_week_high`
- `fifty_two_week_low`

Constraints:
- No trend labels
- No momentum indicators
- No valuation opinions

---

### 4.4 Financial Summary (High-Level)

Coarse financial posture, not detailed accounting analysis.

**Annual (last completed financial year):**
- `revenue_fy`
- `net_profit_fy`
- `operating_margin_fy`

**Recent Quarters (most recent 4, ordered oldest → newest):**
- `quarterly_revenue`
- `quarterly_net_profit`

---

### 4.5 Balance Sheet Signals (Lightweight)

Minimal balance sheet indicators with high structural relevance.

- `total_assets`
- `total_liabilities`
- `total_debt`
- `cash_and_equivalents`

---

### 4.6 User Notes (Optional)

Free-form notes provided manually by the user.

- `user_notes`

Constraints:
- Plain text only
- No parsing or semantic assumptions
- Not modified by automated systems

---

## 5. Explicit Exclusions (v1)

The following are **not allowed** in StockSnapshot v1:

- Buy / sell / hold signals
- Risk scores or ratings
- Forecasts or price targets
- Sentiment analysis
- News interpretation
- AI-generated opinions or summaries
- Portfolio context

These belong to downstream systems that *consume* snapshots, not to the snapshot itself.

---

## 6. Intended Usage

StockSnapshot v1 is intended to be:
- Stored locally
- Queried and compared programmatically
- Rendered as human-readable Markdown
- Used as input to future agents, analyses, and tools

It is **not** intended to be:
- A live object
- A decision engine
- A substitute for human judgment

---

## 7. Versioning

- This document defines **StockSnapshot v1**
- Any incompatible change requires a new schema version
- v1 snapshots must remain readable and valid indefinitely

---

*End of Specification*

