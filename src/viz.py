"""Шаг 7. Визуализации (по результатам SQL-запросов)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from . import config as C
from .sql_queries import run_query


def _save(fig, name):
    path = C.FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_rating_distribution(df):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(df["rating"].astype(str), df["n"] / 1e6, color="#2b6cb0")
    ax.set(title="Распределение оценок", xlabel="Оценка", ylabel="Оценок, млн")
    return _save(fig, "01_rating_distribution.png")


def plot_genre_popularity_vs_quality():
    df = run_query("Q3")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df["n_ratings"] / 1e6, df["avg_rating"], s=60, color="#c05621")
    for _, r in df.iterrows():
        ax.annotate(r["genre"], (r["n_ratings"] / 1e6, r["avg_rating"]), fontsize=8,
                    xytext=(3, 3), textcoords="offset points")
    ax.set(title="Жанры: популярность vs средняя оценка",
           xlabel="Число оценок, млн", ylabel="Средняя оценка")
    return _save(fig, "02_genre_popularity_quality.png")


def plot_genre_heatmap(trends):
    top = trends.groupby("genre")["n"].sum().nlargest(10).index
    d = trends[trends["genre"].isin(top) & (trends["n"] >= 1000)]
    pv = d.pivot(index="genre", columns="decade", values="avg_rating")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.heatmap(pv, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax)
    ax.set(title="Средняя оценка: жанр × десятилетие выхода фильма", xlabel="Десятилетие", ylabel="")
    return _save(fig, "03_genre_decade_heatmap.png")


def plot_ratings_per_year():
    df = run_query("Q6")
    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.bar(df["year"], df["n"] / 1e6, color="#a0aec0")
    ax1.set(xlabel="Год оценки", ylabel="Оценок, млн", title="Активность по годам и скользящее среднее оценки")
    ax2 = ax1.twinx()
    ax2.plot(df["year"], df["moving_avg_3y"], color="#c53030", marker="o")
    ax2.set_ylabel("Скользящее среднее (3 г.)")
    return _save(fig, "04_ratings_per_year.png")


def plot_popularity_vs_quality(ms, min_n=C.MIN_RATINGS_QUALITY):
    d = ms[ms["n"] >= min_n]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(d["n"], d["avg_rating"], s=4, alpha=0.3, color="#2c5282")
    ax.set_xscale("log")
    ax.set(title=f"Популярность vs качество (фильмы с ≥{min_n} оценок)",
           xlabel="Число оценок (log)", ylabel="Средняя оценка")
    return _save(fig, "05_popularity_vs_quality.png")


def plot_user_activity(ua):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(np.log10(ua["n"]), bins=50, color="#38a169")
    ax.set(title="Активность пользователей (heavy tail)", xlabel="log10(число оценок)", ylabel="Пользователей")
    return _save(fig, "06_user_activity.png")


def plot_benchmarks(mem, io, cmp_):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].bar(["до", "после"], [mem["memory_before_mb"], mem["memory_after_mb"]], color=["#e53e3e", "#38a169"])
    axes[0].set(title="Память ratings, МБ")
    axes[1].bar(["CSV", "CSV opt", "Parquet"], [io["csv_read_s"], io["csv_optimized_read_s"], io["parquet_read_s"]],
                color=["#e53e3e", "#dd6b20", "#38a169"])
    axes[1].set(title="Время чтения, с")
    keys = ["pandas_csv_baseline_s", "pandas_parquet_s", "sqlite_s"]
    axes[2].bar(["Pandas\nCSV", "Pandas\nParquet", "SQLite"], [cmp_[k] for k in keys],
                color=["#e53e3e", "#38a169", "#2b6cb0"])
    axes[2].set(title="Top-N по жанрам, с")
    return _save(fig, "07_benchmarks.png")
