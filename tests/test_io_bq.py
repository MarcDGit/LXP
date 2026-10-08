"""Tests for BigQuery I/O module."""

import sys
from unittest.mock import MagicMock, PropertyMock

import polars as pl
import pyarrow as pa
import pytest

from lonely_planner.io_bq import load_bigquery


@pytest.fixture
def mock_bigquery_module():
    """Mock the google.cloud.bigquery module."""

    class MockJobConfig:
        def __init__(self, dry_run=False, use_query_cache=True):
            self.dry_run = dry_run
            self.use_query_cache = use_query_cache
            self.maximum_bytes_billed = None

    from types import ModuleType

    mock_bq = ModuleType("google.cloud.bigquery")
    mock_bq.QueryJobConfig = MockJobConfig
    mock_bq.Client = MagicMock

    sys.modules["google.cloud.bigquery"] = mock_bq
    sys.modules["google.cloud"] = ModuleType("google.cloud")

    yield mock_bq

    if "google.cloud.bigquery" in sys.modules:
        del sys.modules["google.cloud.bigquery"]
    if "google.cloud" in sys.modules:
        del sys.modules["google.cloud"]


@pytest.fixture
def sample_arrow_table():
    """Create a sample Arrow table for testing."""
    return pa.table(
        {
            "product_id": ["P001", "P002"],
            "location_id": ["L001", "L001"],
            "period": ["2023-01", "2023-02"],
            "quantity": [100, 110],
        }
    )


@pytest.fixture
def mock_client(sample_arrow_table):
    """Create a mock BigQuery client."""

    class MockJob:
        def __init__(self, is_dry_run, arrow_table):
            self.total_bytes_processed = 1000
            self.is_dry_run = is_dry_run
            self.arrow_table = arrow_table

        def result(self):
            if not self.is_dry_run:
                return MockResult(self.arrow_table)
            return None

    class MockResult:
        def __init__(self, arrow_table):
            self.arrow_table = arrow_table

        def to_arrow(self):
            return self.arrow_table

    client = MagicMock()

    def query_side_effect(sql, job_config=None):
        is_dry_run = bool(job_config and getattr(job_config, 'dry_run', False))
        return MockJob(is_dry_run, sample_arrow_table)

    client.query = MagicMock(side_effect=query_side_effect)
    return client


