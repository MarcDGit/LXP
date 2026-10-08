"""Tests for forecasting metrics."""

import polars as pl
import pytest

from lonely_planner.metrics import (
    calculate_cumulative_metrics,
    calculate_lag1_metrics,
    calculate_metrics,
)


def test_calculate_metrics():
    """Test basic MAE%, Bias%, Score calculation."""
    df = pl.DataFrame(
        {
            "actual": [100, 110, 120],
            "forecast": [95, 115, 118],
        }
    )

    metrics = calculate_metrics(df, "actual", "forecast")

    assert "MAE%" in metrics.columns
    assert "Bias%" in metrics.columns
    assert "Score" in metrics.columns

    mae_percent = metrics["MAE%"][0]
    bias_percent = metrics["Bias%"][0]
    score = metrics["Score"][0]

    assert mae_percent == pytest.approx((5 + 5 + 2) / (100 + 110 + 120) * 100, rel=0.01)
    assert bias_percent == pytest.approx((-5 + 5 - 2) / (100 + 110 + 120) * 100, rel=0.01)
    assert score == pytest.approx(mae_percent + abs(bias_percent), rel=0.01)


def test_calculate_metrics_with_grouping():
    """Test metrics calculation with grouping."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P001", "P002", "P002"],
            "actual": [100, 110, 200, 210],
            "forecast": [95, 115, 205, 208],
        }
    )

    metrics = calculate_metrics(df, "actual", "forecast", group_columns=["product_id"])

    assert metrics.shape[0] == 2
    assert "product_id" in metrics.columns


def test_calculate_lag1_metrics():
    """Test lag-1 metrics calculation."""
    df = pl.DataFrame(
        {
            "product_id": ["P001"] * 3,
            "period": ["2023-01", "2023-02", "2023-03"],
            "actual": [100, 110, 120],
            "forecast": [95, 115, 118],
        }
    )

    metrics = calculate_lag1_metrics(df, "actual", "forecast", "period", ["product_id"])

    assert "MAE%" in metrics.columns


def test_calculate_cumulative_metrics():
    """Test cumulative metrics calculation."""
    df = pl.DataFrame(
        {
            "product_id": ["P001"] * 5,
            "period": ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05"],
            "actual": [100, 110, 120, 130, 140],
            "forecast": [95, 115, 118, 132, 138],
        }
    )

    metrics = calculate_cumulative_metrics(
        df, "actual", "forecast", "period", horizon=3, group_columns=["product_id"]
    )

    assert "MAE%" in metrics.columns
