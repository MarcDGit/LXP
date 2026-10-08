"""Configuration defaults for Lonely Planner."""

from pathlib import Path

CACHE_DIR = Path("data/cache")
OUTPUT_DIR = Path("data/out")
SAMPLE_DIR = Path("data/sample")

DEFAULT_GRAIN_COLUMNS = ["product_id", "location_id", "period"]
DEFAULT_VALUE_COLUMN = "quantity"

DEFAULT_MA_WINDOW = 12

DEFAULT_MAXIMUM_BYTES_BILLED = 1_000_000_000

CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
