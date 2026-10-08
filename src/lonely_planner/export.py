"""Export module for forecasts and metrics."""

from pathlib import Path

import polars as pl

from lonely_planner.config import OUTPUT_DIR


def export_csv(df: pl.DataFrame, filename: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Export DataFrame to CSV.

    Args:
        df: DataFrame to export
        filename: Output filename
        output_dir: Output directory (default: data/out/)

    Returns:
        Path to exported file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    df.write_csv(output_path)
    return output_path


def export_parquet(df: pl.DataFrame, filename: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Export DataFrame to Parquet.

    Args:
        df: DataFrame to export
        filename: Output filename
        output_dir: Output directory (default: data/out/)

    Returns:
        Path to exported file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    df.write_parquet(output_path)
    return output_path
