# Lonely Planner

**Local-first demand planning toolkit for individual planners**

Lonely Planner is a Python toolkit for solo demand planners who need faster, more auditable forecasts than Excel can provide, without the overhead of enterprise S&OP suites. It implements forecasting best practices from [SupChains](https://supchains.com) / Nicolas Vandeput.

## Who It's For

- **Individual demand planners** working at scale (thousands of SKU × location combinations)
- **S&OP analysts** who want local-first tooling with transparent, reproducible pipelines
- **Supply chain data scientists** prototyping forecast engines and FVA workflows

If you're drowning in Excel tabs, fighting with pivot tables, or manually copying forecasts between systems, this toolkit is for you.

## What It Does (Slice 1)

1. **Import** sales history from CSV or BigQuery (with Parquet caching)
2. **Clean** data by rule (validate grain, remove nulls, drop duplicates)
3. **Forecast** with a configurable moving average (the FVA benchmark)
4. **Score** forecasts with **MAE%**, **Bias%**, and **Score** (not MAPE)
5. **Compare** forecast methods with **Forecast Value Added (FVA)** tables
6. **Export** forecasts and metrics to CSV/Parquet

## Process Stance

Lonely Planner follows SupChains best practices for demand planning:

### Forecast Unconstrained Demand

Forecast what customers will **request**, not what you can supply. Supply constraints (capacity, inventory) are inputs to supply planning, not to demand forecasting. Mixing demand and supply into one number produces poor decisions.

### Budgets Follow Forecasts

The demand forecast is the best unbiased estimate of future demand. If it doesn't match the budget, that's an early warning to act on (adjust budgets, change supply plans, or revisit assumptions). Never edit the forecast to match the budget.

### FVA vs Moving Average

Every forecast method (human adjustments, statistical models, ML engines) should be measured against a **simple moving average benchmark**. If your fancy model doesn't beat a 12-month moving average, it's not adding value.

This is **Forecast Value Added (FVA)**: measure the accuracy added — or destroyed — by every step in your process.

### Why Not MAPE?

**MAPE (Mean Absolute Percentage Error)** is not implemented in Lonely Planner.

**Problems with MAPE:**
- Undefined for zero actuals
- Asymmetric (over-forecasts and under-forecasts penalized differently)
- Biased toward under-forecasting
- Extreme values from small actuals dominate the metric

**Better alternatives:** MAE% (weighted by total demand) and weighted MAE (by value/volume).

See `docs/METRICS.md` for full details.

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/MarcDGit/LXP.git
cd LXP

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Optional: Install with BigQuery support
pip install -e ".[bigquery]"

# Optional: Install development dependencies (tests, linting)
pip install -e ".[dev]"
```

### Quick Demo (CSV)

Run a forecast on the sample data:

```bash
lonely forecast-csv data/sample/sales_history.csv
```

This generates:
- `data/out/forecast_ma.csv` — Forecast with 12-month moving average
- `data/out/metrics_ma.csv` — MAE%, Bias%, Score by product × location

### FVA Comparison

Compare 12-month MA (benchmark) vs 6-month MA (candidate):

```bash
lonely forecast-csv data/sample/sales_history.csv --ma-window 12 --candidate-window 6
```

This adds:
- `data/out/fva_comparison.csv` — FVA table showing which method adds value

## BigQuery Setup

### Authentication

Lonely Planner uses **Application Default Credentials (ADC)** for BigQuery access.

```bash
# Install gcloud SDK, then authenticate
gcloud auth application-default login
```

For service accounts, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**Never commit service account keys to git.** They are already in `.gitignore`.

### Cost Controls

BigQuery queries are **dry-run** before execution to estimate bytes processed. The default limit is **1 GB (1,000,000,000 bytes)**. Queries exceeding this limit will fail unless you override with `--max-bytes`.

```bash
lonely forecast-bigquery "SELECT ..." --max-bytes 5000000000  # 5 GB
```

### Caching

BigQuery results are cached as Parquet files in `data/cache/` (keyed by query fingerprint). Re-running the same query hits the cache instead of BigQuery.

Use `--refresh` to bypass the cache:

```bash
lonely forecast-bigquery "SELECT ..." --refresh
```

### Example Query

```bash
lonely forecast-bigquery "
  SELECT 
    product_id, 
    location_id, 
    FORMAT_DATE('%Y-%m', order_date) AS period,
    SUM(quantity) AS quantity
  FROM \`your-project.your-dataset.sales\`
  WHERE order_date >= '2023-01-01'
  GROUP BY product_id, location_id, period
  ORDER BY product_id, location_id, period
"
```

## Project Layout

```
LXP/
├── src/lonely_planner/       # Package source
│   ├── io_csv.py             # CSV import
│   ├── io_bq.py              # BigQuery import with caching
│   ├── clean.py              # Data cleaning (by rule, not statistics)
│   ├── baseline_ma.py        # Moving average forecaster
│   ├── metrics.py            # MAE%, Bias%, Score
│   ├── fva.py                # Forecast Value Added comparison
│   ├── export.py             # CSV/Parquet export
│   └── cli.py                # Command-line interface
├── tests/                    # pytest test suite
├── data/
│   ├── sample/               # Sample CSV data
│   ├── cache/                # BigQuery Parquet cache (gitignored)
│   └── out/                  # Forecast exports (gitignored)
├── docs/
│   ├── FIRST_SLICE.md        # Slice 1 deliverables
│   └── METRICS.md            # Metrics glossary
├── pyproject.toml            # Package metadata
└── README.md                 # This file
```

## CLI Reference

### `lonely forecast-csv`

Generate forecast from CSV file.

**Arguments:**
- `INPUT_PATH` — Path to CSV file

**Options:**
- `--grain-columns` — Comma-separated grain columns (default: `product_id,location_id,period`)
- `--value-column` — Value column name (default: `quantity`)
- `--period-column` — Period/date column name (default: `period`)
- `--ma-window` — Moving average window (default: `12`)
- `--candidate-window` — Second MA window for FVA comparison (optional)

**Example:**

```bash
lonely forecast-csv data/sample/sales_history.csv --ma-window 12 --candidate-window 6
```

### `lonely forecast-bigquery`

Generate forecast from BigQuery.

**Arguments:**
- `QUERY` — SQL query to execute

**Options:**
- `--grain-columns` — Comma-separated grain columns (default: `product_id,location_id,period`)
- `--value-column` — Value column name (default: `quantity`)
- `--period-column` — Period/date column name (default: `period`)
- `--ma-window` — Moving average window (default: `12`)
- `--max-bytes` — Maximum bytes to bill (default: `1000000000` = 1 GB)
- `--refresh` — Bypass cache and refresh data

**Example:**

```bash
lonely forecast-bigquery "SELECT product_id, location_id, period, quantity FROM \`project.dataset.table\`" --refresh
```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests pass without network access or credentials. BigQuery tests are fully mocked.

### Code Quality

```bash
ruff check .
```

## Non-Goals (For Now)

Lonely Planner **does not** (yet):

- Provide a multi-user cloud SaaS platform
- Write forecasts back to ERP systems
- Support per-SKU manual model selection (ABC-to-choose-model)
- Implement MAPE dashboards
- Optimize inventory or safety stocks (planned for later)
- Include deep learning models (Darts hybrid coming next)

These may come later, but slice 1 focuses on the core loop: import → clean → baseline → score → export.

## Roadmap

**Next slices:**

1. **Darts forecasting engine** — Local/global statistical and ML models
2. **Weighted error metrics** — By value/volume, not just by count
3. **Cumulative accuracy over risk horizon** — Not just lag-1
4. **Demand drivers** — Promotions, prices, shortages, sell-out
5. **Streamlit UI** — Interactive forecast review and enrichment
6. **DuckDB over Parquet** — SQL-based analytics on local data lake

## References

- **SupChains / Nicolas Vandeput**  
  [supchains.com](https://supchains.com) | [Books](https://supchains.com/books/) | [VN1 Competition](https://www.kaggle.com/competitions/vandeput-forecasting-2024)

- **Key Articles**  
  - [Forecast Value Added (FVA)](https://medium.com/supchains)
  - [Why Not MAPE?](https://medium.com/supchains)
  - [Outlier Detection Best Practices](https://medium.com/supchains)
  - [Setting Forecast Accuracy Targets](https://medium.com/supchains)

- **Books**  
  - *Data Science for Supply Chain Forecasting* (2nd ed. 2021)
  - *Inventory Optimization: Models and Simulations* (2nd ed. 2023)
  - *Demand Forecasting Best Practices* (2023)

## License

MIT License. Copyright (c) 2026 Marc Dommach.

See `LICENSE` for full text.

## Questions?

This is a personal toolkit. If you find it useful, feel free to clone and adapt it for your own planning workflows.

For questions about the SupChains methodology, see [supchains.com/lets-talk](https://supchains.com/lets-talk/).
