"""Data cleaning and validation module."""

import polars as pl


def clean_data(
    df: pl.DataFrame,
    grain_columns: list[str],
    value_column: str,
) -> pl.DataFrame:
    """Clean and validate sales history data.

    Validates dtypes and grain, removes erroneous rows by rule.
    Does NOT trim outliers based on statistical deviation.

    Args:
        df: Input DataFrame
        grain_columns: List of grain column names
        value_column: Name of the value column

    Returns:
        Cleaned DataFrame
    """
    cleaned = df.clone()

    cleaned = cleaned.drop_nulls(subset=grain_columns + [value_column])

    if cleaned[value_column].dtype not in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]:
        try:
            cleaned = cleaned.with_columns(pl.col(value_column).cast(pl.Float64))
        except Exception as exc:
            msg = f"Cannot cast {value_column} to numeric type"
            raise ValueError(msg) from exc

    cleaned = cleaned.filter(pl.col(value_column) >= 0)

    return cleaned.unique(subset=grain_columns, keep="last")
