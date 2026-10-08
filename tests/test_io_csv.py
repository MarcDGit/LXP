"""Tests for CSV I/O module."""


import pytest

from lonely_planner.io_csv import load_csv


def test_load_csv(tmp_path):
    """Test loading CSV with valid columns."""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "product_id,location_id,period,quantity\n"
        "P001,L001,2023-01,100\n"
        "P001,L001,2023-02,120\n"
    )

    df = load_csv(
        csv_path,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
    )

    assert df.shape == (2, 4)
    assert df.columns == ["product_id", "location_id", "period", "quantity"]


def test_load_csv_missing_columns(tmp_path):
    """Test loading CSV with missing required columns."""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "product_id,location_id,quantity\n"
        "P001,L001,100\n"
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        load_csv(
            csv_path,
            grain_columns=["product_id", "location_id", "period"],
            value_column="quantity",
        )
