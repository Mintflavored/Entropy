"""
Тесты EDP Memory — Temporal Memory + Incident Memory.
"""

import os
import tempfile
from datetime import datetime

from core.edp.memory import TemporalMemory, IncidentMemory
from core.edp.types import MetricValue, MetricSnapshot, IncidentFingerprint


def _make_snapshot(cpu=30, pps=200, jitter=5, timestamp=None):
    """Хелпер для создания снэпшотов."""
    return MetricSnapshot(
        timestamp=timestamp or datetime.now(),
        cpu=MetricValue(value=cpu, delta=0, pct_change=0, deviation=0),
        ram=MetricValue(value=60),
        pps=MetricValue(value=pps, delta=0, pct_change=0, deviation=0),
        jitter=MetricValue(value=jitter, delta=0, pct_change=0, deviation=0),
    )


class TestTemporalMemory:
    def test_add_and_last(self):
        mem = TemporalMemory(max_size=10)
        snap = _make_snapshot(cpu=45)
        mem.add(snap)
        assert mem.last.cpu.value == 45

    def test_previous(self):
        mem = TemporalMemory(max_size=10)
        mem.add(_make_snapshot(cpu=10))
        mem.add(_make_snapshot(cpu=20))
        assert mem.previous.cpu.value == 10
        assert mem.last.cpu.value == 20

    def test_previous_empty(self):
        mem = TemporalMemory()
        assert mem.previous is None

    def test_buffer_overflow(self):
        mem = TemporalMemory(max_size=5)
        for i in range(10):
            mem.add(_make_snapshot(cpu=i))
        assert len(mem) == 5
        assert mem.last.cpu.value == 9

    def test_get_history(self):
        mem = TemporalMemory()
        for i in range(5):
            mem.add(_make_snapshot(cpu=i * 10))
        history = mem.get_history(3)
        assert len(history) == 3
        assert history[-1].cpu.value == 40

    def test_get_metric_values(self):
        mem = TemporalMemory()
        for v in [10, 20, 30]:
            mem.add(_make_snapshot(cpu=v))
        vals = mem.get_metric_values("cpu", 10)
        assert vals == [10, 20, 30]

    def test_get_trend_up(self):
        mem = TemporalMemory()
        for v in [10, 15, 20, 25, 30, 40, 50, 60, 70, 80]:
            mem.add(_make_snapshot(cpu=v))
        assert mem.get_trend("cpu", 10) == "up"

    def test_get_trend_stable(self):
        mem = TemporalMemory()
        for v in [50, 51, 49, 50, 52, 48, 50, 51, 49, 50]:
            mem.add(_make_snapshot(cpu=v))
        assert mem.get_trend("cpu", 10) == "stable"

    def test_get_trend_insufficient_data(self):
        mem = TemporalMemory()
        mem.add(_make_snapshot(cpu=50))
        assert mem.get_trend("cpu") == "stable"

    def test_get_summary(self):
        mem = TemporalMemory()
        for v in [10, 20, 30]:
            mem.add(_make_snapshot(cpu=v))
        summary = mem.get_summary(10)
        assert "cpu" in summary
        assert "avg" in summary


class TestIncidentMemory:
    def _get_db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        return path

    def test_save_and_count(self):
        db = self._get_db_path()
        try:
            mem = IncidentMemory(db_path=db)
            fp = IncidentFingerprint(
                id="test1",
                timestamp=datetime(2026, 3, 1),
                pattern={"pps": "spike", "jitter": "up", "probes": "new"},
                deviations={"pps": 5.0, "jitter": 2.3},
                outcome="dpi_throttling",
            )
            mem.save_incident(fp)
            assert mem.count == 1
        finally:
            os.unlink(db)

    def test_match_high_similarity(self):
        db = self._get_db_path()
        try:
            mem = IncidentMemory(db_path=db)
            fp = IncidentFingerprint(
                id="inc1",
                timestamp=datetime(2026, 3, 1),
                pattern={"pps": "spike", "jitter": "up", "cpu": "stable", "probes": "new"},
                deviations={"pps": 5.0, "jitter": 2.0, "cpu": 0.5},
                outcome="coordinated_attack",
                match_threshold=0.7,
            )
            mem.save_incident(fp)

            # Тот же паттерн
            matches = mem.match(
                {"pps": "spike", "jitter": "up", "cpu": "stable", "probes": "new"},
                {"pps": 5.0, "jitter": 2.0, "cpu": 0.5},
            )
            assert len(matches) == 1
            assert matches[0].similarity >= 0.9
        finally:
            os.unlink(db)

    def test_match_no_match(self):
        db = self._get_db_path()
        try:
            mem = IncidentMemory(db_path=db)
            fp = IncidentFingerprint(
                id="inc1",
                timestamp=datetime(2026, 3, 1),
                pattern={"pps": "spike", "jitter": "up"},
                deviations={"pps": 5.0},
                outcome="ddos",
            )
            mem.save_incident(fp)

            # Совсем другой паттерн
            matches = mem.match(
                {"pps": "stable", "jitter": "down", "cpu": "stable"},
                {"pps": 0.1},
            )
            assert len(matches) == 0
        finally:
            os.unlink(db)

    def test_update_outcome(self):
        db = self._get_db_path()
        try:
            mem = IncidentMemory(db_path=db)
            fp = IncidentFingerprint(
                id="inc1",
                timestamp=datetime(2026, 3, 1),
                pattern={"pps": "spike"},
                deviations={"pps": 5.0},
            )
            mem.save_incident(fp)
            mem.update_outcome("inc1", "false_alarm", "Ignored", True)
            assert mem.count == 1
        finally:
            os.unlink(db)

    def test_create_fingerprint(self):
        db = self._get_db_path()
        try:
            mem = IncidentMemory(db_path=db)
            snap = MetricSnapshot(
                timestamp=datetime(2026, 3, 3),
                cpu=MetricValue(value=80, deviation=3.0, pct_change=50, delta=20),
                ram=MetricValue(value=60),
                pps=MetricValue(value=1200, deviation=5.0, pct_change=500, delta=1000),
                jitter=MetricValue(value=15, deviation=2.0, pct_change=200, delta=10),
                new_probes=["1.2.3.4"],
            )
            fp = mem.create_fingerprint(snap, outcome="test")
            assert fp.pattern["pps"] == "spike"
            assert fp.pattern["probes"] == "new"
            assert fp.deviations["pps"] == 5.0
        finally:
            os.unlink(db)
