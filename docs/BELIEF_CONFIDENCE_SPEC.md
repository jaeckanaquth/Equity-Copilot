# Manual Belief Confidence — Spec (B)

**Philosophy:** Confidence is **human-set only**. The system does not compute or suggest confidence. You optionally record how confident you are in a belief (low / medium / high); it is stored as a lifecycle event so the artifact stays immutable and you have a history of updates. **Implemented.**

---

## 1. Scope

- **Manual only:** User chooses a confidence level (and optionally a short rationale). No auto-scoring, no LLM suggestion.
- **Stored as lifecycle event:** Same table `belief_lifecycle_events`, new payload shape (`event_kind: "confidence"`). Latest such event defines “current confidence” for display.
- **Optional:** Beliefs can have no confidence event; display as “Not set” or hide the line.

---

## 2. Payload shape (confidence event)

Stored in `BeliefLifecycleEventORM.payload`. ORM fields unchanged: `event_id`, `belief_id`, `created_at`.

| Field            | Type     | Required | Description |
|------------------|----------|----------|-------------|
| `event_id`       | UUID str | Yes      | Unique event id. |
| `schema_version` | Literal  | Yes      | `"v1"`. |
| `occurred_at`    | ISO datetime | Yes | When the user set it. |
| `recorded_by`    | Literal  | Yes      | `"human"`. |
| `reasoning_id`   | UUID str | Yes      | Belief id. |
| `event_kind`     | Literal  | Yes      | `"confidence"`. |
| `trigger`        | Literal  | Yes      | `"manual"`. |
| `confidence_level` | Enum   | Yes      | `low` \| `medium` \| `high`. |
| `rationale`      | string   | No       | Optional short rationale (e.g. 500 chars). |

**Confidence enum:** Reuse existing `ConfidenceLevel` from `core.models.reasoning_artifact` (low, medium, high).

---

## 3. Pydantic model (for implementation)

```python
# core/models/belief_lifecycle_event.py (add)

class BeliefConfidenceEvent(BaseModel):
    event_id: UUID
    schema_version: Literal["v1"] = "v1"
    occurred_at: datetime
    recorded_by: Literal["human"] = "human"
    reasoning_id: UUID
    event_kind: Literal["confidence"] = "confidence"
    trigger: Literal["manual"] = "manual"
    confidence_level: ConfidenceLevel  # from reasoning_artifact
    rationale: Optional[str] = None
```

`BeliefLifecycleRepository.append(event)` works as-is (uses `reasoning_id` → `belief_id`, `occurred_at` → `created_at`, full dump as payload).

---

## 4. API

### 4.1 Set confidence

- **Method/URL:** `POST /api/beliefs/{belief_id}/confidence`
- **Body (JSON):**

  | Field              | Type   | Required | Description |
  |--------------------|--------|----------|-------------|
  | `confidence_level`| string | Yes      | One of `low`, `medium`, `high`. |
  | `rationale`       | string | No       | Optional; max e.g. 500 chars. |

- **Response:** 201 no body, or 400 if invalid / belief not found.
- **Side effect:** One new row in `belief_lifecycle_events`. Belief artifact unchanged.

### 4.2 Reading

- **Current confidence:** From `lifecycle_repo.list_for_belief(belief_id)` — take the **latest** event with `payload.event_kind == "confidence"`; `confidence_level` (+ optional `rationale`) is “current confidence.”
- Belief detail page can show “Confidence: High (set 2026-02-14)” and list prior confidence events under Lifecycle Events.

---

## 5. UI

### 5.1 Where

- **Belief detail page** (`/beliefs/{id}`): a small block “Set confidence (optional)” with:
  - Radios or dropdown: **Low** / **Medium** / **High**
  - Optional text field: “Rationale”
  - Button: “Save confidence”
- **Display:** Show “Current confidence: &lt;level&gt; (set &lt;date&gt;)” near the top or next to the belief text; if no confidence event, show “Not set” or omit.

### 5.2 Lifecycle events list

- For events with `event_kind == "confidence"`: show “Confidence set to &lt;level&gt;” and optional rationale, plus date.
- Other events unchanged.

### 5.3 Optional: weekly review

- “All beliefs” or a separate column could show current confidence (from latest confidence event) per belief. Not required for MVP.

---

## 6. Implementation checklist

- [ ] Add `BeliefConfidenceEvent` in `core/models/belief_lifecycle_event.py` (use `ConfidenceLevel` from reasoning_artifact).
- [ ] Add `POST /api/beliefs/{belief_id}/confidence` (validate level, append event).
- [ ] Belief detail: “Set confidence” block (level + optional rationale); submit → POST → reload or refresh.
- [ ] Belief detail: compute “current confidence” from latest `event_kind == "confidence"` and display; in Lifecycle list, render confidence events as “Confidence set to &lt;level&gt;”.
- [ ] Optional: helper in `BeliefAnalysisService` or artifact_detail route to resolve “current_confidence” for a belief from lifecycle events.

---

## 7. Summary

| Aspect        | Choice |
|---------------|--------|
| **Who sets it** | User only. |
| **Stored as**   | Lifecycle event (`event_kind: "confidence"`). |
| **Values**     | low / medium / high (+ optional rationale). |
| **API**        | `POST /api/beliefs/{belief_id}/confidence` with `confidence_level` (+ optional `rationale`). |
| **Current**    | Latest confidence event per belief. |
| **Philosophy** | No auto-scoring; human-judged only. |
