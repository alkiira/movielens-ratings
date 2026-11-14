"""Точка входа: консольное меню (требование 7).
Запуск:  python main.py          - меню
         python main.py --all    - выполнить все шаги подряд"""
import sys
import json

from src import config as C
from src import pipeline as P
from src.db import run_sql
from src.sql_queries import load_queries, run_query

MENU = """
===== MovieLens: Movie Ratings at Scale =====
1 - Аудит данных + оптимизация памяти (до/после)
2 - CSV -> Parquet (по чанкам) + сравнение CSV vs Parquet
3 - Создать БД SQLite (3НФ) + ER-диаграмма
4 - Выполнить все SQL-запросы (Q1-Q10)
5 - Сравнение: Pandas (CSV) vs Pandas (Parquet) vs SQL
6 - EDA и графики
7 - Top-N фильмов в жанре (интерактивно)
8 - Поиск фильма по названию
9 - Выполнить ВСЕ шаги 1-6
0 - Выход
Выбор: """


def check_raw_files() -> bool:
    missing = [p.name for p in (C.RATINGS_CSV, C.MOVIES_CSV) if not p.exists()]
    if missing:
        print(f"Нет файлов в {C.RAW_DIR}: {', '.join(missing)}.\n"
              "Скачайте MovieLens (см. README) или запустите: python generate_sample_data.py")
        return False
    return True


def pp(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def top_n_in_genre():
    genres = run_sql("SELECT name FROM genres ORDER BY name")["name"].tolist()
    print("Жанры:", ", ".join(genres))
    while True:                                  # повторный ввод
        genre = input("Жанр: ").strip()
        if genre in genres:
            break
        print("Такого жанра нет, попробуйте ещё раз.")
    try:
        n = int(input("Сколько фильмов (N): "))
        if n <= 0:
            raise ValueError
    except ValueError:                           # обработка ошибок
        print("Некорректное N, используем 5.")
        n = 5
    df = run_sql(
        """SELECT m.title, COUNT(*) AS n_ratings, ROUND(AVG(r.rating),3) AS avg_rating
           FROM ratings r JOIN movies m USING(movie_id)
           JOIN movie_genres mg USING(movie_id) JOIN genres g USING(genre_id)
           WHERE g.name = ? GROUP BY m.movie_id, m.title HAVING COUNT(*) >= ?
           ORDER BY avg_rating DESC, n_ratings DESC LIMIT ?""",
        (genre, C.MIN_RATINGS_QUALITY, n))
    print(df.to_string(index=False))


def search_movie():
    q = input("Часть названия: ").strip()
    if not q:
        print("Пустой запрос.")
        return
    df = run_sql(
        """SELECT m.title, m.year, COUNT(r.rating) AS n_ratings, ROUND(AVG(r.rating),3) AS avg_rating
           FROM movies m LEFT JOIN ratings r USING(movie_id)
           WHERE m.title LIKE ? GROUP BY m.movie_id, m.title, m.year
           ORDER BY n_ratings DESC LIMIT 15""", (f"%{q}%",))
    print(df.to_string(index=False) if len(df) else "Ничего не найдено.")


def run_all():
    audit, mem = P.step_audit_and_memory(); pp({"audit": audit, "memory": mem})
    info, io = P.step_parquet(); pp({"convert": info, "io": io})
    pp(P.step_database())
    P.step_sql()
    pp(P.step_compare())
    pp(P.step_eda())
    print(f"\nГотово. Результаты: {C.OUT_DIR}")


def main():
    if "--all" in sys.argv:
        if check_raw_files():
            run_all()
        return
    actions = {
        "1": lambda: pp(dict(zip(("audit", "memory"), P.step_audit_and_memory()))),
        "2": lambda: pp(dict(zip(("convert", "io"), P.step_parquet()))),
        "3": lambda: pp(P.step_database()),
        "4": P.step_sql,
        "5": lambda: pp(P.step_compare()),
        "6": lambda: pp(P.step_eda()),
        "7": top_n_in_genre,
        "8": search_movie,
        "9": run_all,
    }
    while True:
        choice = input(MENU).strip()
        if choice == "0":
            print("До свидания!")
            break
        action = actions.get(choice)
        if action is None:
            print("Неверный пункт меню.")
            continue
        if not check_raw_files():
            continue
        try:
            action()
        except FileNotFoundError as e:
            print(f"Файл не найден: {e}. Выполните предыдущие шаги (1-3).")
        except Exception as e:                    # noqa: BLE001
            print(f"Ошибка: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
