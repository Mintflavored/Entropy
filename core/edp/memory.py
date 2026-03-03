"""
EDP Memory — Temporal Memory + Incident Memory.
Temporal: кольцевой буфер снэпшотов (in-memory).
Incident: SQLite-хранилище fingerprints инцидентов с pattern matching.
"""

import json
import logging
import sqlite3
import uuid
from collections import deque
from datetime import datetime
from typing import Optional

from core.edp.types import IncidentFingerprint, IncidentMatch, MetricSnapshot

logger = logging.getLogger(__name__)

# Направления для pattern matching
_DIRECTIONS = ("spike", "up", "stable", "down", "drop", "new", "none")


class TemporalMemory:
    """Кольцевой буфер снэпшотов — in-memory time-series хранилище."""

    def __init__(self, max_size: int = 360):
        self._buffer: deque[MetricSnapshot] = deque(maxlen=max_size)

    def add(self, snapshot: MetricSnapshot):
        """Добавляет снэпшот в буфер."""
        self._buffer.append(snapshot)

    @property
    def last(self) -> Optional[MetricSnapshot]:
        """Последний снэпшот."""
        return self._buffer[-1] if self._buffer else None

    @property
    def previous(self) -> Optional[MetricSnapshot]:
        """Предпоследний снэпшот (для вычисления дельт)."""
        return self._buffer[-2] if len(self._buffer) >= 2 else None

    def get_history(self, count: int = 60) -> list[MetricSnapshot]:
        """Возвращает последние N снэпшотов."""
        items = list(self._buffer)
        return items[-count:] if len(items) > count else items

    def get_metric_values(self, metric: str, count: int = 60) -> list[float]:
        """Возвращает список значений одной метрики за последние N замеров."""
        history = self.get_history(count)
        result = []
        for snap in history:
            mv = getattr(snap, metric, None)
            if mv is not None:
                result.append(mv.value if hasattr(mv, "value") else float(mv))
        return result

    def get_trend(self, metric: str, window: int = 10) -> str:
        """Определяет тренд метрики: 'up' | 'down' | 'stable'."""
        values = self.get_metric_values(metric, window)
        if len(values) < 3:
            return "stable"

        # Линейный тренд: среднее первой vs второй половины
        mid = len(values) // 2
        first_half = sum(values[:mid]) / mid
        second_half = sum(values[mid:]) / (len(values) - mid)

        if first_half == 0:
            return "stable"

        change_pct = ((second_half - first_half) / first_half) * 100
        if change_pct > 15:
            return "up"
        if change_pct < -15:
            return "down"
        return "stable"

    def get_summary(self, count: int = 60) -> str:
        """Текстовая сводка истории для AI."""
        values = {
            m: self.get_metric_values(m, count)
            for m in ("cpu", "ram", "pps", "jitter")
        }

        parts = []
        for metric, vals in values.items():
            if not vals:
                continue
            avg = sum(vals) / len(vals)
            peak = max(vals)
            parts.append(f"{metric}: avg {avg:.0f}, peak {peak:.0f}")

        if not parts:
            return ""

        return f"За последние {count} замеров: " + ", ".join(parts)

    def __len__(self) -> int:
        return len(self._buffer)


