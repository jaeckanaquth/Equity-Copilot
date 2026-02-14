# Proposals — Lifecycle and Behavior

Proposals are **structural suggestions** the system generates when certain conditions hold (e.g. belief has newer snapshots, staleness). They are **manual only**: accept/reject is a user acknowledgment and does not change beliefs, snapshots, or artifacts.

---

## Statuses

| Status    | Meaning                          | Who sets it |
|-----------|----------------------------------|-------------|
| `pending` | Shown in UI, awaits user action   | Engine      |
| `accepted`| User acknowledged                | User        |
| `rejected`| User declined                    | User        |
| `expired` | Condition no longer holds or TTL  | Engine      |

**No deletion.** Proposals are never deleted; they only transition to these states.

---

## Accept / Reject Are Acknowledgments Only

Accept and Reject **do not**:

- Remove a stale belief from a section
- Add a lifecycle event on the belief
- Attach a snapshot
- Change anything structural

They only change the proposal’s state. The proposal lifecycle is kept **separate from the belief lifecycle** so that the audit trail lives in the proposals table and user agency is preserved (acknowledgment ≠ automatic artifact change).

---

## When Proposals Are Created (Regeneration)

- **Engine safeguard:** `exists_for_belief(belief_id, proposal_type)` prevents creating a new proposal when there is already a non-expired one (pending, accepted, or rejected). Only **expired** proposals allow regeneration, and only if the condition occurs again.
- **Transition rule:** Proposals are (re)created only when a structural condition transitions from **false → true**.
- When the condition becomes **false**, all non-expired proposals of that type are **expired** (pending, accepted, rejected).
- When the condition is **true** and no non-expired proposal exists, a new proposal is **created**.

So: accept/reject suppress until the condition goes away; when it does, proposals expire; when the condition comes back, a new proposal can be created. No permanent suppression, no spam.

---

## API and UI

- Proposals are listed in the weekly review and in proposal history.
- Accept/Reject are performed via the API; the UI shows pending proposals and lets the user acknowledge or decline.
- “Explain” (LLM) can describe why a proposal was triggered; see [LLM assist](LLM_ASSIST.md).
