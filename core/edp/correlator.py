"""
EDP Correlator — корреляционный движок.
Декларативные правила, срабатывающие при совпадении нескольких сигналов.
"""

import logging
from datetime import datetime

from core.edp.types import MetricSnapshot, ThreatEvent

logger = logging.getLogger(__name__)


class CorrelationRule:
    """Одно правило корреляции с набором условий."""

    def __init__(self, rule_id: str, name: str, severity: str,
                 description: str, conditions: list):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.description = description
        # Каждое условие — callable(snapshot, prev_snapshot) -> bool
        self.conditions = conditions

    def evaluate(self, current: MetricSnapshot,
                 previous: MetricSnapshot = None) -> bool:
        """Проверяет все условия правила. Возвращает True если все совпали."""
        try:
            return all(cond(current, previous) for cond in self.conditions)
        except Exception as e:
            logger.debug(f"Rule {self.rule_id} eval error: {e}")
            return False


# === Фабрика условий ===

def _pps_spike(snap, prev):
    """PPS вырос более чем вдвое."""
    return snap.pps.pct_change > 100

def _pps_drop(snap, prev):
    """PPS упал более чем на 30%."""
    return snap.pps.pct_change < -30

def _jitter_spike(snap, prev):
    """Jitter вырос более чем на 50%."""
    return snap.jitter.pct_change > 50

def _jitter_double(snap, prev):
    """Jitter удвоился."""
    return snap.jitter.pct_change > 100

def _new_probes(snap, prev):
    """Есть новые SSH-пробы (3+)."""
    return len(snap.new_probes) >= 3

def _users_stable(snap, prev):
    """Пользователи стабильны (дельта ~0)."""
    return abs(snap.users_delta) <= 1

def _users_mass_drop(snap, prev):
    """Половина пользователей отключились."""
    if prev is None or prev.users_count == 0:
        return False
    return snap.users_delta < 0 and abs(snap.users_delta) > prev.users_count * 0.5

def _cpu_high(snap, prev):
    """CPU выше 85%."""
    return snap.cpu.value > 85

def _ram_high(snap, prev):
    """RAM выше 80%."""
    return snap.ram.value > 80

def _pps_stable(snap, prev):
    """PPS стабилен (изменение < 15%)."""
    return abs(snap.pps.pct_change) < 15


# === Встроенные правила ===

BUILTIN_RULES = [
    CorrelationRule(
        rule_id="coordinated_attack",
        name="Координированная атака",
        severity="critical",
        description="DDoS + brute-force: PPS spike, рост jitter, новые SSH-пробы",
        conditions=[_pps_spike, _jitter_spike, _new_probes],
    ),
    CorrelationRule(
        rule_id="dpi_throttling",
        name="DPI Throttling",
        severity="high",
        description="Подозрение на DPI: PPS падает, jitter растёт, пользователи на месте",
        conditions=[_pps_drop, _jitter_double, _users_stable],
    ),
    CorrelationRule(
        rule_id="cryptominer",
        name="Майнер на сервере",
        severity="critical",
        description="CPU и RAM высоко, но трафик и пользователи стабильны",
        conditions=[_cpu_high, _ram_high, _users_stable, _pps_stable],
    ),
    CorrelationRule(
        rule_id="mass_disconnect",
        name="Массовое отключение",
        severity="high",
        description="Массовое отключение пользователей с ростом jitter — возможная блокировка",
        conditions=[_users_mass_drop, _jitter_double],
    ),
]


class Correlator:
    """Движок корреляции — проверяет правила на каждом цикле."""

    def __init__(self, rules: list[CorrelationRule] = None):
        self._rules = rules if rules is not None else list(BUILTIN_RULES)

    def evaluate(self, current: MetricSnapshot,
                 previous: MetricSnapshot = None) -> list[ThreatEvent]:
        """Проверяет все правила, возвращает список сработавших событий."""
        events = []
        for rule in self._rules:
            if rule.evaluate(current, previous):
                event = ThreatEvent(
                    timestamp=current.timestamp,
                    event_type="correlation_fired",
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    description=f"{rule.name}: {rule.description}",
                    related_metrics=current.to_raw_dict(),
                )
                events.append(event)
                logger.warning(
                    f"🔴 Correlation [{rule.severity.upper()}]: {rule.name}"
                )
        return events

    def add_rule(self, rule: CorrelationRule):
        """Добавляет пользовательское правило."""
        self._rules.append(rule)
