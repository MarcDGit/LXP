"""Tests for data cleaning module."""

import polars as pl

from lonely_planner.clean import clean_data


def test_clean_data_removes_nulls():
    """Test that null values are removed."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P002", None],
            "location_id": ["L001", "L001", "L001"],
            "period": ["2023-01", "2023-02", "2023-03"],
            "quantity": [100, None, 150],
        }
    )

    cleaned = clean_data(df, ["product_id", "location_id", "period"], "quantity")

    assert cleaned.shape[0] == 1
    assert cleaned["product_id"][0] == "P001"


def test_clean_data_removes_negative_values():
    """Test that negative values are removed."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P002", "P003"],
            "location_id": ["L001", "L001", "L001"],
            "period": ["2023-01", "2023-02", "2023-03"],
            "quantity": [100, -50, 150],
        }
    )

    cleaned = clean_data(df, ["product_id", "location_id", "period"], "quantity")

    assert cleaned.shape[0] == 2
    assert -50 not in cleaned["quantity"]


def test_clean_data_removes_duplicates():
    """Test that duplicate grain combinations are removed (keeping last)."""
    df = pl.DataFrame(
        {
            "product_id": ["P001", "P001"],
            "location_id": ["L001", "L001"],
            "period": ["2023-01", "2023-01"],
            "quantity": [100, 120],
        }
    )

    cleaned = clean_data(df, ["product_id", "location_id", "period"], "quantity")

    assert cleaned.shape[0] == 1
    assert cleaned["quantity"][0] == 120
