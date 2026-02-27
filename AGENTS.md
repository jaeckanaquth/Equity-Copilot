# Equity Copilot

Local-first equity research app (FastAPI + SQLite + Jinja2 templates). See `README.md` for main entry points and usage.

## Cursor Cloud specific instructions

### Services

| Service | How to run | Notes |
|---------|-----------|-------|
| FastAPI web app | `conda activate snow && uvicorn main:app --reload` | Serves on port 8000. Auto-creates SQLite DB (`equity_copilot.db`) on startup via `init_db()`. |
| Ollama (optional) | `ollama serve` | Only needed for LLM-assisted features (drafting, delta analysis). App works fully without it—LLM endpoints return 503. |

### Key caveats

- **Missing runtime deps**: `requirements/base.txt` is compiled from `base.in` but does not include `sqlalchemy`, `uvicorn`, or `python-multipart`, which are required at runtime. Install them alongside the requirements file: `pip install -r requirements/base.txt sqlalchemy uvicorn python-multipart`.
- **Test deps**: `pytest` and `httpx` are needed for the test suite but are not listed in requirements. Install with: `pip install pytest httpx`.
- **Lint**: No project-level lint config exists. Use `ruff check .` for a quick lint pass. Pre-existing warnings (unused imports, E402) are in the codebase.
- **Tests**: `pytest tests/ -v` — all tests use in-memory SQLite, no external services required.
- **Conda env**: The project expects a conda env named `snow` with Python 3.12. Always run `conda activate snow` before executing commands.
- **Database**: SQLite file-based at `equity_copilot.db` in the project root. Created automatically on first app startup. Delete the file to reset.
- **Data import**: `python scripts/import_snapshots.py AAPL MSFT ...` fetches Yahoo Finance data (requires internet). Optional—the app runs without snapshot data.
