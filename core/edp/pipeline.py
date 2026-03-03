"""
EDP Pipeline — центральный оркестратор обработки данных.
Принимает сырые данные → прогоняет через 4 стадии → выдаёт обогащённый результат.

Стадии:
1. Parse — сырой dict → MetricSnapshot
2. Enrich — Server DNA оценивает каждую метрику (baseline, deviation, verdict)
3. Correlate — проверка правил корреляции → ThreatEvent'ы
4. Remember — проверка Incident Memory → IncidentMatch'и, сохранение новых инцидентов
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core.edp.bus import EDPBus
from core.edp.correlator import Correlator
from core.edp.memory import IncidentMemory, TemporalMemory
from core.edp.server_dna import ServerDNA
from core.edp.types import (
    AIContext,
    IncidentMatch,
    MetricSnapshot,
    MetricValue,
    ThreatEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Результат одного прогона Pipeline."""
    snapshot: MetricSnapshot
    events: list[ThreatEvent]
    incident_matches: list[IncidentMatch]
    ai_context: AIContext
    risk_data: tuple = ("LOW", "#00ff00", 0.0)  # (label, color, score)


class EDPPipeline:
    """4-стадийный Pipeline обработки данных."""

    def __init__(self, data_dir: str = ""):
        """
        Args:
            data_dir: директория для persistence (DNA, incidents).
                      Пустая строка — без persistence.
        """
        dna_path = os.path.join(data_dir, "server_dna.json") if data_dir else ""
        incidents_db = os.path.join(data_dir, "edp_incidents.db") if data_dir else "edp_incidents.db"

        self.dna = ServerDNA(persist_path=dna_path)
        self.temporal = TemporalMemory(max_size=360)
        self.incidents = IncidentMemory(db_path=incidents_db)
        self.correlator = Correlator()
        self.bus = EDPBus()

        self._prev_probes: list[str] = []
        self._prev_users_count: int = 0

        logger.info("EDP Pipeline initialized")

    def process(self, raw_data: dict) -> PipelineResult:
        """
        Главный метод: сырые данные → полный обогащённый результат.

        Args:
            raw_data: словарь с ключами: cpu, ram, pps, jitter,
                      users_count (opt), probes (opt)

        Returns:
            PipelineResult со snapshot, events, incident_matches, ai_context, risk_data
        """
        now = datetime.now()

        # === СТАДИЯ 1: Parse ===
        snapshot = self._parse(raw_data, now)

        # === СТАДИЯ 2: Enrich ===
        snapshot = self._enrich(snapshot)

        # === СТАДИЯ 3: Correlate ===
        events = self._correlate(snapshot)

        # === СТАДИЯ 4: Remember ===
        incident_matches = self._remember(snapshot, events)

        # Сохраняем в Temporal Memory
        self.temporal.add(snapshot)
        snapshot.events = events

        # Формируем AI Context + Risk Score
        ai_context = self._build_ai_context(snapshot, events, incident_matches)
        risk_data = self._calculate_risk(snapshot, events)

        result = PipelineResult(
            snapshot=snapshot,
            events=events,
            incident_matches=incident_matches,
            ai_context=ai_context,
            risk_data=risk_data,
        )

        # Публикуем через Bus
        self.bus.publish(snapshot)
        self.bus.publish_many(events)
        for match in incident_matches:
            self.bus.publish(match)

        return result

    def _parse(self, raw: dict, timestamp: datetime) -> MetricSnapshot:
        """Стадия 1: сырой dict → базовый MetricSnapshot."""
        probes = raw.get("probes", [])
        # Вычисляем какие пробы новые
        prev_ips = set(p if isinstance(p, str) else p.get("ip", "") for p in self._prev_probes)
        current_ips = [p if isinstance(p, str) else p.get("ip", "") for p in probes]
        new_probes = [ip for ip in current_ips if ip and ip not in prev_ips]
        self._prev_probes = probes

        users_count = raw.get("users_count", 0)
        users_delta = users_count - self._prev_users_count
        self._prev_users_count = users_count

        return MetricSnapshot(
            timestamp=timestamp,
            cpu=MetricValue(value=float(raw.get("cpu", 0))),
            ram=MetricValue(value=float(raw.get("ram", 0))),
            pps=MetricValue(value=float(raw.get("pps", 0))),
            jitter=MetricValue(value=float(raw.get("jitter", 0))),
            users_count=users_count,
            users_delta=users_delta,
            probes=probes,
            new_probes=new_probes,
        )

    def _enrich(self, snapshot: MetricSnapshot) -> MetricSnapshot:
        """Стадия 2: обогащение через Server DNA + вычисление дельт."""
        # На этом этапе текущий snapshot ещё НЕ в temporal → last = предыдущий
        prev = self.temporal.last
        hour = snapshot.timestamp.hour

        for metric_name in ("cpu", "ram", "pps", "jitter"):
            raw_val = getattr(snapshot, metric_name).value

            # Server DNA оценка
            enriched = self.dna.evaluate(metric_name, raw_val, hour)

            # Вычисляем дельту относительно предыдущего замера
            if prev:
                prev_val = getattr(prev, metric_name).value
                enriched.delta = round(raw_val - prev_val, 2)
                if prev_val != 0:
                    enriched.pct_change = round(
                        ((raw_val - prev_val) / prev_val) * 100, 1
                    )
                else:
                    enriched.pct_change = 0.0 if raw_val == 0 else 100.0

            # Обновляем DNA
            self.dna.update(metric_name, raw_val, hour)

            setattr(snapshot, metric_name, enriched)

        return snapshot

    def _correlate(self, snapshot: MetricSnapshot) -> list[ThreatEvent]:
        """Стадия 3: проверка правил корреляции."""
        prev = self.temporal.last  # Предыдущий (ещё не добавлен текущий)

        events = self.correlator.evaluate(snapshot, prev)

        # Генерируем anomaly-события для метрик с verdict == "anomaly"
        for metric_name in ("cpu", "ram", "pps", "jitter"):
            mv = getattr(snapshot, metric_name)
            if mv.verdict == "anomaly":
                events.append(ThreatEvent(
                    timestamp=snapshot.timestamp,
                    event_type="metric_anomaly",
                    severity="medium",
                    rule_id=f"dna_{metric_name}",
                    description=(
                        f"{metric_name.upper()} = {mv.value} "
                        f"(σ={mv.deviation:+.1f}, baseline={mv.baseline})"
                    ),
                    related_metrics={metric_name: mv.value},
                ))

        return events

    def _remember(self, snapshot: MetricSnapshot,
                  events: list[ThreatEvent]) -> list[IncidentMatch]:
        """Стадия 4: проверка Incident Memory + сохранение новых инцидентов."""
        # Проверяем совпадения с прошлыми инцидентами
        has_anomalies = any(
            getattr(snapshot, m).verdict == "anomaly"
            for m in ("cpu", "ram", "pps", "jitter")
        )
        has_correlations = bool(events)

        matches = []
        if has_anomalies or has_correlations:
            pattern = snapshot.to_pattern()
            deviations = snapshot.to_deviations()
            matches = self.incidents.match(pattern, deviations)

            if matches:
                logger.info(
                    f"⚡ Incident Memory: {len(matches)} match(es), "
                    f"best: {matches[0].similarity:.0%}"
                )

            # Сохраняем новый инцидент, если есть correlation events
            # и нет close match (чтобы не дублировать)
            if has_correlations and not any(m.similarity > 0.9 for m in matches):
                outcome = events[0].rule_id if events else "unknown"
                fp = self.incidents.create_fingerprint(
                    snapshot, outcome=outcome, outcome_source="auto"
                )
                self.incidents.save_incident(fp)

        return matches

    def _build_ai_context(self, snapshot: MetricSnapshot,
                          events: list[ThreatEvent],
                          matches: list[IncidentMatch]) -> AIContext:
        """Формирует оптимизированный контекст для AI."""
        # Собираем аномалии
        anomalies = []
        for metric_name in ("cpu", "ram", "pps", "jitter"):
            mv = getattr(snapshot, metric_name)
            if mv.verdict != "normal":
                direction = "↑" if mv.delta > 0 else "↓" if mv.delta < 0 else "→"
                anomaly_text = (
                    f"{metric_name.upper()}: {mv.value} "
                    f"({direction}{abs(mv.pct_change):.0f}%, "
                    f"σ={mv.deviation:+.1f}, baseline={mv.baseline})"
                )
                anomalies.append(anomaly_text)

        if snapshot.new_probes:
            anomalies.append(
                f"Новые SSH-пробы: {', '.join(snapshot.new_probes)} "
                f"({len(snapshot.new_probes)} шт.)"
            )

        return AIContext(
            anomalies=anomalies,
            correlations=events,
            server_dna_summary=self.dna.get_summary(snapshot.timestamp.hour),
            history_summary=self.temporal.get_summary(),
            incident_matches=matches,
            raw_metrics=snapshot.to_raw_dict(),
        )

    def get_ai_context(self) -> Optional[AIContext]:
        """Возвращает последний AI Context (для внешнего использования)."""
        last = self.temporal.last
        if not last:
            return None
        return self._build_ai_context(last, last.events, [])

    @staticmethod
    def _calculate_risk(snapshot: MetricSnapshot,
                        events: list[ThreatEvent]) -> tuple:
        """
        Вычисляет risk score на основе EDP-данных.
        Заменяет SecurityEngine.calculate_risk.
        Возвращает (label, color, score).
        """
        import math

        pps = snapshot.pps.value
        jitter = snapshot.jitter.value
        probe_count = len(snapshot.probes)

        # Базовый скор через atan (плавное насыщение) — совместимо со старой формулой
        p_score = math.atan(pps / 400) * (2 / math.pi) * 100
        j_score = math.atan(jitter / 30) * (2 / math.pi) * 100
        b_score = min(100, probe_count * 10)

        base_risk = (j_score * 0.4) + (p_score * 0.3) + (b_score * 0.3)

        # EDP-бонусы: корреляции и DNA-аномалии увеличивают скор
        severity_weights = {"critical": 15, "high": 10, "medium": 5, "low": 2}
        correlation_bonus = sum(
            severity_weights.get(e.severity, 0) for e in events
            if e.event_type == "correlation_fired"
        )

        anomaly_bonus = sum(
            5 for m in ("cpu", "ram", "pps", "jitter")
            if getattr(snapshot, m).verdict == "anomaly"
        )

        total = min(100, round(base_risk + correlation_bonus + anomaly_bonus, 1))

        if total >= 70:
            return "CRITICAL", "#ff4444", total
        elif total >= 40:
            return "HIGH", "#ff7744", total
        elif total >= 15:
            return "MEDIUM", "#ffaa00", total
        else:
            return "LOW", "#00ff00", total