def test_dry_run_executed_first(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that dry-run is executed first and estimated bytes are read."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    df = load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    assert mock_client.query.call_count == 2

    first_call = mock_client.query.call_args_list[0]
    assert first_call[1]["job_config"].dry_run is True

    second_call = mock_client.query.call_args_list[1]
    assert second_call[1]["job_config"].dry_run is False

    assert df.shape == (2, 4)


def test_query_exceeds_maximum_bytes_billed(mock_bigquery_module, tmp_path, monkeypatch):
    """Test that query is refused when dry-run estimate exceeds limit."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    client = MagicMock()

    def query_side_effect(sql, job_config=None):
        job = MagicMock()
        type(job).total_bytes_processed = PropertyMock(return_value=2_000_000_000)
        return job

    client.query.side_effect = query_side_effect

    with pytest.raises(ValueError, match="exceeding limit"):
        load_bigquery(
            "SELECT * FROM `test.table`",
            grain_columns=["product_id", "location_id", "period"],
            value_column="quantity",
            maximum_bytes_billed=1_000_000_000,
            refresh=True,
            _client=client,
        )


def test_default_maximum_bytes_billed(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that default maximum_bytes_billed is 1 GB."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    second_call = mock_client.query.call_args_list[1]
    assert second_call[1]["job_config"].maximum_bytes_billed == 1_000_000_000


def test_custom_maximum_bytes_billed(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that custom maximum_bytes_billed is set correctly."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    custom_limit = 5_000_000_000

    load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        maximum_bytes_billed=custom_limit,
        refresh=True,
        _client=mock_client,
    )

    second_call = mock_client.query.call_args_list[1]
    assert second_call[1]["job_config"].maximum_bytes_billed == custom_limit


def test_arrow_to_polars_conversion(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test Arrow -> Polars conversion with correct columns and dtypes."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    df = load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    assert df.shape == (2, 4)
    assert df.columns == ["product_id", "location_id", "period", "quantity"]

    assert df["product_id"].dtype == pl.String
    assert df["location_id"].dtype == pl.String
    assert df["period"].dtype == pl.String
    assert df["quantity"].dtype == pl.Int64

    assert df["product_id"].to_list() == ["P001", "P002"]
    assert df["quantity"].to_list() == [100, 110]


def test_cache_write_on_first_call(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that first call writes to cache."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    query = "SELECT * FROM `test.table`"

    load_bigquery(
        query,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    cache_files = list(tmp_path.glob("bq_*.parquet"))
    assert len(cache_files) == 1

    import hashlib

    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    expected_cache_path = tmp_path / f"bq_{query_hash}.parquet"
    assert expected_cache_path.exists()


def test_cache_read_on_second_call(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that second call reads from cache without calling client."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    query = "SELECT * FROM `test.table`"
    grain_columns = ["product_id", "location_id", "period"]
    value_column = "quantity"

    df1 = load_bigquery(
        query,
        grain_columns=grain_columns,
        value_column=value_column,
        refresh=True,
        _client=mock_client,
    )

    mock_client.reset_mock()

    df2 = load_bigquery(
        query,
        grain_columns=grain_columns,
        value_column=value_column,
        refresh=False,
        _client=mock_client,
    )

    assert mock_client.query.call_count == 0

    assert df1.equals(df2)


def test_refresh_bypasses_cache(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that refresh=True bypasses cache."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    query = "SELECT * FROM `test.table`"
    grain_columns = ["product_id", "location_id", "period"]
    value_column = "quantity"

    load_bigquery(
        query,
        grain_columns=grain_columns,
        value_column=value_column,
        refresh=True,
        _client=mock_client,
    )

    mock_client.reset_mock()

    load_bigquery(
        query,
        grain_columns=grain_columns,
        value_column=value_column,
        refresh=True,
        _client=mock_client,
    )

    assert mock_client.query.call_count == 2


def test_different_queries_different_fingerprints(
    mock_bigquery_module, mock_client, tmp_path, monkeypatch
):
    """Test that different queries get different cache fingerprints."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    query1 = "SELECT * FROM `test.table1`"
    query2 = "SELECT * FROM `test.table2`"

    load_bigquery(
        query1,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    load_bigquery(
        query2,
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    cache_files = list(tmp_path.glob("bq_*.parquet"))
    assert len(cache_files) == 2

    cache_names = {f.name for f in cache_files}
    assert len(cache_names) == 2


def test_missing_bigquery_import():
    """Test that missing google-cloud-bigquery gives helpful error."""
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


def test_missing_required_columns(mock_bigquery_module, tmp_path, monkeypatch):
    """Test that missing required columns in result raises clear error."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    client = MagicMock()

    def query_side_effect(sql, job_config=None):
        job = MagicMock()

        if job_config and job_config.dry_run:
            type(job).total_bytes_processed = PropertyMock(return_value=1000)
        else:
            incomplete_table = pa.table(
                {
                    "product_id": ["P001", "P002"],
                    "location_id": ["L001", "L001"],
                }
            )
            result = MagicMock()
            result.to_arrow.return_value = incomplete_table
            job.result.return_value = result

        return job

    client.query.side_effect = query_side_effect

    with pytest.raises(ValueError, match="Missing required columns in query result"):
        load_bigquery(
            "SELECT * FROM `test.table`",
            grain_columns=["product_id", "location_id", "period"],
            value_column="quantity",
            refresh=True,
            _client=client,
        )


def test_job_config_use_query_cache(mock_bigquery_module, mock_client, tmp_path, monkeypatch):
    """Test that QueryJobConfig has use_query_cache=True."""
    monkeypatch.setattr("lonely_planner.io_bq.CACHE_DIR", tmp_path)

    load_bigquery(
        "SELECT * FROM `test.table`",
        grain_columns=["product_id", "location_id", "period"],
        value_column="quantity",
        refresh=True,
        _client=mock_client,
    )

    second_call = mock_client.query.call_args_list[1]
    assert second_call[1]["job_config"].use_query_cache is True
