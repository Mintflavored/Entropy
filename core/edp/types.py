"""
EDP Types — типизированные структуры данных протокола.
Все данные в EDP передаются через эти dataclass-ы, а не через сырые dict-ы.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MetricValue:
    """Метрика с полным контекстом: текущее значение, дельта, базлайн и вердикт."""
    value: float
    delta: float = 0.0              # Изменение с прошлого замера
    pct_change: float = 0.0         # Процент изменения
    baseline: float = 0.0           # Server DNA: среднее для этого часа
    deviation: float = 0.0          # Отклонение в σ (стандартных отклонениях)
    verdict: str = "normal"         # "normal" | "elevated" | "anomaly"

    @property
    def direction(self) -> str:
        """Направление изменения для pattern matching."""
        if abs(self.pct_change) < 10:
            return "stable"
        if self.pct_change >= 100:
            return "spike"
        if self.pct_change <= -50:
            return "drop"
        return "up" if self.delta > 0 else "down"


@dataclass
class MetricSnapshot:
    """Один замер — основной тип данных EDP. Полностью обогащённый снэпшот."""
    timestamp: datetime
    cpu: MetricValue
    ram: MetricValue
    pps: MetricValue
    jitter: MetricValue
    users_count: int = 0
    users_delta: int = 0
    probes: list = field(default_factory=list)
    new_probes: list = field(default_factory=list)
    events: list = field(default_factory=list)

    def to_pattern(self) -> dict:
        """Создаёт паттерн направлений для Incident Memory matching."""
        return {
            "cpu": self.cpu.direction,
            "ram": self.ram.direction,
            "pps": self.pps.direction,
            "jitter": self.jitter.direction,
            "probes": "new" if self.new_probes else "none",
        }

    def to_deviations(self) -> dict:
        """Создаёт вектор отклонений для Incident Memory matching."""
        return {
            "cpu": abs(self.cpu.deviation),
            "ram": abs(self.ram.deviation),
            "pps": abs(self.pps.deviation),
            "jitter": abs(self.jitter.deviation),
        }

    def to_raw_dict(self) -> dict:
        """Обратная совместимость: конвертация в raw dict для legacy-компонентов."""
        return {
            "cpu": self.cpu.value,
            "ram": self.ram.value,
            "pps": self.pps.value,
            "jitter": self.jitter.value,
            "users_count": self.users_count,
        }


@dataclass
class ThreatEvent:
    """Событие угрозы от корреляционного движка или другого источника."""
    timestamp: datetime
    event_type: str                 # "correlation_fired" | "metric_anomaly" | ...
    severity: str                   # "critical" | "high" | "medium" | "low" | "info"
    rule_id: str                    # ID правила или источника
    description: str                # Человекочитаемое описание
    related_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация для QML."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "rule_id": self.rule_id,
            "description": self.description,
        }


@dataclass
class IncidentFingerprint:
    """Слепок инцидента — EDP запоминает паттерн для распознавания в будущем."""
    id: str                         # UUID
    timestamp: datetime
    pattern: dict                   # {metric: direction} — напр. {"pps": "spike", "jitter": "up"}
    deviations: dict                # {metric: sigma} — напр. {"pps": 5.0, "jitter": 2.3}
    outcome: str = "unknown"        # "dpi_throttling" | "ddos" | "cryptominer" | "false_alarm" | ...
    outcome_source: str = "auto"    # "ai_analysis" | "user_feedback" | "auto_resolved"
    resolution: Optional[str] = None  # "Переключил на Reality" | None
    resolution_worked: bool = False
    match_threshold: float = 0.75   # Порог совпадения для matching


@dataclass
class IncidentMatch:
    """Результат сравнения текущей ситуации с Incident Memory."""
    fingerprint: IncidentFingerprint
    similarity: float               # 0.0 - 1.0
    message: str                    # Человекочитаемое сообщение

    def to_dict(self) -> dict:
        """Сериализация для QML."""
        return {
            "similarity": round(self.similarity * 100),
            "message": self.message,
            "outcome": self.fingerprint.outcome,
            "resolution": self.fingerprint.resolution,
            "resolution_worked": self.fingerprint.resolution_worked,
            "incident_date": self.fingerprint.timestamp.isoformat(),
        }


@dataclass
class AIContext:
    """Оптимизированный контекст для AI — формируется EDP Pipeline автоматически."""
    anomalies: list = field(default_factory=list)
    correlations: list = field(default_factory=list)
    server_dna_summary: str = ""
    history_summary: str = ""
    incident_matches: list = field(default_factory=list)
    raw_metrics: dict = field(default_factory=dict)

    def to_prompt_text(self) -> str:
        """Формирует оптимизированный текст для LLM промпта."""
        parts = []

        if self.anomalies:
            parts.append("⚠ АНОМАЛИИ:")
            for a in self.anomalies:
                parts.append(f"  - {a}")

        if self.correlations:
            parts.append("\n🔴 КОРРЕЛЯЦИИ:")
            for c in self.correlations:
                sev = c.severity.upper() if isinstance(c, ThreatEvent) else str(c)
                desc = c.description if isinstance(c, ThreatEvent) else str(c)
                parts.append(f"  - [{sev}] {desc}")

        if self.incident_matches:
            parts.append("\n🧠 INCIDENT MEMORY:")
            for m in self.incident_matches:
                if isinstance(m, IncidentMatch):
                    parts.append(f"  - {m.message}")
                    if m.fingerprint.resolution:
                        status = "✅" if m.fingerprint.resolution_worked else "❌"
                        parts.append(f"    Прошлое решение: {m.fingerprint.resolution} {status}")

        if self.server_dna_summary:
            parts.append(f"\n📊 SERVER DNA: {self.server_dna_summary}")

        if self.history_summary:
            parts.append(f"📈 ИСТОРИЯ: {self.history_summary}")

        # Если нет аномалий — отправляем сводку
        if not parts:
            parts.append("Все метрики в норме. Аномалий не обнаружено.")
            if self.raw_metrics:
                metrics_str = ", ".join(f"{k}: {v}" for k, v in self.raw_metrics.items())
                parts.append(f"Текущие значения: {metrics_str}")

        return "\n".join(parts)
