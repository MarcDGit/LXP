"""Forecasting metrics: MAE%, Bias%, Score."""

import polars as pl


def calculate_metrics(
    df: pl.DataFrame,
    actual_column: str,
    forecast_column: str,
    group_columns: list[str] | None = None,
) -> pl.DataFrame:
    """Calculate MAE%, Bias%, and Score.

    Score = MAE% + |Bias%|

    Args:
        df: DataFrame with actual and forecast columns
        actual_column: Name of the actual values column
        forecast_column: Name of the forecast column
        group_columns: Optional list of columns to group by

    Returns:
        DataFrame with metrics
    """
    df_with_error = df.with_columns(
        (pl.col(forecast_column) - pl.col(actual_column)).alias("error"),
        pl.col(forecast_column).alias("forecast"),
        pl.col(actual_column).alias("actual"),
    )

    if group_columns:
        metrics = df_with_error.group_by(group_columns).agg(
            [
                pl.col("error").abs().sum().alias("sum_abs_error"),
                pl.col("error").sum().alias("sum_error"),
                pl.col("actual").sum().alias("sum_actual"),
            ]
        )
    else:
        metrics = df_with_error.select(
            [
                pl.col("error").abs().sum().alias("sum_abs_error"),
                pl.col("error").sum().alias("sum_error"),
                pl.col("actual").sum().alias("sum_actual"),
            ]
        )

    metrics = metrics.with_columns(
        [
            (pl.col("sum_abs_error") / pl.col("sum_actual") * 100).alias("MAE%"),
            (pl.col("sum_error") / pl.col("sum_actual") * 100).alias("Bias%"),
        ]
    )

    metrics = metrics.with_columns(
        (pl.col("MAE%") + pl.col("Bias%").abs()).alias("Score")
    )

    return metrics.select(
        (group_columns or []) + ["MAE%", "Bias%", "Score"]
    )


def calculate_lag1_metrics(
    df: pl.DataFrame,
    actual_column: str,
    forecast_column: str,
    period_column: str,
    group_columns: list[str] | None = None,
) -> pl.DataFrame:
    """Calculate lag-1 (one-period-ahead) metrics.

    Args:
        df: DataFrame with actual and forecast columns
        actual_column: Name of the actual values column
        forecast_column: Name of the forecast column
        period_column: Name of the period column
        group_columns: Optional list of columns to group by (excluding period)

    Returns:
        DataFrame with lag-1 metrics
    """
    df_sorted = df.sort((group_columns or []) + [period_column])

    return calculate_metrics(df_sorted, actual_column, forecast_column, group_columns)


def calculate_cumulative_metrics(
    df: pl.DataFrame,
    actual_column: str,
    forecast_column: str,
    period_column: str,
    horizon: int,
    group_columns: list[str] | None = None,
) -> pl.DataFrame:
    """Calculate cumulative metrics over a horizon.

    Args:
        df: DataFrame with actual and forecast columns
        actual_column: Name of the actual values column
        forecast_column: Name of the forecast column
        period_column: Name of the period column
        horizon: Number of periods to accumulate
        group_columns: Optional list of columns to group by (excluding period)

    Returns:
        DataFrame with cumulative metrics
    """
    df_sorted = df.sort((group_columns or []) + [period_column])

    if group_columns:
        df_cumsum = df_sorted.with_columns(
            [
                pl.col(actual_column)
                .rolling_sum(window_size=horizon, min_samples=horizon)
                .over(group_columns)
                .alias("cumulative_actual"),
                pl.col(forecast_column)
                .rolling_sum(window_size=horizon, min_samples=horizon)
                .over(group_columns)
                .alias("cumulative_forecast"),
            ]
        )
    else:
        df_cumsum = df_sorted.with_columns(
            [
                pl.col(actual_column)
                .rolling_sum(window_size=horizon, min_samples=horizon)
                .alias("cumulative_actual"),
                pl.col(forecast_column)
                .rolling_sum(window_size=horizon, min_samples=horizon)
                .alias("cumulative_forecast"),
            ]
        )

    df_filtered = df_cumsum.filter(
        pl.col("cumulative_actual").is_not_null()
        & pl.col("cumulative_forecast").is_not_null()
    )

    return calculate_metrics(
        df_filtered, "cumulative_actual", "cumulative_forecast", group_columns
    )
