# Adding Beliefs and Questions

## From the app

1. Open **Weekly Review** (`/weekly-review`).
2. Click **Add belief or question** (or go to `/create`).
3. Use one of the two forms:
   - **Add belief:** Enter the statement, optionally check “Treat as risk”, optionally select reference snapshots. Submit → you are redirected to the new belief page.
   - **Add question:** Enter the question, optionally select reference snapshots. Submit → you are redirected to the new question page.

Reference snapshots link the artifact to specific data (e.g. MSFT 2025-12-31). They are used for coverage, “beliefs needing review”, and LLM context.

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

Add a **question**:

```bash
python scripts/add_artifact.py question "What is the margin trajectory for AWS?"
python scripts/add_artifact.py question "How does JPM NIM trend?" --snapshots <uuid>
```

After creation, the script prints the new artifact ID and the URL (e.g. `/beliefs/<id>`).
