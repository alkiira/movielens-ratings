"""Шаг 4. Загрузка и выполнение SQL-запросов из sql/queries.sql."""
import re

import pandas as pd

from . import config as C
from .db import run_sql


def load_queries() -> dict:
    """Парсит queries.sql в словарь {'Q1': (описание, текст)}."""
    text = (C.SQL_DIR / "queries.sql").read_text(encoding="utf-8")
    blocks = re.split(r"^-- (Q\d+) ", text, flags=re.M)[1:]
    queries = {}
    for i in range(0, len(blocks), 2):
        qid, body = blocks[i], blocks[i + 1]
        desc, _, sql = body.partition("\n")
        queries[qid] = (desc.strip(), sql.strip().rstrip(";"))
    return queries


def run_query(qid: str) -> pd.DataFrame:
    queries = load_queries()
    if qid not in queries:
        raise KeyError(f"Нет запроса {qid}")
    sql = queries[qid][1]
    params = {}
    if ":min_n" in sql:
        params = {"min_n": C.MIN_RATINGS_QUALITY, "top_n": C.TOP_N}
    return run_sql(sql, params)


def run_all() -> dict:
    """Запускает все запросы, сохраняет результаты в CSV."""
    results = {}
    for qid, (desc, _) in load_queries().items():
        df = run_query(qid)
        df.to_csv(C.OUT_DIR / f"{qid.lower()}.csv", index=False)
        results[qid] = df
        print(f"{qid}: {desc} -> {len(df)} строк")
    return results
