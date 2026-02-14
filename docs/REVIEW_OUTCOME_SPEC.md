# Manual Review Outcome — Lifecycle Payload & UI Spec

Belief health remains **human-judged**. The system does not auto-classify tension or reinforcement. This spec adds an optional **manual review outcome** recorded when you complete a belief review: a single choice (Reinforced / Slight tension / Strong tension / Inconclusive) plus optional note, stored as a lifecycle event. Implementation can follow this later without changing the philosophy.

---

## 1. Philosophy (unchanged)

- The app surfaces **deltas** and **linkage** (Option 2, staleness, snapshots).
- **You** decide whether the belief is reinforced or under tension.
- Recording the outcome is **optional** and **user-only**; no automated scoring or interpretation.

---

## 2. Lifecycle payload

### 2.1 Event type

Use the **same** table `belief_lifecycle_events`. New events have a distinct payload shape so they can be rendered differently from existing state-transition events.

- **Discrimination:** payload contains `"outcome"` (and optionally `"event_kind": "review_outcome"`) so the UI/API can tell “review outcome” events from legacy `BeliefLifecycleEvent` payloads.

### 2.2 Payload shape (review outcome event)

Stored in `BeliefLifecycleEventORM.payload` (JSON). All fields in the payload; the ORM still stores `event_id`, `belief_id`, `created_at` at top level (as today).

| Field           | Type     | Required | Description |
|-----------------|----------|----------|-------------|
| `event_id`      | UUID str | Yes      | Unique event id (e.g. uuid4). |
| `schema_version`| Literal  | Yes      | `"v1"`. |
| `occurred_at`   | ISO datetime | Yes | When the user recorded the outcome. |
| `recorded_by`   | Literal  | Yes      | `"human"` only for this event kind. |
| `reasoning_id`  | UUID str | Yes      | Belief (artifact) id. |
| `event_kind`    | Literal  | Yes      | `"review_outcome"` so consumers can detect. |
| `trigger`       | Literal  | Yes      | `"manual_review"`. |
| `outcome`       | Enum     | Yes      | See below. |
| `note`          | string   | No       | Optional free-text note (e.g. one line). |

**Outcome enum (string values):**

| Value            | Label (UI)      | Meaning (user-interpreted) |
|------------------|-----------------|----------------------------|
| `reinforced`     | Reinforced      | Data aligns with belief.   |
| `slight_tension` | Slight tension  | Some friction; belief still held with caveats. |
| `strong_tension` | Strong tension  | Material contradiction or mechanism under pressure. |
| `inconclusive`   | Inconclusive    | Can’t tell yet or data not decisive. |

### 2.3 Pydantic model (for implementation)

```python
# core/models/belief_lifecycle_event.py (add)

from typing import Literal, Optional
from enum import Enum

class ReviewOutcome(str, Enum):
    reinforced = "reinforced"
    slight_tension = "slight_tension"
    strong_tension = "strong_tension"
    inconclusive = "inconclusive"

class BeliefReviewOutcomeEvent(BaseModel):
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["review_outcome"] = "review_outcome"
    trigger: Literal["manual_review"] = "manual_review"
    outcome: ReviewOutcome
    note: Optional[str] = None
```

`BeliefLifecycleRepository.append(event)` already works: it uses `event_id`, `reasoning_id` → `belief_id`, `occurred_at` → `created_at`, and `payload = event.model_dump(mode="json")`.

### 2.4 Backward compatibility

- **Existing** lifecycle events (state transitions) have no `outcome` and no `event_kind`. Keep rendering them as today (e.g. “previous_state → new_state” or raw payload).
- **New** events have `event_kind == "review_outcome"` and `outcome` in payload. Render as “Review outcome: &lt;label&gt;” and optional note.

---

## 3. API

### 3.1 Record review outcome

- **Method/URL:** `POST /api/beliefs/{belief_id}/review-outcome`
- **Body (JSON):**

  | Field    | Type   | Required | Description |
  |----------|--------|----------|-------------|
  | `outcome`| string | Yes      | One of `reinforced`, `slight_tension`, `strong_tension`, `inconclusive`. |
  | `note`   | string | No       | Optional note; max length e.g. 500. |

