-- Q1 [GROUP BY]: распределение оценок
SELECT rating, COUNT(*) AS n
FROM ratings GROUP BY rating ORDER BY rating;

-- Q2 [JOIN + GROUP BY + HAVING]: фильмы с >= 50 оценками, топ-10 по среднему
SELECT m.title, COUNT(*) AS n_ratings, ROUND(AVG(r.rating), 3) AS avg_rating
FROM ratings r JOIN movies m ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
HAVING COUNT(*) >= 50
ORDER BY avg_rating DESC, n_ratings DESC
LIMIT 10;

-- Q3 [JOIN x3 + GROUP BY]: число оценок и средняя оценка по жанрам
SELECT g.name AS genre, COUNT(*) AS n_ratings, ROUND(AVG(r.rating), 3) AS avg_rating
FROM ratings r
JOIN movie_genres mg ON mg.movie_id = r.movie_id
JOIN genres g ON g.genre_id = mg.genre_id
GROUP BY g.name
ORDER BY n_ratings DESC;

-- Q4 [CTE + WINDOW ROW_NUMBER]: Top-N фильмов в каждом жанре (ключевой фокус темы)
WITH movie_stats AS (
    SELECT r.movie_id, COUNT(*) AS n, AVG(r.rating) AS avg_rating
    FROM ratings r GROUP BY r.movie_id HAVING COUNT(*) >= :min_n
),
ranked AS (
    SELECT g.name AS genre, m.title, s.n, ROUND(s.avg_rating, 3) AS avg_rating,
           ROW_NUMBER() OVER (PARTITION BY g.name
                              ORDER BY s.avg_rating DESC, s.n DESC) AS rn
    FROM movie_stats s
    JOIN movies m ON m.movie_id = s.movie_id
    JOIN movie_genres mg ON mg.movie_id = s.movie_id
    JOIN genres g ON g.genre_id = mg.genre_id
)
SELECT genre, rn, title, n, avg_rating FROM ranked WHERE rn <= :top_n
ORDER BY genre, rn;

-- Q5 [WINDOW RANK]: ранг жанров по средней оценке внутри каждого десятилетия
WITH gd AS (
    SELECT (m.year / 10) * 10 AS decade, g.name AS genre,
           COUNT(*) AS n, AVG(r.rating) AS avg_rating
    FROM ratings r
    JOIN movies m ON m.movie_id = r.movie_id
    JOIN movie_genres mg ON mg.movie_id = r.movie_id
    JOIN genres g ON g.genre_id = mg.genre_id
    WHERE m.year IS NOT NULL
    GROUP BY decade, g.name HAVING COUNT(*) >= 1000
)
SELECT decade, genre, n, ROUND(avg_rating, 3) AS avg_rating,
       RANK() OVER (PARTITION BY decade ORDER BY avg_rating DESC) AS rnk
FROM gd ORDER BY decade, rnk;

-- Q6 [WINDOW скользящее среднее]: число оценок по годам + скользящее среднее за 3 года
WITH yearly AS (
    SELECT CAST(strftime('%Y', ts, 'unixepoch') AS INTEGER) AS year,
           COUNT(*) AS n, AVG(rating) AS avg_rating
    FROM ratings GROUP BY year
)
SELECT year, n, ROUND(avg_rating, 3) AS avg_rating,
       ROUND(AVG(avg_rating) OVER (ORDER BY year
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 3) AS moving_avg_3y
FROM yearly ORDER BY year;

-- Q7 [ПОДЗАПРОС]: самые активные пользователи (оценок > 5x среднего по пользователям)
SELECT user_id, n_ratings, ROUND(avg_rating, 3) AS avg_rating
FROM (SELECT user_id, COUNT(*) AS n_ratings, AVG(rating) AS avg_rating
      FROM ratings GROUP BY user_id)
WHERE n_ratings > (SELECT 5 * AVG(c) FROM
                   (SELECT COUNT(*) AS c FROM ratings GROUP BY user_id))
ORDER BY n_ratings DESC LIMIT 20;

-- Q8 [CTE + WINDOW NTILE]: популярность vs качество - квартили популярности
WITH ms AS (
    SELECT movie_id, COUNT(*) AS n, AVG(rating) AS avg_rating
    FROM ratings GROUP BY movie_id
),
q AS (
    SELECT *, NTILE(4) OVER (ORDER BY n) AS popularity_quartile FROM ms
)
SELECT popularity_quartile, COUNT(*) AS n_movies,
       MIN(n) AS min_ratings, MAX(n) AS max_ratings,
       ROUND(AVG(avg_rating), 3) AS mean_of_avg_rating
FROM q GROUP BY popularity_quartile ORDER BY popularity_quartile;

-- Q9 [LAG]: прирост числа оценок год к году
WITH yearly AS (
    SELECT CAST(strftime('%Y', ts, 'unixepoch') AS INTEGER) AS year, COUNT(*) AS n
    FROM ratings GROUP BY year
)
SELECT year, n, n - LAG(n) OVER (ORDER BY year) AS diff_prev_year
FROM yearly ORDER BY year;

-- Q10 [JOIN + оконная SUM OVER]: доля жанра в общем числе оценок (накопленная)
WITH gcount AS (
    SELECT g.name AS genre, COUNT(*) AS n
    FROM ratings r
    JOIN movie_genres mg ON mg.movie_id = r.movie_id
    JOIN genres g ON g.genre_id = mg.genre_id
    GROUP BY g.name
)
SELECT genre, n,
       ROUND(100.0 * n / SUM(n) OVER (), 2) AS pct,
       ROUND(100.0 * SUM(n) OVER (ORDER BY n DESC) / SUM(n) OVER (), 2) AS cum_pct
FROM gcount ORDER BY n DESC;
