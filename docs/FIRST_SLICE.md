# Slice 1: Import → MA Benchmark → FVA

This document describes the first deliverable slice of Lonely Planner.

## Scope

Slice 1 provides:

1. **Data import** from CSV and BigQuery (with Parquet caching)
2. **Data cleaning** (dtype validation, null removal, duplicate handling)
3. **Moving average forecasting** as the FVA benchmark
4. **Metrics calculation** (MAE%, Bias%, Score)
5. **FVA comparison** (benchmark vs candidate forecast)
6. **CLI** for running forecasts and exporting results

## What's Included

### Modules

- `io_csv.py` — Load sales history from CSV files
- `io_bq.py` — Load from BigQuery with cost controls and caching
- `clean.py` — Clean data by rule (no statistical outlier trimming)
- `baseline_ma.py` — Moving average forecaster (configurable window)
- `metrics.py` — MAE%, Bias%, Score calculation
- `fva.py` — Forecast Value Added comparison tables
- `export.py` — Export forecasts and metrics to CSV/Parquet
- `cli.py` — Command-line interface

### Data

- `data/sample/sales_history.csv` — Synthetic sample data (2 products × 2 locations × 36 months)
- `data/cache/` — BigQuery Parquet cache (gitignored)
- `data/out/` — Forecast and metric exports (gitignored)

### Documentation

- `README.md` — Project overview, quickstart, process stance
- `docs/METRICS.md` — Metrics glossary (MAE%, Bias%, Score; why not MAPE)
- `docs/FIRST_SLICE.md` — This file

### Tests

Full test coverage with pytest:
- `test_io_csv.py`
- `test_io_bq.py` (mocked, no network/credentials required)
- `test_clean.py`
- `test_baseline_ma.py`
- `test_metrics.py`
- `test_fva.py`

## What's NOT Included (Deferred)

- **Darts forecasting engine** — Next slice (statistical and ML models)
- **Weighted errors by value/volume** — API stubbed, implementation next
- **Demand drivers** (promotions, prices, shortages) — Later
- **Streamlit UI** — Later
- **DuckDB over Parquet** — Later
- **Multi-step FVA** (engine → planner → consensus) — Later

## Design Decisions

### Polars Only

The package code uses **Polars** exclusively (no pandas imports). This keeps dependencies light and leverages Polars' performance and ergonomics for data pipelines.

### BigQuery as Optional Dependency

BigQuery support is an optional extra (`pip install lonely-planner[bigquery]`) so users who only need CSV imports don't install the heavy `google-cloud-bigquery` SDK.

### Caching Strategy

BigQuery results are cached as Parquet files keyed by query fingerprint (SHA256). This:
- Avoids repeated billing for the same query
- Enables offline work after initial pull
- Speeds up iteration during development

Use `--refresh` to bypass cache.

### Cleaning by Rule, Not by Statistics

The `clean_data` module removes erroneous rows by rule:
- Null values in grain or value columns
- Negative quantities (if demand cannot be negative)
- Duplicate grain combinations (keeping last)

It does **NOT** trim outliers by standard deviation or z-score. SupChains best practice is to clean bad transactions and feed drivers (promotions, shortages) to the model, not to remove legitimate high-demand periods.

### Moving Average as FVA Benchmark

Following SupChains guidance, the **moving average** is the recommended statistical benchmark for Forecast Value Added (FVA) analysis. Any forecast method (human adjustments, statistical models, ML engines) should be measured against this baseline.

The default window is **12 periods** (configurable). For monthly data, this is a 12-month moving average.

## CLI Examples

See `README.md` for full CLI usage.

### CSV Forecast

```bash
lonely forecast-csv data/sample/sales_history.csv
```

### FVA Comparison

Compare 12-period MA (benchmark) vs 6-period MA (candidate):

```bash
lonely forecast-csv data/sample/sales_history.csv --ma-window 12 --candidate-window 6
```

### BigQuery Forecast

```bash
lonely forecast-bigquery "SELECT product_id, location_id, period, quantity FROM \`project.dataset.table\` WHERE period >= '2023-01-01'"
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

All tests pass without network access or credentials. BigQuery tests are fully mocked.

## Next Steps

The next slice will add:

1. **Darts integration** for local/global statistical and ML models
2. **Multi-model FVA** comparing automated engines
3. **Weighted error metrics** by value/volume
4. **Cumulative accuracy over risk horizon** (scaffolded in slice 1)

Following slices will add demand drivers, enrichment UI, and scenario planning.
