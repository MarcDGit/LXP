"""Forecast Value Added (FVA) analysis."""

import polars as pl

from lonely_planner.metrics import calculate_metrics


def calculate_fva(
    df: pl.DataFrame,
    actual_column: str,
    benchmark_column: str,
    candidate_column: str,
    group_columns: list[str] | None = None,
) -> pl.DataFrame:
    """Calculate Forecast Value Added comparison.

    Compares a candidate forecast against a benchmark (e.g., moving average).

    Args:
        df: DataFrame with actual, benchmark, and candidate forecasts
        actual_column: Name of the actual values column
        benchmark_column: Name of the benchmark forecast column
        candidate_column: Name of the candidate forecast column
        group_columns: Optional list of columns to group by

    Returns:
        DataFrame with FVA comparison table
    """
    benchmark_metrics = calculate_metrics(
        df, actual_column, benchmark_column, group_columns
    )
    benchmark_metrics = benchmark_metrics.rename(
        {
            "MAE%": "benchmark_MAE%",
            "Bias%": "benchmark_Bias%",
            "Score": "benchmark_Score",
        }
    )

    candidate_metrics = calculate_metrics(
        df, actual_column, candidate_column, group_columns
    )
    candidate_metrics = candidate_metrics.rename(
        {
            "MAE%": "candidate_MAE%",
            "Bias%": "candidate_Bias%",
            "Score": "candidate_Score",
        }
    )

    if group_columns:
        fva_table = benchmark_metrics.join(candidate_metrics, on=group_columns)
    else:
        fva_table = benchmark_metrics.hstack(candidate_metrics)

    return fva_table.with_columns(
        [
            (pl.col("benchmark_MAE%") - pl.col("candidate_MAE%")).alias("MAE%_improvement"),
            (pl.col("benchmark_Score") - pl.col("candidate_Score")).alias("Score_improvement"),
        ]
    )
