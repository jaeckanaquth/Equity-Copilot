# Project Charter
**Project Name (working):** Equity Copilot  
**Tagline:** A local-first, agentic equity research and portfolio intelligence system

---

## 1. Purpose

Equity Copilot is a **local-first, agentic AI system** designed to support *individual* equity research and portfolio decision-making through structured analysis, transparent reasoning, and disciplined record-keeping.

The primary goal is **education through construction**: learning agentic AI, financial analysis, and systems design by building a real, functional system that can be used daily by a single person.

A secondary goal is **practical utility**: the system should be genuinely helpful for researching stocks, tracking investment theses, and understanding portfolio risk—without automating trading or making opaque predictions.

---

## 2. Core Principles

- **Individual-first**  
  Designed for one primary user. No shared accounts, social features, or collaboration assumptions.

- **Local-first by default**  
  Most computation, data storage, and inference run locally to minimize cost, maximize control, and preserve privacy.

- **Agentic, not monolithic**  
  The system is composed of narrowly scoped agents with clear responsibilities, coordinated by an orchestrator.

- **Decision support, not decision replacement**  
  The system assists human judgment; it does not execute trades or claim predictive authority.

- **Reproducible, not hosted-first**  
  Anyone should be able to clone the repository and run their own local copy. A hosted instance, if present, is only a reference demo.

---

## 3. Scope (What the System Does)

### In Scope

- Equity research automation:
  - Stock/company snapshots (one-pagers)
  - Financial statement analysis
  - Quarter-over-quarter change detection
  - News and narrative summarization

- Portfolio intelligence:
  - Holdings tracking
  - Allocation and exposure analysis
  - Risk and correlation insights

- Thesis and journal management:
  - Explicit bull and bear cases
  - Assumptions tracking
  - Decision logs and thesis drift over time

- Agentic architecture:
  - Multiple cooperating agents
  - Tool usage and task delegation
  - Structured short-term and long-term memory

---

## 4. Non-Goals (Explicitly Out of Scope)

- Automated trading or order execution
- Price prediction or "market beating" claims
- High-frequency or intraday trading logic
- Mandatory paid data sources
- Black-box reasoning without traceability

These exclusions are intentional to avoid regulatory, ethical, and epistemic pitfalls.

---

## 5. Deployment & Accessibility

- **Primary mode:** Local execution (CLI and/or local web UI)
- **Optional mode:** A single-user hosted instance on the author’s website
  - Read-only or limited interaction
  - Intended for demonstration and learning

The hosted version is not a commercial product and is not required for normal use.

---

## 6. Technology Constraints

- Free and open-source tooling where possible
- Local LLMs as the default (pluggable by design)
- Simple, auditable storage (e.g., SQLite, local files)
- No hard dependency on proprietary APIs

**Assumption:** Some data ingestion may require manual exports or user-provided files to remain within ethical and legal boundaries.

---

## 7. Intended Audience

- The author (primary user)
- Engineers learning agentic AI systems
- Developers interested in applied finance tooling
- Advanced retail investors using their own local copy

This project does not provide financial advice.

---

## 8. Success Criteria

The project is considered successful if:

- It is used regularly for real research decisions by the author
- Each major feature teaches a concrete technical or financial concept
- A third party can reproduce the system locally with reasonable effort
- The codebase shows clear, incremental evolution over time
- The system remains understandable after long breaks

---

## 9. Evolution Over Time

This is a **year-long, iterative project**. Features will be added incrementally, documented clearly, and justified by learning value rather than novelty.

The system is expected to change. The philosophy should not.

---

*End of Project Charter*

