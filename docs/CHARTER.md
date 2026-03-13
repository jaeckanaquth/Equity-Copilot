# Charter — Operational Scope & Constraints

**Operational only.** Who the system is for, what it does and does not do, how it is constrained. For why it exists and the epistemic guardrails, see [PHILOSOPHY.md](PHILOSOPHY.md).

---

## 1. Intended Audience

- The primary user (author)
- Engineers and developers interested in agentic AI or applied finance tooling
- Long-horizon, process-oriented investors running their own local copy

This project does not provide financial advice.

---

## 2. Scope (What the System Does)

### In scope

- Stock/company snapshots (immutable, one per company per moment)
- Financial statement analysis and quarter-over-quarter change
- Thesis and risk management: explicit beliefs, grounding, review, decision logs
- Structured review and proposal engine (newer data, missing grounding)
- Decision layer: append-only events; derived state and analytics
- Agentic architecture: multiple cooperating agents, tool use, structured memory
- Optional LLM assist: drafting, structural analysis, explanation (no mutation)

### Out of scope (non-goals)

- Automated trading or order execution
- Price prediction or “market beating” claims
- High-frequency or intraday trading logic
- Mandatory paid data sources
- Black-box reasoning without traceability
- Belief-rewriting or auto-creation of beliefs from decisions

---

## 3. Technology Constraints

- Free and open-source tooling where possible
- Local LLMs as default (e.g. Ollama); pluggable by design
- Simple, auditable storage (SQLite, local files)
- No hard dependency on proprietary APIs

Some data ingestion may use manual exports or user-provided files to stay within ethical and legal bounds.

---

## 4. Success Criteria

The project is successful if:

- It is used regularly for real research and review decisions
- Reasoning clarity and auditability improve; self-deception is reduced
- A third party can reproduce the system locally with reasonable effort
- The codebase and docs remain clear and coherent over time
- The philosophy and invariants stay fixed while features evolve

---

## 5. Evolution

The system is iterative. Features are added incrementally and documented. **The philosophy and invariants should not change.** See [ROADMAP.md](ROADMAP.md) for phases.

---

## References

- [PHILOSOPHY.md](PHILOSOPHY.md) — Why it exists, problem, causal chain, guardrail
- [INVARIANTS.md](INVARIANTS.md) — Non-negotiable constraints
- [ARCHITECTURE.md](ARCHITECTURE.md) — Structural design
