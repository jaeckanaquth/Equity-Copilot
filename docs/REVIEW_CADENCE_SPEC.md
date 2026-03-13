# Review Cadence Reminders — Spec (C)

**Status:** Implemented. Cadence table, POST/DELETE API, weekly review “Due for review (cadence)”, set/clear on belief detail.

**Philosophy:** Reminders are **calendar-driven**, not truth-driven. The system does not judge belief health. You set when you want to review a belief again (e.g. “in 2 weeks” or “by 2026-03-01”); the app surfaces “Due for review (cadence)” when that date is reached. No automatic interpretation of data or belief strength.

---

## 1. Scope

- **User-set only:** You choose “next review by &lt;date&gt;” and optionally a repeat cadence (e.g. every 2 weeks). No auto-scheduling from data or LLM.
- **Separate from “Beliefs Needing Review”:** “Beliefs Needing Review” = there is **newer snapshot data** than last review. “Due for review (cadence)” = **calendar due date** has passed (or is today). Both can be shown; a belief can appear in one or both.
- **Optional:** Beliefs without a cadence never appear in the cadence-due list.

---

## 2. Data model

### 2.1 New table: `belief_review_cadence`

One row per belief that has a cadence set. Simple and queryable.

| Column           | Type      | Description |
|------------------|-----------|-------------|
| `belief_id`      | String PK | Reasoning artifact id (belief). |
| `next_review_by` | Date      | User wants to review by this date (inclusive). |
| `cadence_days`   | Int NULL  | Optional: repeat interval in days (e.g. 14 = every 2 weeks). When user records a review outcome (or “reviewed”), advance `next_review_by` by this many days. If NULL, no auto-advance. |
| `updated_at`     | DateTime  | Last time this row was set/updated. |

**Uniqueness:** One row per `belief_id`. Setting cadence again overwrites (upsert).

### 2.2 ORM (for implementation)

```python
# db/models/review_cadence.py

from sqlalchemy import Column, String, Date, Integer, DateTime
from db.session import Base
from datetime import datetime, timezone

def _utc_now():
    return datetime.now(timezone.utc)

class BeliefReviewCadenceORM(Base):
    __tablename__ = "belief_review_cadence"

    belief_id = Column(String, primary_key=True, index=True)
    next_review_by = Column(Date, nullable=False)
    cadence_days = Column(Integer, nullable=True)  # e.g. 14 for biweekly
    updated_at = Column(DateTime, nullable=False, default=_utc_now)
```

- Add to `db/init_db.py`: `Base.metadata.create_all(...)` will create the table when the model is imported and init runs.
- **Clear on --clear:** If `scripts/import_snapshots.py --clear` wipes artifacts/lifecycle/proposals, add wiping of `belief_review_cadence` so it stays consistent.

---

## 3. API

### 3.1 Set or update cadence

- **Method/URL:** `POST /api/beliefs/{belief_id}/cadence`
- **Body (JSON):**

  | Field            | Type   | Required | Description |
  |------------------|--------|----------|-------------|
  | `next_review_by`| string | Yes      | Date ISO (YYYY-MM-DD). When you want to review by. |
  | `cadence_days`  | int    | No       | If set, after you record a review outcome (or mark reviewed), advance `next_review_by` by this many days. E.g. 14 = every 2 weeks. Omit or null = no auto-advance. |

- **Response:** 201 no body, or 400 if date invalid / belief not found.
- **Side effect:** Upsert row in `belief_review_cadence` for this belief.

### 3.2 Clear cadence

- **Method/URL:** `DELETE /api/beliefs/{belief_id}/cadence`
- **Response:** 204 no body (or 404 if no row).
- **Side effect:** Delete row for this belief; it will no longer appear in “Due for review (cadence)”.

### 3.3 Reading

- **Belief detail:** When loading a belief, join or query `belief_review_cadence` by `belief_id`. If row exists, show “Next review by: 2026-03-01” and “Cadence: every 14 days” (if set). Expose to template so the UI can show set/clear and optional “Mark reviewed” that advances the date.
- **Weekly review:** New section “Due for review (cadence)”: list beliefs where `next_review_by <= today` (and row exists). Link to each belief. Optionally show the date and cadence.

---

## 4. When does “next review by” advance?

**Option A (recommended):** When the user **records a review outcome** (Reinforced / Slight tension / etc.) on the belief detail page, if that belief has a cadence with `cadence_days` set, automatically set `next_review_by = today + cadence_days` and update the row. So “recording an outcome” counts as “did the review.”

**Option B:** Separate “Mark reviewed” control that only advances the date (no outcome required). More flexible but one more action.

Spec recommends **Option A** for simplicity: same “Record outcome” flow advances the cadence when `cadence_days` is set.

---

## 5. UI

### 5.1 Belief detail page

- **Block: “Review cadence (optional)”**
  - “Next review by:” date picker (required when setting).
  - “Repeat every:” dropdown or number + “days” (e.g. 7, 14, 30, or empty for “no repeat”).
  - Buttons: “Save cadence” (POST), “Clear cadence” (DELETE).
- **Display:** If cadence exists, show “Next review by: &lt;date&gt;. Repeat every &lt;n&gt; days.” above or below the block.
- **Integration with review outcome:** When user clicks “Record outcome” and the belief has `cadence_days` set, after appending the lifecycle event the backend advances `next_review_by` by `cadence_days` (same request or immediately after). No extra UI for “mark reviewed.”

### 5.2 Weekly review page

- **New section:** “Due for review (cadence) (N)”
  - List beliefs where `next_review_by <= today`, grouped by company (or flat). Each row: belief text (truncated), “Due: &lt;date&gt;”, link to belief.
  - If none: “No beliefs due by cadence.”
- **Ordering:** By `next_review_by` ascending (most overdue first).

### 5.3 No automation of “what to believe”

- Cadence only means “you said you’d look at this again by X.” It does not:
  - Change belief health.
  - Auto-expire or invalidate beliefs.
  - Depend on snapshot data (that stays in “Beliefs Needing Review”).

---

## 6. Implementation checklist

- [ ] Add `BeliefReviewCadenceORM` and table in `db/models/review_cadence.py`; register in `init_db.py`.
- [ ] Add `POST /api/beliefs/{belief_id}/cadence` (upsert), `DELETE /api/beliefs/{belief_id}/cadence` (remove row).
- [ ] Service or route helper: “beliefs due by cadence” = query `belief_review_cadence` where `next_review_by <= today`, join to artifact repo for belief text/company.
- [ ] When recording review outcome (existing endpoint): if belief has cadence with `cadence_days`, set `next_review_by = today + cadence_days` and save.
- [ ] Belief detail: “Review cadence” block (date, optional cadence_days, save/clear); show current next_review_by and cadence.
- [ ] Weekly review: “Due for review (cadence)” section with list and link to each belief.
- [ ] `--clear` in import_snapshots (or init): delete from `belief_review_cadence` when wiping artifacts.

---

## 7. Summary

| Aspect           | Choice |
|------------------|--------|
| **Who sets it**  | User only (next_review_by, optional cadence_days). |
| **Stored as**    | New table `belief_review_cadence` (belief_id, next_review_by, cadence_days). |
| **Advance**      | When user records a review outcome and cadence_days is set: next_review_by = today + cadence_days. |
| **Surface**      | “Due for review (cadence)” on weekly review when next_review_by ≤ today. |
| **API**         | POST set/update, DELETE clear; read via existing belief + new query. |
| **Philosophy**   | Calendar-driven reminder only; no auto-judgment of belief health. |
