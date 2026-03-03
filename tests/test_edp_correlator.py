"""
Тесты EDP Correlator — правила корреляции.
"""

from datetime import datetime

from core.edp.correlator import Correlator
from core.edp.types import MetricValue, MetricSnapshot


def _make_snapshot(**kwargs):
    """Хелпер: создаёт снэпшот с заданными параметрами."""
    defaults = {
        "cpu_val": 30, "cpu_pct": 0,
        "ram_val": 50, "ram_pct": 0,
        "pps_val": 200, "pps_pct": 0,
        "jitter_val": 5, "jitter_pct": 0,
        "users_count": 10, "users_delta": 0,
        "new_probes": [],
    }
    defaults.update(kwargs)
    d = defaults
    return MetricSnapshot(
        timestamp=datetime(2026, 3, 3, 12, 0),
        cpu=MetricValue(value=d["cpu_val"], pct_change=d["cpu_pct"]),
        ram=MetricValue(value=d["ram_val"], pct_change=d["ram_pct"]),
        pps=MetricValue(value=d["pps_val"], pct_change=d["pps_pct"]),
        jitter=MetricValue(value=d["jitter_val"], pct_change=d["jitter_pct"]),
        users_count=d["users_count"],
        users_delta=d["users_delta"],
        new_probes=d["new_probes"],
    )


class TestCorrelator:
    def setup_method(self):
        self.correlator = Correlator()

    def test_no_events_on_normal(self):
        """Нормальные метрики — ничего не срабатывает."""
        snap = _make_snapshot()
        events = self.correlator.evaluate(snap)
        assert len(events) == 0

    def test_coordinated_attack(self):
        """PPS spike + jitter spike + новые пробы = координированная атака."""
        snap = _make_snapshot(
            pps_val=1200, pps_pct=500,
            jitter_val=15, jitter_pct=200,
            new_probes=["1.1.1.1", "2.2.2.2", "3.3.3.3"],
        )
        events = self.correlator.evaluate(snap)
        rule_ids = [e.rule_id for e in events]
        assert "coordinated_attack" in rule_ids
        assert events[0].severity == "critical"

    def test_dpi_throttling(self):
        """PPS drop + jitter double + users stable = DPI throttling."""
        snap = _make_snapshot(
            pps_val=50, pps_pct=-75,
            jitter_val=20, jitter_pct=300,
            users_count=10, users_delta=0,
        )
        events = self.correlator.evaluate(snap)
        rule_ids = [e.rule_id for e in events]
        assert "dpi_throttling" in rule_ids

    def test_cryptominer(self):
        """CPU + RAM high + users/PPS stable = майнер."""
        snap = _make_snapshot(
            cpu_val=90, cpu_pct=5,
            ram_val=85, ram_pct=3,
            pps_val=200, pps_pct=2,
            users_count=10, users_delta=0,
        )
        events = self.correlator.evaluate(snap)
        rule_ids = [e.rule_id for e in events]
        assert "cryptominer" in rule_ids

    def test_mass_disconnect(self):
        """Users массово ушли + jitter double."""
        prev = _make_snapshot(users_count=20)
        snap = _make_snapshot(
            users_count=5, users_delta=-15,
            jitter_val=30, jitter_pct=500,
        )
        events = self.correlator.evaluate(snap, prev)
        rule_ids = [e.rule_id for e in events]
        assert "mass_disconnect" in rule_ids

    def test_partial_conditions_no_fire(self):
        """Только PPS spike без остальных — coordinated_attack не срабатывает."""
        snap = _make_snapshot(pps_val=1200, pps_pct=500)
        events = self.correlator.evaluate(snap)
        rule_ids = [e.rule_id for e in events]
        assert "coordinated_attack" not in rule_ids
