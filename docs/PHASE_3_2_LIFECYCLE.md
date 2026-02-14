# Phase 3.2 — Proposal Lifecycle (Manual Only)

## Decision: A vs B

**When a proposal is accepted, should we record a lifecycle event on the belief?**

**Chosen: B — Keep proposal lifecycle separate from belief lifecycle.**

Accepting a proposal is a recorded acknowledgment. It does **not**:
- Add a lifecycle event on the belief (e.g. "review acknowledged")
- Modify beliefs, snapshots, or artifacts

Proposals and beliefs remain independent. This preserves:
- Audit trail in proposals table only
- No hidden coupling between proposal actions and belief history
- User agency: acknowledgment ≠ automatic artifact mutation

---

## Status States

| Status    | Meaning                          | Who sets it |
|-----------|----------------------------------|-------------|
| `pending` | Shown in UI, awaits user action   | Engine      |
| `accepted`| User acknowledged                | User        |
| `rejected`| User declined                    | User        |
| `expired` | Condition no longer holds or TTL  | Engine      |

**No deletion. Ever.**

---

## Critical Rule

Accept/Reject are **acknowledgments only**. They do not:
- Remove stale belief from a section
- Add lifecycle event
- Attach snapshot
- Change anything structural

They only change proposal state.

---

## Engine Safeguard

`exists_for_belief(belief_id, proposal_type)` blocks regeneration when:
- `pending` exists (idempotency)
- `accepted` exists (user acknowledged)
- `rejected` exists (user declined)

Only `expired` proposals allow regeneration — and only if the condition reoccurs.

---

## Transition Logic (State-Aware Regeneration)

**Rule:** Proposals regenerate only when a structural condition transitions from false → true.

**Implementation:**

1. When condition becomes **false** → expire ALL non-expired proposals of that type (pending, accepted, rejected).
2. When condition is **true** AND no non-expired proposal exists → create.

This achieves:
- Accept → suppress until condition resolves
- Condition resolves → expire (clears acknowledgment)
- Condition reoccurs → create new proposal

No permanent suppression. No spam. Clean false → true detection.

**Choice:** When condition resolves, we expire (Option A). State machine stays clean; accepted/rejected do not persist when the world has changed.
