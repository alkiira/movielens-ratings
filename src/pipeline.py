"""Шаги проекта как отдельные функции (используются меню и run_all)."""
from . import analysis, config as C, data_loader as dl, db, pandas_vs_sql, sql_queries, viz
from .utils import load_json, save_json


def step_audit_and_memory():
    audit = dl.data_quality_audit()
    mem = dl.memory_report()
    save_json({"audit": audit, "memory": mem}, "step1_audit_memory.json")
    return audit, mem


def step_parquet():
    info = dl.csv_to_parquet_chunked()
    io = dl.csv_vs_parquet()
    save_json({"convert": info, "io": io}, "step2_parquet.json")
    return info, io


def step_database():
    info = db.build_database()
    db.draw_er_diagram()
    save_json(info, "step3_db.json")
    return info


def step_sql():
    return sql_queries.run_all()


def step_compare():
    return pandas_vs_sql.compare()


def step_eda():
    ms = analysis.movie_stats()
    ua = analysis.user_activity()
    trends = analysis.genre_trends()
    dist = analysis.rating_distribution()
    summary = {
        "popularity_vs_quality": analysis.popularity_vs_quality(ms),
        "outliers_user_activity": analysis.outliers_iqr(ua["n"]),
        "outliers_movie_popularity": analysis.outliers_iqr(ms["n"]),
        "top5_bayesian": analysis.bayesian_average(ms[ms["n"] >= C.MIN_RATINGS_QUALITY])
                         .head(5)[["title", "n", "avg_rating", "bayes"]].round(3).to_dict("records"),
    }
    save_json(summary, "step6_eda.json")
    viz.plot_rating_distribution(dist)
    viz.plot_genre_popularity_vs_quality()
    viz.plot_genre_heatmap(trends)
    viz.plot_ratings_per_year()
    viz.plot_popularity_vs_quality(ms)
    viz.plot_user_activity(ua)
    io = load_json("step2_parquet.json").get("io")
    mem = load_json("step1_audit_memory.json").get("memory")
    cmp_ = load_json("pandas_vs_sql.json")
    if io and mem and cmp_:
        viz.plot_benchmarks(mem, io, cmp_)
    return summary
