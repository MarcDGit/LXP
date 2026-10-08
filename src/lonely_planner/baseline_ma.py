"""Moving average baseline forecaster."""

import polars as pl


def forecast_moving_average(
    df: pl.DataFrame,
    grain_columns: list[str],
    value_column: str,
    period_column: str,
    window: int = 12,
) -> pl.DataFrame:
    """Generate moving average forecast.

    Args:
        df: Input DataFrame with historical data
        grain_columns: List of grain column names (e.g., product_id, location_id)
        value_column: Name of the value column
        period_column: Name of the period/date column
        window: Number of periods for moving average

    Returns:
        DataFrame with forecast column added
    """
    group_columns = [col for col in grain_columns if col != period_column]

    if not group_columns:
        df_sorted = df.sort(period_column)
        result = df_sorted.with_columns(
            pl.col(value_column)
            .rolling_mean(window_size=window, min_samples=1)
            .shift(1)
            .alias("forecast_ma")
        )
    else:
        df_sorted = df.sort(group_columns + [period_column])
        result = df_sorted.with_columns(
            pl.col(value_column)
            .rolling_mean(window_size=window, min_samples=1)
            .shift(1)
            .over(group_columns)
            .alias("forecast_ma")
        )

    return result.filter(pl.col("forecast_ma").is_not_null())
