# Live Fire — Operating the System End-to-End

This runbook walks through running Equity Copilot with **real snapshots**, **2–3 beliefs per company**, the **weekly review**, and **accept/reject proposals**. Use it to observe tension and document friction. **Status:** Final; project closed.

**Prerequisite:** Ingestion + creation are working (you’ve already added a week’s review of theses/risk).

---

## 1. Import real snapshots

Import quarterly financials from Yahoo Finance into `StockSnapshot` artifacts. One snapshot per quarter per ticker; existing ticker+quarter are skipped (immutable).

```bash
conda activate snow
python scripts/import_snapshots.py
```

- **Default tickers:** MSFT, AMZN, JPM (up to 8 quarters each).
- **Custom tickers:** `python scripts/import_snapshots.py AAPL GOOGL`
- **Fresh start (wipe all data first):** `python scripts/import_snapshots.py --clear`
- **Fewer quarters:** `python scripts/import_snapshots.py -q 4`

Check: list snapshots with `python scripts/add_artifact.py list-snapshots`.

---

## Immediate action items (cleanup)

If you have too many beliefs or a “weekly AWS prediction”–style question, run:

1. **Delete the AWS prediction question** (or any question matching words):
   ```bash
   conda activate snow
   python scripts/delete_question.py --match "prediction" "AWS"
   ```
   Use `--dry-run` to list matches first. To delete by ID: `--id <uuid>`.

2. **Deduplicate beliefs** (keeps oldest per statement+type):
   ```bash
   python scripts/delete_duplicate_beliefs.py
   ```

3. **Trim to ~7–8 beliefs** (2–3 per company, 1–2 comparative):
   ```bash
   python scripts/trim_beliefs.py
   ```
   Use `--dry-run` to see what would be kept/deleted. Options: `--per-company 3 --comparative 2 --total 8`.

Target: **~7–8 total beliefs**, not 24. Re-seeding uses the trimmed `seed_beliefs.py` (8 beliefs).

---

## 2. Create 2–3 beliefs per company

Either use the **seeded set** (MSFT/AMZN/JPM theses and risks) or add your own.

**Option A — Seed script (recommended for live fire):**

```bash
conda activate snow
python scripts/seed_beliefs.py
```

This creates the example beliefs from `scripts/seed_beliefs.py` (2–3 theses/risks per company + comparative beliefs), each linked to all snapshots for that ticker.

**Option B — Manual (UI):**

