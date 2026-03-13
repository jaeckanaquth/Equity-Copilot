# Adding Beliefs and Questions

**Implemented.** From the app:

1. Open **Weekly Review** (`/weekly-review`).
2. Click **Add belief or question** (or go to `/create`).
3. Use one of the two forms:
   - **Add belief:** Enter the statement, optionally check “Treat as risk”, optionally select reference snapshots. Submit → you are redirected to the new belief page.
   - **Add question:** Enter the question, optionally select reference snapshots. Submit → you are redirected to the new question page.

Reference snapshots link the artifact to specific data (e.g. MSFT 2025-12-31). They are used for coverage, “beliefs needing review”, and LLM context.

### Framing questions to fit the system

Questions work best when they are **mechanism-driven**, **tied to snapshots**, and **structurally reviewable**:

- **Mechanism-driven:** Ask about leading indicators, drivers, or conditions—not one-off predictions.  
  - Prefer: *“What leading indicators would suggest AWS growth acceleration in the next quarter?”*  
  - Avoid: *“What is next week’s prediction for AWS?”*
- **Snapshot-connected:** Attach reference snapshots (company/quarter) so the question is grounded in data and shows up in coverage and review.
- **Structurally reviewable:** Phrase so you can later answer or update the question using new snapshots and the weekly review.

## From the CLI

List snapshot IDs (to use as `--snapshots`):

```bash
python scripts/add_artifact.py list-snapshots
```

Add a **belief** (thesis or risk):

```bash
python scripts/add_artifact.py belief "MSFT cloud growth will decelerate in FY26."
python scripts/add_artifact.py belief "AWS margins may compress." --snapshots <uuid1> <uuid2>
python scripts/add_artifact.py belief "Downside risk from regulation." --risk
```

Add a **question** (mechanism-driven, snapshot-connected, reviewable):

```bash
python scripts/add_artifact.py question "What leading indicators would suggest AWS growth acceleration in the next quarter?" --snapshots <uuid>
python scripts/add_artifact.py question "What would signal that JPM NIM has peaked?" --snapshots <uuid>
```

After creation, the script prints the new artifact ID and the URL (e.g. `/beliefs/<id>`).
