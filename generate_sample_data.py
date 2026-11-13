"""Генератор СИНТЕТИЧЕСКИХ данных в формате MovieLens - только для отладки кода,
если настоящий датасет ещё не скачан. Для отчёта используйте реальные данные!
Запуск: python generate_sample_data.py [число_оценок]  (по умолчанию 2_000_000)"""
import sys
import numpy as np
import pandas as pd
from src import config as C

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000
rng = np.random.default_rng(42)
GENRES = ["Action", "Adventure", "Animation", "Children", "Comedy", "Crime", "Documentary",
          "Drama", "Fantasy", "Film-Noir", "Horror", "IMAX", "Musical", "Mystery", "Romance",
          "Sci-Fi", "Thriller", "War", "Western"]
n_movies, n_users = 8000, 20000
years = rng.integers(1930, 2020, n_movies)
rows = []
for i in range(n_movies):
    k = rng.integers(0, 4)
    g = "|".join(rng.choice(GENRES, k, replace=False)) if k else "(no genres listed)"
    rows.append((i + 1, f"Movie {i+1} ({years[i]})", g))
pd.DataFrame(rows, columns=["movieId", "title", "genres"]).to_csv(C.MOVIES_CSV, index=False)

pop = rng.pareto(1.2, n_movies) + 1
pop /= pop.sum()
quality = rng.normal(3.4, 0.5, n_movies)
users = rng.integers(1, n_users + 1, N * 11 // 10)
movies = rng.choice(np.arange(1, n_movies + 1), N * 11 // 10, p=pop)
df = pd.DataFrame({"userId": users, "movieId": movies}).drop_duplicates().head(N)
r = np.clip(np.round((quality[df.movieId.values - 1] + rng.normal(0, 0.8, len(df))) * 2) / 2, 0.5, 5.0)
df["rating"] = r
df["timestamp"] = rng.integers(820_000_000, 1_697_000_000, len(df))
df.to_csv(C.RATINGS_CSV, index=False)
print("Сгенерировано:", len(df), "оценок,", n_movies, "фильмов")
