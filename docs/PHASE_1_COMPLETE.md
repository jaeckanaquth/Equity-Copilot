# Phase 1 — Factual Snapshot Foundation

## What Phase 1 Is

Phase 1 establishes the **factual data foundation** of Equity Copilot.

It defines a **single, immutable data contract** — `StockSnapshot v1` — that represents what was *factually known* about one publicly listed company at one specific point in time.

This phase intentionally contains:

* **No intelligence**
* **No opinions**
* **No predictions**
* **No agents**
* **No data fetching**
* **No storage**

Phase 1 answers only one question:

> *How do we represent facts in a way that future reasoning cannot corrupt?*

---

## Core Outcome

At the end of Phase 1, the system has:

* A frozen **StockSnapshot v1 specification** (Markdown = source of truth)
* A strict **Pydantic model** that enforces the spec
* Explicit handling of missing data via `null`
* Guaranteed immutability after creation
* A single, explicit construction path
* Tests that lock the contract

Once Phase 1 is complete, **facts are protected from interpretation forever**.

---

## Key Concepts Introduced

### 1. StockSnapshot v1

A `StockSnapshot` is:

* A factual record
* About **one company**
* At **one moment in time**
* With **explicit provenance**
* And **no embedded judgment**

It is not:

* A live object
* A recommendation
* An analysis
* A forecast
* A portfolio artifact

Snapshots are **inputs** to reasoning, never outputs.

---

### 2. Explicit Nulls

Every field in the snapshot must be either:

* populated with a value, or
* explicitly set to `null`

This avoids:

* silent assumptions
* “missing means zero” bugs
* accidental inference

Unknown is treated as a **first-class state**, not an error.

---

### 3. Immutability

Once a snapshot is created:

* It cannot be modified
* Any change requires a **new snapshot**

This ensures:

* Historical truth is preserved
* Analysis can be replayed later
* No retroactive rewriting of facts

Immutability is enforced at the model level.

---

### 4. Time-Bound Truth

Every snapshot has an `as_of` timestamp:

* Timezone-aware
* Normalized to IST
* Required

This encodes the idea that:

> Facts are only true *as of when they were observed*.

---

## Code Structure (Phase 1)

```
core/
  models/
    stock_snapshot.py        # Immutable Pydantic models
  builders/
    stock_snapshot_builder.py # Single construction path

tests/
  test_stock_snapshot.py
  test_stock_snapshot_builder.py
```

---

## Snapshot Creation Flow

1. Raw data is gathered **outside** the snapshot system
2. Data is passed explicitly into the builder
3. Builder:

   * performs no logic
   * performs no defaults
   * performs no interpretation
4. Pydantic validates everything
5. An immutable `StockSnapshot` is returned

If anything is invalid → the process fails loudly.

This is intentional.

---

## What Phase 1 Does NOT Do

Phase 1 deliberately excludes:

* Data ingestion or scraping
* APIs or connectors
* Financial analysis
* Ratio interpretation
* Trend detection
* Agent logic
* Portfolio context
* Storage or persistence
* Serialization formats

All of those belong to **later phases**.

---

## Why Phase 1 Exists

Most systems mix:

* facts
* assumptions
* interpretations
* convenience logic

This makes them impossible to reason about later.

Phase 1 draws a **hard line**:

* Facts live here
* Reasoning lives later

Every future feature must respect this boundary.

---

## Phase Boundary

Phase 1 is **complete and frozen**.

Any change to:

* fields
* meanings
* constraints

requires a **new schema version**.

Phase 2 and beyond may **consume** snapshots, but must never modify them.

---

## Summary

Phase 1 delivers a boring, strict, and unyielding foundation.

That boredom is the feature.

Everything interesting that happens later will only be trustworthy because Phase 1 refused to be clever.