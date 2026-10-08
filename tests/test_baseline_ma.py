"""Tests for moving average forecasting."""

import polars as pl

from lonely_planner.baseline_ma import forecast_moving_average


def test_forecast_moving_average():
    """Test basic moving average forecast."""
    df = pl.DataFrame(
        {
            "product_id": ["P001"] * 5,
            "location_id": ["L001"] * 5,
            "period": ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05"],
            "quantity": [100, 110, 120, 130, 140],
        }
    )

    result = forecast_moving_average(
        df,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        period_column="period",
        window=3,
    )

    assert "forecast_ma" in result.columns
    assert result.shape[0] == 4


def test_forecast_moving_average_multiple_groups():
    """Test moving average with multiple product-location groups."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P001", "P001", "P002", "P002", "P002"],
            "location_id": ["L001", "L001", "L001", "L001", "L001", "L001"],
            "period": ["2023-01", "2023-02", "2023-03", "2023-01", "2023-02", "2023-03"],
            "quantity": [100, 110, 120, 200, 210, 220],
        }
    )

    result = forecast_moving_average(
        df,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        period_column="period",
        window=2,
    )

    assert result.shape[0] == 4
    p001_forecast = result.filter(pl.col("product_id") == "P001")
    assert p001_forecast.shape[0] == 2
