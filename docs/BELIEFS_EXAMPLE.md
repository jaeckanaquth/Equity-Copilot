# Example: Adding Beliefs (Markdown Format)

Use this file as a template to draft beliefs in markdown, then add them via the **UI** ([/beliefs/new](http://localhost:8000/beliefs/new)) or the **CLI** (`scripts/add_artifact.py`). For bulk add by ticker, you can follow the pattern in `scripts/seed_beliefs.py`.

---

## Format for one belief

```markdown
**Company / label** (Thesis | Risk)

Statement text here.

- **Tickers:** MSFT (or MSFT, AMZN for comparative)
- **Why:** One line on how snapshots will reinforce or create tension.
```

- **Thesis** = investment view you’re taking.
- **Risk** = downside you’re tracking (check “Treat as risk” in the UI or use `--risk` in CLI).

---

## Example set (copy and adapt)

### Microsoft (MSFT)

**Belief 1 — Margin-sensitive (Thesis)**  
Azure-led revenue mix will support operating margin expansion over the next two quarters.

- **Tickers:** MSFT  
- **Why:** If revenue grows but margin flat → tension. If margin expands → reinforced. If margin compresses → strong tension.

**Belief 2 — Capex risk (Risk)**  
AI-related infrastructure investment will not materially compress free cash flow in FY25.

- **Tickers:** MSFT  
- **Why:** Snapshot shows revenue and operating income. If income lags revenue → tension.

**Belief 3 — Stability thesis (Thesis)**  
Microsoft's enterprise demand remains structurally resilient despite macro uncertainty.

- **Tickers:** MSFT  
- **Why:** If revenue decelerates sharply → tension. If margins hold → partially reinforced.

---

### Amazon (AMZN)

**Belief 1 — AWS-driven margin (Thesis)**  
AWS growth stabilization will drive consolidated operating margin expansion.

- **Tickers:** AMZN  

**Belief 2 — Retail risk (Risk)**  
Retail operating income remains vulnerable to demand normalization.

- **Tickers:** AMZN  

**Belief 3 — Mixed structural (Thesis)**  
Amazon's profitability trajectory is increasingly dependent on AWS rather than retail recovery.

- **Tickers:** AMZN  

---

### JPMorgan (JPM)

**Belief 1 — Rate cycle (Thesis)**  
Net interest margin has peaked and will compress as rates stabilize.

- **Tickers:** JPM  

**Belief 2 — Credit risk containment (Risk)**  
Credit costs will remain contained despite macro slowdown risk.

- **Tickers:** JPM  

**Belief 3 — Revenue mix stability (Thesis)**  
Trading and fee income will not materially offset potential NIM compression.

- **Tickers:** JPM  

---

### Comparative (multi-ticker)

**MSFT vs AMZN (stability)**  
Microsoft's cloud margin profile is structurally more stable than Amazon's.

- **Tickers:** MSFT, AMZN  

**MSFT vs AMZN (growth)**  
AWS revenue growth will outpace Azure growth over the next two quarters.

- **Tickers:** MSFT, AMZN  

**JPM vs Tech**  
JPMorgan earnings volatility is lower than large-cap tech peers in this cycle.

- **Tickers:** JPM, MSFT, AMZN  

---

## How to add next time

**Option A — UI**

1. Go to [Weekly Review](/weekly-review) → **Add belief** (or **Add question**).
2. Paste the **statement**.
3. Check **Treat as risk** only for risks.
4. Use **Add all &lt;TICKER&gt;** to attach all snapshots for that company (or pick specific snapshots).

**Option B — CLI (single belief)**

```bash
conda activate snow
python scripts/add_artifact.py list-snapshots   # get UUIDs if you want specific snapshots
python scripts/add_artifact.py belief "Your statement here."
python scripts/add_artifact.py belief "This is a risk." --risk
python scripts/add_artifact.py belief "With refs." --snapshots <uuid1> <uuid2>
```

**Option C — Bulk (many beliefs with “all snapshots per ticker”)**

1. Copy the format from `scripts/seed_beliefs.py`: list of `(statement, risk, ["TICKER1", "TICKER2"])`.
2. Append your new rows to the `BELIEFS` list.
3. Run: `python scripts/seed_beliefs.py`.

Note: Running `seed_beliefs.py` as-is will **create duplicates** of the existing 12 beliefs. To only add new ones, either add a new script (e.g. `scripts/seed_beliefs_extra.py`) with just the new entries, or add a “skip if statement already exists” check in the script.
