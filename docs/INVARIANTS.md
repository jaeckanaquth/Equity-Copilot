# Invariants — Hard Constraints

The constitution. Non-negotiable. **Status:** In force; project closed for current slice.

---

## Non-Negotiable Invariants

1. **No mutation of snapshots.**  
   StockSnapshot rows are immutable. Deterministic IDs. No edits, no deletes of historical financial data.

2. **No mutation of belief text.**  
   `ReasoningArtifact.claim.statement` never changes after creation. No semantic rewrite, no auto-edit.

3. **No auto-creation of beliefs from decisions.**  
   Recording `revised` or any decision does not create a new belief. The analyst creates beliefs explicitly.

4. **No state machine enforcement.**  
   No workflow states (e.g. active → abandoned) override the log. Beliefs are not tickets.

5. **No performance-driven semantic edits.**  
   Returns and performance observation do not trigger automatic changes to beliefs or decisions.

6. **Lifecycle is append-only.**  
   New events only. No updates or deletes to existing lifecycle rows.

7. **All “current state” views are derived.**  
   Current decision, tension density, durability, trajectories: computed from the log. Not stored as authoritative state.

8. **Agents and tools do not mutate reasoning layer.**  
   Any agent or tool (e.g. drafting assistant, proposal explainer) has an explicit contract: no belief creation, no decision recording, no artifact or lifecycle mutation. See ARCHITECTURE § Agents & Tools.

---

## When in Doubt

**Preserve epistemic integrity.**

This file prevents cleverness from destroying coherence.
