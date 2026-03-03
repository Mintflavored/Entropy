"""
EDP Server DNA — поведенческий профиль сервера.
Автоматически строит базлайны (среднее + σ) для каждой метрики по часу дня.
Определяет является ли текущее значение нормой, повышенным или аномалией.
"""

import json
import logging
import math
import os
from datetime import datetime

from core.edp.types import MetricValue

logger = logging.getLogger(__name__)

# Минимум замеров перед тем как начать выдавать verdict != "normal"
_MIN_SAMPLES = 10


class ServerDNA:
    """Поведенческий отпечаток сервера: учится что «нормально» для каждого часа."""

    def __init__(self, persist_path: str = ""):
        # 24 слота (по часу), для каждой метрики храним список значений
        self._data: dict[str, list[list[float]]] = {}
        self._persist_path = persist_path
        self._dirty = False
        self._update_counter = 0
        # Автосохранение каждые N обновлений
        self._save_every = 30

        if persist_path and os.path.exists(persist_path):
            self._load()

    def _ensure_metric(self, metric: str):
        """Инициализирует хранилище для метрики если нужно."""
        if metric not in self._data:
            self._data[metric] = [[] for _ in range(24)]

    def update(self, metric: str, value: float, hour: int = -1):
        """Добавляет значение метрики в профиль для текущего часа."""
        if hour < 0:
            hour = datetime.now().hour
        self._ensure_metric(metric)

        slot = self._data[metric][hour]
        slot.append(value)

        # Ограничиваем до 500 значений на слот (скользящее окно)
        if len(slot) > 500:
            self._data[metric][hour] = slot[-500:]

        self._dirty = True
        self._update_counter += 1

        if self._update_counter >= self._save_every:
            self._update_counter = 0
            self.save()

    def evaluate(self, metric: str, value: float, hour: int = -1) -> MetricValue:
        """Оценивает значение метрики относительно DNA-профиля."""
        if hour < 0:
            hour = datetime.now().hour
        self._ensure_metric(metric)

        slot = self._data[metric][hour]
        total_samples = len(slot)

        # Недостаточно данных — не делаем выводов
        if total_samples < _MIN_SAMPLES:
            return MetricValue(
                value=value,
                baseline=value,
                deviation=0.0,
                verdict="normal",
            )

        mean = sum(slot) / total_samples
        # Вычисляем стандартное отклонение
        variance = sum((x - mean) ** 2 for x in slot) / total_samples
        std = math.sqrt(variance) if variance > 0 else 0.001  # Защита от деления на 0

        deviation = (value - mean) / std
        abs_dev = abs(deviation)

        if abs_dev > 2.0:
            verdict = "anomaly"
        elif abs_dev > 1.0:
            verdict = "elevated"
        else:
            verdict = "normal"

        return MetricValue(
            value=value,
            baseline=round(mean, 2),
            deviation=round(deviation, 2),
            verdict=verdict,
        )

    def get_summary(self, hour: int = -1) -> str:
        """Создаёт текстовую сводку DNA для текущего часа (для AI)."""
        if hour < 0:
            hour = datetime.now().hour

        parts = []
        for metric in ("cpu", "ram", "pps", "jitter"):
            if metric not in self._data:
                continue
            slot = self._data[metric][hour]
            if len(slot) < _MIN_SAMPLES:
                continue
            mean = sum(slot) / len(slot)
            std = math.sqrt(sum((x - mean) ** 2 for x in slot) / len(slot))
            lo = max(0, mean - std)
            hi = mean + std
            parts.append(f"{metric}: {lo:.0f}-{hi:.0f} (σ={std:.1f})")

        if not parts:
            return "Недостаточно данных для DNA-профиля (нужно ~10 замеров)"

        return f"Обычно для {hour}:00: " + ", ".join(parts)

    def save(self):
        """Сохраняет DNA на диск."""
        if not self._persist_path or not self._dirty:
            return
        try:
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False)
            self._dirty = False
        except Exception as e:
            logger.error(f"DNA save error: {e}")

    def _load(self):
        """Загружает DNA с диска."""
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception as e:
            logger.warning(f"DNA load error, starting fresh: {e}")
            self._data = {}

    @property
    def has_enough_data(self) -> bool:
        """Есть ли достаточно данных хотя бы для одной метрики."""
        for metric_slots in self._data.values():
            for slot in metric_slots:
                if len(slot) >= _MIN_SAMPLES:
                    return True
        return False
