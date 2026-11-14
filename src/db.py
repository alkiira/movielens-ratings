"""Шаг 3. SQLite: схема в 3НФ, загрузка по чанкам, ER-диаграмма."""
import sqlite3

import pandas as pd

from . import config as C
from .data_loader import load_movies, read_ratings_chunked

SCHEMA = """
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS movie_genres;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS users;

CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    title    TEXT NOT NULL,
    year     INTEGER
);
CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE
);
CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id),
    genre_id INTEGER NOT NULL REFERENCES genres(genre_id),
    PRIMARY KEY (movie_id, genre_id)
);
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY
);
CREATE TABLE ratings (
    user_id  INTEGER NOT NULL REFERENCES users(user_id),
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id),
    rating   REAL    NOT NULL,
    ts       INTEGER NOT NULL,
    PRIMARY KEY (user_id, movie_id)
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_mg_genre ON movie_genres(genre_id);
"""


def connect() -> sqlite3.Connection:
    return sqlite3.connect(C.DB_PATH)


def build_database() -> dict:
    """Создаёт БД и грузит данные. Рейтинги - чанками, чтобы не забивать память."""
    movies = load_movies()
    with connect() as con:
        con.executescript(SCHEMA)
        # быстрая массовая загрузка (БД можно пересоздать в любой момент)
        con.execute("PRAGMA journal_mode = OFF")
        con.execute("PRAGMA synchronous = OFF")
        con.execute("PRAGMA cache_size = -200000")

        # movies
        m = movies[["movieId", "title", "year"]].rename(
            columns={"movieId": "movie_id"})
        m["year"] = m["year"].astype("Int64")
        m.to_sql("movies", con, if_exists="append", index=False)

        # genres + связь many-to-many (нормализация: жанры не хранятся строкой)
        exploded = movies[["movieId", "genres_list"]].explode("genres_list")
        exploded = exploded[exploded["genres_list"] != "(no genres listed)"]
        genre_names = sorted(exploded["genres_list"].dropna().unique())
        pd.DataFrame({"name": genre_names}).to_sql(
            "genres", con, if_exists="append", index=False)
        gmap = pd.read_sql("SELECT genre_id, name FROM genres", con)
        mg = (exploded.merge(gmap, left_on="genres_list", right_on="name")
              [["movieId", "genre_id"]]
              .rename(columns={"movieId": "movie_id"}))
        mg.to_sql("movie_genres", con, if_exists="append", index=False)

        # ratings чанками + users
        users, n = set(), 0
        for chunk in read_ratings_chunked():
            chunk = chunk.rename(columns={"userId": "user_id",
                                          "movieId": "movie_id",
                                          "timestamp": "ts"})
            chunk.to_sql("ratings", con, if_exists="append", index=False,
                         chunksize=200_000, method=None)
            users.update(chunk["user_id"].unique().tolist())
            n += len(chunk)
        pd.DataFrame({"user_id": sorted(users)}).to_sql(
            "users", con, if_exists="append", index=False)
        con.executescript(INDEXES)
        con.execute("ANALYZE")
    return {"movies": len(m), "genres": len(genre_names),
            "movie_genres": len(mg), "users": len(users), "ratings": n}


def run_sql(query: str, params=()) -> pd.DataFrame:
    """Выполняет запрос и возвращает DataFrame (требование 10)."""
    with connect() as con:
        return pd.read_sql_query(query, con, params=params)


def draw_er_diagram(path=None):
    """ER-диаграмма средствами matplotlib (без graphviz)."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    path = path or C.FIG_DIR / "er_diagram.png"
    tables = {
        "users": (0.5, 4.2, ["PK user_id"]),
        "ratings": (4.6, 3.6, ["PK,FK user_id", "PK,FK movie_id", "rating", "ts"]),
        "movies": (8.7, 3.9, ["PK movie_id", "title", "year"]),
        "movie_genres": (8.7, 0.6, ["PK,FK movie_id", "PK,FK genre_id"]),
        "genres": (4.6, 0.6, ["PK genre_id", "name (UNIQUE)"]),
    }
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 7.2); ax.axis("off")
    boxes = {}
    for name, (x, y, cols) in tables.items():
        h = 0.5 * (len(cols) + 1) + 0.2
        w = 3.0
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                    fc="#eef3fb", ec="#2b4c7e", lw=1.5))
        ax.text(x + w / 2, y + h - 0.35, name, ha="center", weight="bold")
        for i, c in enumerate(cols):
            ax.text(x + 0.2, y + h - 0.95 - 0.45 * i, c, fontsize=9)
        boxes[name] = (x, y, w, h)

    def link(a, b, side_a, side_b, label):
        def pt(n, side):
            x, y, w, h = boxes[n]
            return {"r": (x + w, y + h / 2), "l": (x, y + h / 2),
                    "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]
        pa, pb = pt(a, side_a), pt(b, side_b)
        ax.annotate("", xy=pb, xytext=pa, arrowprops=dict(arrowstyle="-|>", color="#555"))
        ax.text((pa[0] + pb[0]) / 2 + 0.1, (pa[1] + pb[1]) / 2 + 0.12, label,
                fontsize=9, color="#a33", ha="center")

    link("users", "ratings", "r", "l", "1 : N")
    link("movies", "ratings", "l", "r", "1 : N")
    link("movies", "movie_genres", "b", "t", "1 : N")
    link("genres", "movie_genres", "r", "l", "1 : N")
    ax.set_title("ER-диаграмма MovieLens (3НФ)", y=1.0)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
