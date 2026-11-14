"""Шаг 5. Один и тот же расчёт в SQL и Pandas: время + проверка совпадения.
Сравниваем ТРИ подхода (требование 9): baseline (Pandas на CSV без оптимизации),
Pandas на оптимизированном Parquet, SQL (SQLite)."""
import time

import numpy as np
import pandas as pd

from . import config as C
from .data_loader import load_movies, read_ratings_naive
from .db import run_sql
from .utils import save_json

MIN_N = C.MIN_RATINGS_QUALITY

SQL_TOPN = """
WITH s AS (SELECT movie_id, COUNT(*) AS n, AVG(rating) AS avg_rating
           FROM ratings GROUP BY movie_id HAVING COUNT(*) >= :min_n),
r AS (SELECT g.name AS genre, s.movie_id, s.n, s.avg_rating,
             ROW_NUMBER() OVER (PARTITION BY g.name
                                ORDER BY s.avg_rating DESC, s.n DESC, s.movie_id) AS rn
      FROM s JOIN movie_genres mg ON mg.movie_id = s.movie_id
             JOIN genres g ON g.genre_id = mg.genre_id)
SELECT genre, rn, movie_id, n, avg_rating FROM r WHERE rn <= :top_n
ORDER BY genre, rn
"""


def topn_pandas(ratings: pd.DataFrame, movies: pd.DataFrame,
                top_n: int = C.TOP_N, min_n: int = MIN_N) -> pd.DataFrame:
    """Top-N фильмов в жанре на Pandas (groupby + rank/cumcount)."""
    stats = (ratings.groupby("movieId")["rating"].agg(n="count", avg_rating="mean")
             .reset_index())
    stats = stats[stats["n"] >= min_n]
    exp = movies[["movieId", "genres_list"]].explode("genres_list")
    exp = exp[exp["genres_list"] != "(no genres listed)"]
    df = stats.merge(exp, on="movieId").rename(columns={"genres_list": "genre"})
    df = df.sort_values(["genre", "avg_rating", "n", "movieId"],
                        ascending=[True, False, False, True])
    df["rn"] = df.groupby("genre").cumcount() + 1
    out = df[df["rn"] <= top_n].rename(columns={"movieId": "movie_id"})
    return out[["genre", "rn", "movie_id", "n", "avg_rating"]].reset_index(drop=True)


def compare() -> dict:
    movies = load_movies()
    res = {}

    # A. baseline: Pandas на CSV (без оптимизации типов)
    t0 = time.perf_counter()
    r_csv = read_ratings_naive()
    out_a = topn_pandas(r_csv, movies)
    res["pandas_csv_baseline_s"] = round(time.perf_counter() - t0, 2)
    del r_csv

    # B. Pandas на Parquet (оптимизированные типы)
    t0 = time.perf_counter()
    r_pq = pd.read_parquet(C.RATINGS_PARQUET)
    out_b = topn_pandas(r_pq, movies)
    res["pandas_parquet_s"] = round(time.perf_counter() - t0, 2)
    del r_pq

    # C. SQL (SQLite)
    t0 = time.perf_counter()
    out_c = run_sql(SQL_TOPN, {"min_n": MIN_N, "top_n": C.TOP_N})
    res["sqlite_s"] = round(time.perf_counter() - t0, 2)

    # Проверка совпадения результатов
    def same(x, y):
        if list(x["movie_id"]) != list(y["movie_id"]) or list(x["genre"]) != list(y["genre"]):
            return False
        return bool(np.allclose(x["avg_rating"].astype(float), y["avg_rating"].astype(float),
                                atol=1e-4))
    res["results_match_baseline_vs_parquet"] = same(out_a, out_b)
    res["results_match_pandas_vs_sql"] = same(out_b, out_c)
    res["fastest"] = min(("pandas_csv_baseline_s", "pandas_parquet_s", "sqlite_s"),
                         key=lambda k: res[k])
    save_json(res, "pandas_vs_sql.json")
    return res
