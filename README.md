# Movie Ratings at Scale (MovieLens 32M)

Итоговый проект «Programming for Data Analysis and Database», ADA-2601M, тема 6.
Анализ распределений оценок, трендов жанров, популярности и качества фильмов.
Фокус: оптимизация памяти + Top-N фильмов в каждом жанре (оконные функции SQL).

**Команда:** Alina Y., Bakhytnur U., Dana K. (вклад каждого: см. раздел «Вклад участников»).

## Данные
MovieLens 32M (GroupLens Research, University of Minnesota):
https://grouplens.org/datasets/movielens/32m/
Прямая ссылка: https://files.grouplens.org/datasets/movielens/ml-32m.zip (239 МБ; 32 000 204 оценок, 87 585 фильмов, 200 948 пользователей).
Используются `ratings.csv` и `movies.csv`. Датасет в репозиторий не включён (объём и лицензия).
Можно использовать и MovieLens 25M (`ml-25m.zip`) - код не меняется.

Цитирование: F. M. Harper, J. A. Konstan. *The MovieLens Datasets: History and Context.*
ACM TiiS 5(4), 2015. https://doi.org/10.1145/2827872

## Запуск в Google Colab (рекомендуется)
Откройте `notebooks/colab_run.ipynb` в Colab (Файл → Открыть блокнот → GitHub) и выполните ячейки сверху вниз.
Ноутбук сам клонирует репозиторий, ставит библиотеки, скачивает датасет и запускает все шаги.

## Запуск локально (VS Code / PyCharm / консоль)
```bash
git clone https://github.com/<user>/<repo>.git && cd <repo>
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# скачать ml-32m.zip, распаковать, положить ratings.csv и movies.csv в data/raw/
python main.py            # интерактивное меню
python main.py --all      # все шаги подряд
```
Быстрая отладка на части данных: `ML_MAX_ROWS=3000000 python main.py --all`
(Windows PowerShell: `$env:ML_MAX_ROWS=3000000; python main.py --all`).
Без датасета (синтетические данные, только для проверки кода): `python generate_sample_data.py`.

Требования: Python 3.10+, ~8 ГБ RAM для полного 32M (для 25M достаточно ~6 ГБ), ~3 ГБ диска.

## Структура
| Файл | Назначение |
|---|---|
| `main.py` | консольное меню (требование 7) |
| `src/config.py` | пути, константы |
| `src/utils.py` | замеры времени/памяти, сохранение JSON |
| `src/data_loader.py` | чанки, оптимизация типов, Parquet, аудит качества |
| `src/db.py` | схема SQLite (3НФ), загрузка, ER-диаграмма |
| `sql/queries.sql`, `src/sql_queries.py` | 10 SQL-запросов (JOIN, HAVING, CTE, оконные функции) |
| `src/pandas_vs_sql.py` | один расчёт: Pandas(CSV) / Pandas(Parquet) / SQL |
| `src/analysis.py`, `src/viz.py` | EDA и графики |
| `notebooks/colab_run.ipynb` | запуск в Colab |
| `docs/` | шаблоны отчёта и презентации |
| `outputs/` | результаты: CSV запросов, JSON с метриками, графики |

## Пункты меню
1. Аудит качества + память до/после оптимизации типов
2. CSV → Parquet (по чанкам) + сравнение CSV vs Parquet
3. База SQLite (3НФ) + ER-диаграмма
4. SQL-запросы Q1–Q10 (результаты в `outputs/q*.csv`)
5. Сравнение Pandas(CSV) vs Pandas(Parquet) vs SQL (время + совпадение результатов)
6. EDA и графики
7. Top-N фильмов в жанре (интерактивно)
8. Поиск фильма
9. Выполнить все шаги

Порядок первого запуска: 3 пунктами 1 → 2 → 3, затем остальные (или сразу пункт 9).

## Вклад участников
| Участник | Что сделал |
|---|---|
| Alina Y. | (загрузка по чанкам, оптимизация типов, Parquet, аудит качества данных, запуск полного прогона) |
| Bakhytnur U. | (заполнить: напр. БД, ER, SQL, сравнение SQL vs Pandas) |
| Dana K. | (заполнить: напр. EDA, графики, отчёт) |