1. Open [http://localhost:8000/weekly-review](http://localhost:8000/weekly-review).
2. Use **Add belief** (or go to `/beliefs/new`).
3. Enter statement, optionally check **Treat as risk**, select snapshot(s). Submit.

**Option C — CLI:**

```bash
python scripts/add_artifact.py belief "Your thesis or risk here." [--snapshots ID1 ID2 ...] [--risk]
```

Aim for **2–3 beliefs per company** (mix of theses and risks) so the weekly review has enough to propose actions on.

---

## 3. Run weekly review

1. Start the app if needed:
   ```bash
   conda activate snow
   uvicorn main:app --reload
   ```
2. Open **[http://localhost:8000/weekly-review](http://localhost:8000/weekly-review)**.

You should see:

- **Open questions**
- **Beliefs needing review** (beliefs that have newer snapshots than when they were created)
- **All beliefs** (theses/risks grouped by company)
- **Orphans** (e.g. beliefs without snapshots)
- **Structural proposals** (e.g. “Review belief X — newer data”, “Link belief to snapshots”)

The page runs the proposal engine and lists pending proposals; use them in step 4.

---

## 3b. Answer questions

**Open questions** on the weekly review are research questions that don’t have a recorded answer yet. Frame new questions so they are mechanism-driven, snapshot-connected, and structurally reviewable (see [Adding beliefs and questions](ADDING_BELIEFS_QUESTIONS.md#framing-questions-to-fit-the-system)). Once you answer one, it disappears from “Open questions” (so that list stays actionable).

**How to answer:**

1. On the weekly review, click a question in **Open questions** (or open any question at `/questions/{id}`).
2. On the question detail page, type your answer in the **Answer** text area (findings, decision, or “deferred” / “N/A”).
3. Click **Save answer** (or **Update answer** to change it later).

Answers are stored per question; you can edit them anytime from the question page. The list **Open questions** shows only questions with no answer, so you can use it as a working list.

---

## 4. Accept / reject proposals

- **In the UI:** On the weekly review (and wherever proposals are rendered), use the **Accept** / **Reject** actions for each pending proposal.
- **API (for scripting/automation):**
  - Accept: `POST /proposals/{proposal_id}/accept`
  - Reject: `POST /proposals/{proposal_id}/reject`

Accept and reject are **acknowledgments only**: they do not change beliefs, snapshots, or lifecycle. They only update the proposal status. See [PROPOSALS.md](PROPOSALS.md).

**Audit:** [http://localhost:8000/proposals/history](http://localhost:8000/proposals/history) shows all proposals by type and status.

---

## 4b. Reports (read-only)

- **Observed outcomes:** Beliefs with current decision, plus portfolio return periods and per-belief return placeholders. From the weekly review, use **Observed outcomes** (or call `GET /api/reports/observed-outcomes` for JSON, or `?format=csv` for CSV).
- **Other reports:** Decision summary, beliefs by decision, durability, tension-density, trajectories, portfolio returns — see [MASTER.md](MASTER.md) §12 Quick reference.

---

## 5. Wait for next quarter import

- After the next quarter’s data is available, run the import again (same command as step 1). New quarter snapshots will be added; existing quarters are skipped.
- Re-open the weekly review. More beliefs may move into **Beliefs needing review** and new proposals may appear (e.g. “Review belief X — newer data”).

This is when **tension** appears: which beliefs get proposed, how often, and whether the workflow (review → accept/reject) feels right.

---

## 6. Observe tension

Watch for:

- **Proposal volume:** Too many/too few proposals?
- **Clarity:** Is it obvious what each proposal is asking you to do?
- **Staleness vs. noise:** Do “newer data” proposals feel timely or noisy?
- **Orphans and coverage:** Do beliefs without snapshots or with missing coverage get surfaced in a useful way?
- **Accept/reject semantics:** Does “acknowledge only” match how you want to work, or do you want accept to trigger a concrete action (e.g. “mark reviewed” on the belief)?

---

## 7. Document friction

Use the table below (or a separate doc) to log friction as you run the live fire. Copy and fill as you go.

| Date       | Step / area        | What happened | Friction / observation |
|------------|--------------------|---------------|-------------------------|
|            | Import             |               |                         |
|            | Beliefs            |               |                         |
|            | Weekly review      |               |                         |
|            | Accept/reject      |               |                         |
|            | Questions / answers|               |                         |
|            | Next quarter       |               |                         |
|            | (other)            |               |                         |

---

## Quick reference

| Action              | Command / URL |
|---------------------|---------------|
| Import snapshots    | `python scripts/import_snapshots.py` |
| List snapshots      | `python scripts/add_artifact.py list-snapshots` |
| Seed beliefs        | `python scripts/seed_beliefs.py` |
| Weekly review       | [http://localhost:8000/weekly-review](http://localhost:8000/weekly-review) |
| Proposal history    | [http://localhost:8000/proposals/history](http://localhost:8000/proposals/history) |
| Accept proposal     | `POST /proposals/{id}/accept` |
| Reject proposal     | `POST /proposals/{id}/reject` |
| Answer a question   | Open `/questions/{id}` → fill Answer → Save answer |
| Observed outcomes (JSON/CSV) | [GET /api/reports/observed-outcomes](http://localhost:8000/api/reports/observed-outcomes) — add `?format=csv` for CSV |
