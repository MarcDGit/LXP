"""Tests for FVA analysis."""

import polars as pl

from lonely_planner.fva import calculate_fva


def test_calculate_fva():
    """Test FVA calculation comparing benchmark and candidate."""
    df = pl.DataFrame(
        {
            "actual": [100, 110, 120],
            "benchmark": [95, 115, 118],
            "candidate": [98, 112, 119],
        }
    )

    fva_table = calculate_fva(df, "actual", "benchmark", "candidate")

    assert "benchmark_MAE%" in fva_table.columns
    assert "candidate_MAE%" in fva_table.columns
    assert "MAE%_improvement" in fva_table.columns
    assert "Score_improvement" in fva_table.columns


def test_calculate_fva_with_grouping():
    """Test FVA with grouping."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P001", "P002", "P002"],
            "actual": [100, 110, 200, 210],
            "benchmark": [95, 115, 205, 208],
            "candidate": [98, 112, 202, 211],
        }
    )

    fva_table = calculate_fva(df, "actual", "benchmark", "candidate", ["product_id"])

    assert fva_table.shape[0] == 2
    assert "product_id" in fva_table.columns
