"""BigQuery import module with caching."""

import hashlib
import os

import polars as pl

from lonely_planner.config import CACHE_DIR


def load_bigquery(
    query: str,
    grain_columns: list[str],
    value_column: str,
    maximum_bytes_billed: int | None = None,
    refresh: bool = False,
) -> pl.DataFrame:
    """Load sales history from BigQuery with Parquet caching.

    Args:
        query: SQL query to execute
        grain_columns: List of grain column names
        value_column: Name of the value column
        maximum_bytes_billed: Maximum bytes to bill (default 1 GB)
        refresh: If True, bypass cache and refresh data

    Returns:
        Polars DataFrame with validated columns
    """
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        msg = "google-cloud-bigquery not installed. Install with: pip install lonely-planner[bigquery]"
        raise ImportError(msg) from exc

    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    cache_path = CACHE_DIR / f"bq_{query_hash}.parquet"

    if not refresh and cache_path.exists():
        df = pl.read_parquet(cache_path)
        required_columns = grain_columns + [value_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if not missing_columns:
            return df.select(required_columns)

    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        client = bigquery.Client.from_service_account_json(credentials_path)
    else:
        client = bigquery.Client()

    job_config = bigquery.QueryJobConfig(use_query_cache=True)
    if maximum_bytes_billed is not None:
        job_config.maximum_bytes_billed = maximum_bytes_billed

    dry_run_config = bigquery.QueryJobConfig(dry_run=True)
    dry_run_job = client.query(query, job_config=dry_run_config)
    estimated_bytes = dry_run_job.total_bytes_processed

    print(f"Estimated bytes to process: {estimated_bytes:,}")

    if maximum_bytes_billed and estimated_bytes > maximum_bytes_billed:
        msg = (
            f"Query would process {estimated_bytes:,} bytes, "
            f"exceeding limit of {maximum_bytes_billed:,}"
        )
        raise ValueError(msg)

    query_job = client.query(query, job_config=job_config)
    rows = query_job.result()

    arrow_table = rows.to_arrow()
    df = pl.from_arrow(arrow_table)

    required_columns = grain_columns + [value_column]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        msg = f"Missing required columns in query result: {missing_columns}"
        raise ValueError(msg)

    df_subset = df.select(required_columns)
    df_subset.write_parquet(cache_path)

    return df_subset
