"""Пути и константы проекта (требование 8: модульность, pathlib)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"          # сюда кладём ratings.csv, movies.csv, ...
PROC_DIR = ROOT / "data" / "processed"   # parquet, sqlite
OUT_DIR = ROOT / "outputs"
FIG_DIR = OUT_DIR / "figures"
SQL_DIR = ROOT / "sql"

RATINGS_CSV = RAW_DIR / "ratings.csv"
MOVIES_CSV = RAW_DIR / "movies.csv"
TAGS_CSV = RAW_DIR / "tags.csv"
LINKS_CSV = RAW_DIR / "links.csv"

RATINGS_PARQUET = PROC_DIR / "ratings.parquet"
MOVIES_PARQUET = PROC_DIR / "movies.parquet"
DB_PATH = PROC_DIR / "movielens.db"

import os

CHUNKSIZE = 1_000_000
# Для быстрой отладки можно ограничить число строк: ML_MAX_ROWS=3000000 python main.py --all
_mr = os.environ.get("ML_MAX_ROWS")
MAX_ROWS = int(_mr) if _mr else None
MIN_RATINGS_QUALITY = 50   # порог числа оценок для "качества" фильма
TOP_N = 5

for _d in (RAW_DIR, PROC_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)
