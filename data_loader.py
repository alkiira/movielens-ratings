"""Шаг 1-2. Чанковая загрузка, оптимизация типов, конвертация в Parquet."""
import pandas as pd

from . import config as C
from .utils import df_mb, file_mb, timed

RATINGS_DTYPES_RAW = None  # по умолчанию pandas: int64/float64
RATINGS_DTYPES_OPT = {"userId": "int32", "movieId": "int32", "rating": "float32"}


def read_ratings_naive() -> pd.DataFrame:
    """Baseline: читаем всё без оптимизации."""
    return pd.read_csv(C.RATINGS_CSV, nrows=C.MAX_ROWS)


def read_ratings_optimized() -> pd.DataFrame:
    """Оптимизация: узкие типы; timestamp -> int32 (секунды до 2038 г. влезают)."""
    dtypes = dict(RATINGS_DTYPES_OPT, timestamp="int32")
    return pd.read_csv(C.RATINGS_CSV, dtype=dtypes, nrows=C.MAX_ROWS)


def read_ratings_chunked(chunksize: int = C.CHUNKSIZE):
    """Генератор чанков с оптимизированными типами (требование 11)."""
    dtypes = dict(RATINGS_DTYPES_OPT, timestamp="int32")
    for chunk in pd.read_csv(C.RATINGS_CSV, dtype=dtypes, chunksize=chunksize, nrows=C.MAX_ROWS):
        yield chunk


def load_movies() -> pd.DataFrame:
    """movies.csv: добавляем год и список жанров."""
    movies = pd.read_csv(C.MOVIES_CSV, dtype={"movieId": "int32"})
    movies["year"] = (movies["title"].str.extract(r"\((\d{4})\)\s*$")[0]
                      .astype("float32"))
    movies["genres_list"] = movies["genres"].str.split("|")
    return movies


def csv_to_parquet_chunked() -> dict:
    """CSV -> Parquet по чанкам (не держим всё в памяти)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    writer = None
    n_rows = 0
    for chunk in read_ratings_chunked():
        table = pa.Table.from_pandas(chunk, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(C.RATINGS_PARQUET, table.schema,
                                      compression="snappy")
        writer.write_table(table)
        n_rows += len(chunk)
    if writer is not None:
        writer.close()
    movies = load_movies().drop(columns=["genres_list"])
    movies.to_parquet(C.MOVIES_PARQUET, index=False)
    return {"rows": n_rows, "parquet_mb": file_mb(C.RATINGS_PARQUET)}


def memory_report() -> dict:
    """Память ДО и ПОСЛЕ оптимизации типов."""
    before = read_ratings_naive()
    mb_before = df_mb(before)
    del before
    after = read_ratings_optimized()
    mb_after = df_mb(after)
    return {
        "rows": int(len(after)),
        "memory_before_mb": round(mb_before, 1),
        "memory_after_mb": round(mb_after, 1),
        "saving_pct": round(100 * (1 - mb_after / mb_before), 1),
    }


@timed
def _timed_csv():
    return pd.read_csv(C.RATINGS_CSV, nrows=C.MAX_ROWS)


@timed
def _timed_csv_opt():
    return read_ratings_optimized()


@timed
def _timed_parquet():
    return pd.read_parquet(C.RATINGS_PARQUET)


def csv_vs_parquet() -> dict:
    """Сравнение: размер файла и время чтения (требование 9)."""
    _, t_csv = _timed_csv()
    _, t_csv_opt = _timed_csv_opt()
    _, t_pq = _timed_parquet()
    return {
        "csv_size_mb": round(file_mb(C.RATINGS_CSV), 1),
        "parquet_size_mb": round(file_mb(C.RATINGS_PARQUET), 1),
        "csv_read_s": round(t_csv, 2),
        "csv_optimized_read_s": round(t_csv_opt, 2),
        "parquet_read_s": round(t_pq, 2),
    }


def data_quality_audit() -> dict:
    """Аудит качества: пропуски, дубликаты, диапазоны, 'сиротские' movieId."""
    r = read_ratings_optimized()
    m = load_movies()
    return {
        "n_ratings": int(len(r)),
        "n_users": int(r["userId"].nunique()),
        "n_movies_rated": int(r["movieId"].nunique()),
        "n_movies_catalog": int(len(m)),
        "nulls_ratings": int(r.isna().sum().sum()),
        "duplicate_user_movie": int(r.duplicated(["userId", "movieId"]).sum()),
        "rating_min": float(r["rating"].min()),
        "rating_max": float(r["rating"].max()),
        "orphan_movieIds": int((~r["movieId"].isin(m["movieId"])).sum()),
        "movies_without_year": int(m["year"].isna().sum()),
        "movies_no_genre": int((m["genres"] == "(no genres listed)").sum()),
    }
