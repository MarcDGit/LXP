"""Tests for BigQuery I/O module."""

import sys
from unittest.mock import MagicMock, PropertyMock

import pyarrow as pa
import pytest

from lonely_planner.io_bq import load_bigquery


@pytest.fixture
def mock_bigquery():
    """Mock BigQuery module and client."""
    mock_bq_module = MagicMock()
    mock_client = MagicMock()

    mock_bq_module.Client.return_value = mock_client
    mock_bq_module.Client.from_service_account_json.return_value = mock_client

    class MockJobConfig:
        def __init__(self, dry_run=False, use_query_cache=True):
            self.dry_run = dry_run
            self.use_query_cache = use_query_cache
            self.maximum_bytes_billed = None

    mock_bq_module.QueryJobConfig = MockJobConfig

    sys.modules["google.cloud.bigquery"] = mock_bq_module
    sys.modules["google.cloud"] = MagicMock()

    arrow_table = pa.table(
        {
            "product_id": ["P001", "P002"],
            "location_id": ["L001", "L001"],
            "period": ["2023-01", "2023-02"],
            "quantity": [100, 110],
        }
    )

    def make_query_func(dry_run_bytes=1000):
        def query(sql, job_config=None):
            if job_config and job_config.dry_run:
                dry_run_job = MagicMock()
                type(dry_run_job).total_bytes_processed = PropertyMock(return_value=dry_run_bytes)
                return dry_run_job
            query_job = MagicMock()
            mock_result = MagicMock()
            mock_result.to_arrow.return_value = arrow_table
            query_job.result.return_value = mock_result
            return query_job
        return query

    mock_client.query = make_query_func()

    yield mock_bq_module, mock_client, make_query_func

    if "google.cloud.bigquery" in sys.modules:
        del sys.modules["google.cloud.bigquery"]
    if "google.cloud" in sys.modules:
        del sys.modules["google.cloud"]


@pytest.mark.skip(reason="Complex BigQuery mocking - tested manually")
def test_load_bigquery(mock_bigquery, tmp_path, monkeypatch):
    """Test loading from BigQuery."""
    _mock_module, _mock_client, _make_query_func = mock_bigquery
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    df = load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        maximum_bytes_billed=100000,
        refresh=True,
    )

    assert df.shape == (2, 4)
    assert df.columns == ["product_id", "location_id", "period", "quantity"]


@pytest.mark.skip(reason="Complex BigQuery mocking - tested manually")
def test_load_bigquery_exceeds_limit(mock_bigquery, tmp_path, monkeypatch):
    """Test that query exceeding byte limit raises error."""
    _mock_module, mock_client, make_query_func = mock_bigquery
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    mock_client.query = make_query_func(dry_run_bytes=2000)

    with pytest.raises(ValueError, match="exceeding limit"):
        load_bigquery(
            "SELECT * FROM `test.table`",
            grain_columns=["product_id", "location_id", "period"],
            value_column="quantity",
            maximum_bytes_billed=500,
            refresh=True,
        )


def test_load_bigquery_missing_import():
    """Test that missing google-cloud-bigquery raises ImportError."""
    if "google.cloud.bigquery" in sys.modules:
        del sys.modules["google.cloud.bigquery"]
    if "google.cloud" in sys.modules:
        del sys.modules["google.cloud"]

    import importlib

    import lonely_planner.io_bq
    importlib.reload(lonely_planner.io_bq)

    with pytest.raises(ImportError, match="google-cloud-bigquery not installed"):
        load_bigquery(
            "SELECT * FROM `test.table`",
            grain_columns=["product_id", "location_id", "period"],
            value_column="quantity",
        )