- **Response:** 201 with no body, or 400 if `outcome` invalid / belief not found.
- **Side effect:** One new row in `belief_lifecycle_events` with payload as in §2.2. No change to the belief artifact itself; no proposal state change.

### 3.2 Reading

- **Existing:** `GET /beliefs/{belief_id}` (belief detail) already receives `lifecycle_events` from `lifecycle_repo.list_for_belief(belief_id)`. Each item has `created_at` and `payload`.
- **Rendering:** In the template (or a small helper), for each event:
  - If `payload.get("event_kind") == "review_outcome"`: show “Review outcome: &lt;label&gt;” and `payload.get("note")` if present.
  - Else: keep current display (e.g. payload summary or raw).

No new read endpoint required.

---

## 4. UI

### 4.1 Where

- **Belief detail page** (`/beliefs/{belief_id}`), after **Option 2 — Structural Change Analysis** (and after the user has had a chance to read the delta). Optionally show the block only when `has_newer_snapshots` is true (same condition as Option 2), so “review outcome” is in context of “you’ve seen new data.”

### 4.2 Block contents

- **Heading:** e.g. “Record review outcome (optional)”.
- **Subtext:** “Your judgment only. Not stored as fact.”
- **Controls:**
  - **Outcome:** Single choice (radio or buttons).
    - Reinforced  
    - Slight tension  
    - Strong tension  
    - Inconclusive  
  - **Note (optional):** Single-line or short text input, placeholder e.g. “Optional note”.
  - **Submit:** “Record outcome” (or “Save”). POST to `POST /api/beliefs/{belief_id}/review-outcome` with `{ "outcome": "...", "note": "..." }`.
- **After submit:** Reload the page or re-fetch lifecycle; the new event appears under “Lifecycle Events” as “Review outcome: &lt;label&gt;” and optional note. Optionally show a short “Recorded.” confirmation.

### 4.3 Lifecycle events list

- For each event with `payload.event_kind == "review_outcome"`:
  - Display: `{created_at} — Review outcome: Reinforced` (or Slight tension / Strong tension / Inconclusive).
  - If `payload.note` is present: show it on the same or next line (e.g. grey, smaller).
- For other events: keep existing display (e.g. `created_at — payload` or a short summary).

### 4.4 No automation

- No pre-selection of outcome.
- No “suggested” outcome from Option 2 or any LLM. Option 2 remains “for review only”; the user chooses the outcome independently.

---

## 5. Implementation checklist (for later)

- [ ] Add `ReviewOutcome` enum and `BeliefReviewOutcomeEvent` model (e.g. in `core/models/belief_lifecycle_event.py`).
- [ ] Add `POST /api/beliefs/{belief_id}/review-outcome` (validate `outcome`, build `BeliefReviewOutcomeEvent`, `lifecycle_repo.append(event)`).
- [ ] Belief detail template: add “Record review outcome” block (outcome radios, optional note, submit); show only when `has_newer_snapshots` if desired.
- [ ] Belief detail template: in “Lifecycle Events”, branch on `payload.event_kind == "review_outcome"` and render label + note; else keep current payload display.
- [ ] Optional: client-side reload or inline insert of the new event after POST so the user sees it without a full page refresh.

---

## 6. Summary

| Aspect | Choice |
|--------|--------|
| **Who decides** | User only. |
| **Stored as** | Lifecycle event (same table, new payload shape). |
| **Payload** | `event_kind: "review_outcome"`, `outcome`, optional `note`, plus ids/datetime. |
| **API** | `POST /api/beliefs/{belief_id}/review-outcome` with `outcome` (+ optional `note`). |
| **UI** | Belief detail; optional block after Option 2; radios + optional note; list shows “Review outcome: &lt;label&gt;”. |
| **Philosophy** | Unchanged: system surfaces deltas; you interpret; recording outcome is optional and human-only. |
