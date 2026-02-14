# Data Ingestion

## Rule

- **Produces StockSnapshot objects only.** No other artifacts.
- **Never bypasses Phase 1 model.** All data flows through the snapshot schema.
- **Never auto-creates beliefs, proposals, or runs LLM.** Ingestion feeds Phase 1. Nothing else.
- **Snapshots are immutable.** If a snapshot for the same ticker + quarter already exists → skip. Never overwrite.

## Yahoo Finance (yfinance)

- **Source:** Yahoo Finance via `yfinance`. No official API; suitable for personal/local use only.
- **Script:** `scripts/import_snapshots.py`

### Usage

```bash
# Default tickers (MSFT, AMZN, JPM), default quarters (8)
python scripts/import_snapshots.py

# Remove all data (artifacts, lifecycle, proposals) then import default tickers
python scripts/import_snapshots.py --clear

# Specific tickers
python scripts/import_snapshots.py MSFT AAPL GOOGL

# Limit quarters per ticker
python scripts/import_snapshots.py MSFT AMZN -q 4
```

### Behavior

1. Fetches quarterly income statement (Total Revenue, Operating Income, Net Income).
2. Maps to `StockSnapshot`: metadata (deterministic `snapshot_id` from ticker + period), company, market_state, financials, balance_sheet.
3. Saves via `ArtifactRepository.save()`.
4. Skips when a snapshot with the same `snapshot_id` already exists (id is deterministic: `uuid5(namespace, f"{ticker}_{period_end}")`).

### Dependencies

- `yfinance` (in `requirements/base.in`).
- No API key. Free. Local only.