class IncidentMemory:
    """SQLite-хранилище fingerprints инцидентов с pattern matching."""

    def __init__(self, db_path: str = "edp_incidents.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        """Создаёт таблицу если не существует."""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incident_memory (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    deviations TEXT NOT NULL,
                    outcome TEXT DEFAULT 'unknown',
                    outcome_source TEXT DEFAULT 'auto',
                    resolution TEXT,
                    resolution_worked INTEGER DEFAULT 0,
                    match_threshold REAL DEFAULT 0.75
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"IncidentMemory DB init error: {e}")

    def save_incident(self, fingerprint: IncidentFingerprint):
        """Сохраняет fingerprint инцидента в БД."""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT OR REPLACE INTO incident_memory
                   (id, timestamp, pattern, deviations, outcome, outcome_source,
                    resolution, resolution_worked, match_threshold)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fingerprint.id,
                    fingerprint.timestamp.isoformat(),
                    json.dumps(fingerprint.pattern, ensure_ascii=False),
                    json.dumps(fingerprint.deviations, ensure_ascii=False),
                    fingerprint.outcome,
                    fingerprint.outcome_source,
                    fingerprint.resolution,
                    1 if fingerprint.resolution_worked else 0,
                    fingerprint.match_threshold,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"Incident saved: {fingerprint.id} ({fingerprint.outcome})")
        except Exception as e:
            logger.error(f"IncidentMemory save error: {e}")

    def match(self, current_pattern: dict, current_deviations: dict) -> list[IncidentMatch]:
        """Сравнивает текущую ситуацию со всеми сохранёнными инцидентами."""
        incidents = self._load_all()
        matches = []

        for fp in incidents:
            similarity = self._calculate_similarity(current_pattern, fp.pattern,
                                                     current_deviations, fp.deviations)
            if similarity >= fp.match_threshold:
                msg = (
                    f"Совпадение {similarity:.0%} с инцидентом от "
                    f"{fp.timestamp.strftime('%d.%m.%Y %H:%M')}. "
                    f"Тогда это был: {fp.outcome}"
                )
                matches.append(IncidentMatch(
                    fingerprint=fp,
                    similarity=similarity,
                    message=msg,
                ))

        return sorted(matches, key=lambda m: m.similarity, reverse=True)

    def update_outcome(self, incident_id: str, outcome: str,
                       resolution: Optional[str] = None,
                       resolution_worked: bool = False):
        """Обновляет outcome инцидента после разбора."""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """UPDATE incident_memory
                   SET outcome = ?, resolution = ?, resolution_worked = ?
                   WHERE id = ?""",
                (outcome, resolution, 1 if resolution_worked else 0, incident_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"IncidentMemory update error: {e}")

    def create_fingerprint(self, snapshot: MetricSnapshot,
                           outcome: str = "unknown",
                           outcome_source: str = "auto") -> IncidentFingerprint:
        """Создаёт fingerprint из текущего снэпшота."""
        return IncidentFingerprint(
            id=str(uuid.uuid4())[:8],
            timestamp=snapshot.timestamp,
            pattern=snapshot.to_pattern(),
            deviations=snapshot.to_deviations(),
            outcome=outcome,
            outcome_source=outcome_source,
        )

    def _load_all(self) -> list[IncidentFingerprint]:
        """Загружает все инциденты из БД."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute("SELECT * FROM incident_memory ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()

            return [
                IncidentFingerprint(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    pattern=json.loads(row[2]),
                    deviations=json.loads(row[3]),
                    outcome=row[4],
                    outcome_source=row[5],
                    resolution=row[6],
                    resolution_worked=bool(row[7]),
                    match_threshold=row[8],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"IncidentMemory load error: {e}")
            return []

    @staticmethod
    def _calculate_similarity(pattern_a: dict, pattern_b: dict,
                               deviations_a: dict, deviations_b: dict) -> float:
        """
        Вычисляет сходство двух инцидентов.
        Комбинация: совпадение направлений (70%) + близость отклонений (30%).
        """
        # 1. Direction matching (70% веса)
        common_keys = set(pattern_a.keys()) & set(pattern_b.keys())
        if not common_keys:
            return 0.0

        direction_matches = sum(
            1 for k in common_keys if pattern_a.get(k) == pattern_b.get(k)
        )
        direction_score = direction_matches / len(common_keys)

        # 2. Deviation proximity (30% веса)
        dev_keys = set(deviations_a.keys()) & set(deviations_b.keys())
        if dev_keys:
            dev_diffs = []
            for k in dev_keys:
                a = deviations_a.get(k, 0)
                b = deviations_b.get(k, 0)
                max_val = max(abs(a), abs(b), 1.0)
                dev_diffs.append(1.0 - min(abs(a - b) / max_val, 1.0))
            deviation_score = sum(dev_diffs) / len(dev_diffs)
        else:
            deviation_score = 0.5  # Нет данных — нейтральный скор

        return direction_score * 0.7 + deviation_score * 0.3

    @property
    def count(self) -> int:
        """Количество сохранённых инцидентов."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM incident_memory")
            result = cursor.fetchone()[0]
            conn.close()
            return result
        except Exception:
            return 0
