"""CSV import module."""

from pathlib import Path

import polars as pl


def load_csv(
    path: Path | str,
    grain_columns: list[str],
    value_column: str,
) -> pl.DataFrame:
    """Load sales history from CSV.

    Args:
        path: Path to CSV file
        grain_columns: List of grain column names (e.g., product_id, location_id, period)
        value_column: Name of the value column (e.g., quantity)

    Returns:
        Polars DataFrame with validated columns
    """
    df = pl.read_csv(path)

    required_columns = grain_columns + [value_column]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        msg = f"Missing required columns: {missing_columns}"
        raise ValueError(msg)

    return df.select(required_columns)
