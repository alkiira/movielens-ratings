"""Вспомогательные функции: замер времени/памяти, сохранение результатов."""
import json
import time
from functools import wraps
from pathlib import Path

import psutil

from .config import OUT_DIR


def timed(func):
    """Декоратор: возвращает (результат, секунды)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        return res, time.perf_counter() - t0
    return wrapper


def rss_mb() -> float:
    """Текущая память процесса, МБ."""
    return psutil.Process().memory_info().rss / 1024 ** 2


def df_mb(df) -> float:
    """Память DataFrame, МБ (deep=True учитывает строки)."""
    return df.memory_usage(deep=True).sum() / 1024 ** 2


def file_mb(path: Path) -> float:
    return Path(path).stat().st_size / 1024 ** 2


def save_json(obj: dict, name: str) -> Path:
    """Сохранение результатов в постоянное хранилище (требование 5)."""
    path = OUT_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def load_json(name: str) -> dict:
    path = OUT_DIR / name
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:           # требование 6: обработка ошибок
        return {}
