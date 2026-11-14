"""Шаг 6. EDA: распределения, тренды жанров, популярность vs качество."""
import numpy as np
import pandas as pd

from . import config as C
from .data_loader import load_movies
from .db import run_sql


def rating_distribution() -> pd.DataFrame:
    return run_sql("SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating")


def movie_stats() -> pd.DataFrame:
    """Статистика на фильм: n оценок, средняя, год, жанры."""
    df = run_sql("""SELECT m.movie_id, m.title, m.year, COUNT(*) AS n,
                           AVG(r.rating) AS avg_rating
                    FROM ratings r JOIN movies m USING(movie_id)
                    GROUP BY m.movie_id, m.title, m.year""")
    return df


def user_activity() -> pd.DataFrame:
    return run_sql("""SELECT user_id, COUNT(*) AS n, AVG(rating) AS avg_rating
                      FROM ratings GROUP BY user_id""")


def genre_trends() -> pd.DataFrame:
    """Средняя оценка и число оценок по жанру и десятилетию выхода фильма."""
    return run_sql("""
        SELECT (m.year/10)*10 AS decade, g.name AS genre,
               COUNT(*) AS n, AVG(r.rating) AS avg_rating
        FROM ratings r
        JOIN movies m ON m.movie_id = r.movie_id
        JOIN movie_genres mg ON mg.movie_id = r.movie_id
        JOIN genres g ON g.genre_id = mg.genre_id
        WHERE m.year IS NOT NULL
        GROUP BY decade, g.name""")


def outliers_iqr(series: pd.Series) -> dict:
    """Выбросы по IQR (числа оценок у пользователей/фильмов)."""
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    hi = q3 + 1.5 * iqr
    return {"q1": float(q1), "q3": float(q3), "upper_fence": float(hi),
            "n_outliers": int((series > hi).sum()), "share_pct": round(100 * (series > hi).mean(), 2)}


def popularity_vs_quality(ms: pd.DataFrame, min_n: int = C.MIN_RATINGS_QUALITY) -> dict:
    """Корреляция Спирмена между log(число оценок) и средней оценкой."""
    d = ms[ms["n"] >= min_n].copy()
    rho = d["n"].corr(d["avg_rating"], method="spearman")
    d["pop_quartile"] = pd.qcut(d["n"], 4, labels=["Q1 (редкие)", "Q2", "Q3", "Q4 (популярные)"])
    by_q = d.groupby("pop_quartile", observed=True)["avg_rating"].mean().round(3).to_dict()
    return {"n_movies": int(len(d)), "spearman_rho": round(float(rho), 3),
            "mean_rating_by_popularity_quartile": {str(k): v for k, v in by_q.items()}}


def bayesian_average(ms: pd.DataFrame, m_prior: int = 100) -> pd.DataFrame:
    """Взвешенный рейтинг (IMDb-подобный): устойчив к фильмам с малым числом оценок."""
    c = (ms["avg_rating"] * ms["n"]).sum() / ms["n"].sum()
    ms = ms.copy()
    ms["bayes"] = (ms["n"] / (ms["n"] + m_prior)) * ms["avg_rating"] + \
                  (m_prior / (ms["n"] + m_prior)) * c
    return ms.sort_values("bayes", ascending=False)
