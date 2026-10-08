"""Command-line interface for Lonely Planner."""

import click

from lonely_planner.baseline_ma import forecast_moving_average
from lonely_planner.clean import clean_data
from lonely_planner.config import (
    DEFAULT_GRAIN_COLUMNS,
    DEFAULT_MA_WINDOW,
    DEFAULT_MAXIMUM_BYTES_BILLED,
    DEFAULT_VALUE_COLUMN,
)
from lonely_planner.export import export_csv
from lonely_planner.fva import calculate_fva
from lonely_planner.io_bq import load_bigquery
from lonely_planner.io_csv import load_csv
from lonely_planner.metrics import calculate_lag1_metrics


@click.group()
@click.version_option()
def cli():
    """Lonely Planner: Local-first demand planning toolkit."""


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--grain-columns",
    default=",".join(DEFAULT_GRAIN_COLUMNS),
    help="Comma-separated list of grain column names",
)
@click.option(
    "--value-column",
    default=DEFAULT_VALUE_COLUMN,
    help="Name of the value column",
)
@click.option(
    "--period-column",
    default="period",
    help="Name of the period/date column",
)
@click.option(
    "--ma-window",
    default=DEFAULT_MA_WINDOW,
    type=int,
    help="Moving average window size",
)
@click.option(
    "--candidate-window",
    type=int,
    help="Second MA window for candidate forecast (for FVA comparison)",
)
def forecast_csv(
    input_path: str,
    grain_columns: str,
    value_column: str,
    period_column: str,
    ma_window: int,
    candidate_window: int | None,
):
    """Generate forecast from CSV file."""
    grain_cols = [col.strip() for col in grain_columns.split(",")]
    group_cols = [col for col in grain_cols if col != period_column]

    click.echo(f"Loading data from {input_path}...")
    df = load_csv(input_path, grain_cols, value_column)

    click.echo("Cleaning data...")
    df_clean = clean_data(df, grain_cols, value_column)

    click.echo(f"Generating {ma_window}-period moving average forecast...")
    df_forecast = forecast_moving_average(
        df_clean, grain_cols, value_column, period_column, window=ma_window
    )

    click.echo("Calculating metrics...")
    metrics = calculate_lag1_metrics(
        df_forecast, value_column, "forecast_ma", period_column, group_cols or None
    )

    click.echo("\n=== Benchmark MA Metrics (Lag-1) ===")
    click.echo(metrics)

    export_csv(df_forecast, "forecast_ma.csv")
    export_csv(metrics, "metrics_ma.csv")
    click.echo("\nExported: data/out/forecast_ma.csv, data/out/metrics_ma.csv")

    if candidate_window:
        click.echo(f"\nGenerating {candidate_window}-period candidate MA forecast...")
        df_candidate = forecast_moving_average(
            df_clean, grain_cols, value_column, period_column, window=candidate_window
        )

        df_comparison = df_forecast.join(
            df_candidate.select(grain_cols + ["forecast_ma"]),
            on=grain_cols,
            suffix="_candidate",
        )

        click.echo("Calculating FVA...")
        fva_table = calculate_fva(
            df_comparison,
            value_column,
            "forecast_ma",
            "forecast_ma_candidate",
            group_cols or None,
        )

        click.echo("\n=== FVA: Benchmark vs Candidate ===")
        click.echo(fva_table)

        export_csv(fva_table, "fva_comparison.csv")
        click.echo("\nExported: data/out/fva_comparison.csv")


@cli.command()
@click.argument("query")
@click.option(
    "--grain-columns",
    default=",".join(DEFAULT_GRAIN_COLUMNS),
    help="Comma-separated list of grain column names",
)
@click.option(
    "--value-column",
    default=DEFAULT_VALUE_COLUMN,
    help="Name of the value column",
)
@click.option(
    "--period-column",
    default="period",
    help="Name of the period/date column",
)
@click.option(
    "--ma-window",
    default=DEFAULT_MA_WINDOW,
    type=int,
    help="Moving average window size",
)
@click.option(
    "--max-bytes",
    default=DEFAULT_MAXIMUM_BYTES_BILLED,
    type=int,
    help="Maximum bytes to bill",
)
@click.option(
    "--refresh",
    is_flag=True,
    help="Bypass cache and refresh data",
)
def forecast_bigquery(
    query: str,
    grain_columns: str,
    value_column: str,
    period_column: str,
    ma_window: int,
    max_bytes: int,
    refresh: bool,
):
    """Generate forecast from BigQuery."""
    grain_cols = [col.strip() for col in grain_columns.split(",")]
    group_cols = [col for col in grain_cols if col != period_column]

    click.echo("Loading data from BigQuery...")
    df = load_bigquery(query, grain_cols, value_column, max_bytes, refresh)

    click.echo("Cleaning data...")
    df_clean = clean_data(df, grain_cols, value_column)

    click.echo(f"Generating {ma_window}-period moving average forecast...")
    df_forecast = forecast_moving_average(
        df_clean, grain_cols, value_column, period_column, window=ma_window
    )

    click.echo("Calculating metrics...")
    metrics = calculate_lag1_metrics(
        df_forecast, value_column, "forecast_ma", period_column, group_cols or None
    )

    click.echo("\n=== Benchmark MA Metrics (Lag-1) ===")
    click.echo(metrics)

    export_csv(df_forecast, "forecast_bq.csv")
    export_csv(metrics, "metrics_bq.csv")
    click.echo("\nExported: data/out/forecast_bq.csv, data/out/metrics_bq.csv")


if __name__ == "__main__":
    cli()
