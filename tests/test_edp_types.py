"""
Тесты EDP Types — валидация dataclass-ов и методов.
"""

from datetime import datetime
from core.edp.types import MetricValue, MetricSnapshot, ThreatEvent, IncidentFingerprint, IncidentMatch, AIContext


class TestMetricValue:
    def test_direction_stable(self):
        mv = MetricValue(value=50, pct_change=5)
        assert mv.direction == "stable"

    def test_direction_up(self):
        mv = MetricValue(value=50, delta=10, pct_change=25)
        assert mv.direction == "up"

    def test_direction_down(self):
        mv = MetricValue(value=50, delta=-10, pct_change=-25)
        assert mv.direction == "down"

    def test_direction_spike(self):
        mv = MetricValue(value=1200, delta=1000, pct_change=500)
        assert mv.direction == "spike"

    def test_direction_drop(self):
        mv = MetricValue(value=50, delta=-100, pct_change=-66)
        assert mv.direction == "drop"


class TestMetricSnapshot:
    def _make_snapshot(self, **overrides):
        defaults = dict(
            timestamp=datetime(2026, 3, 3, 12, 0),
            cpu=MetricValue(value=45, delta=5, pct_change=12),
            ram=MetricValue(value=60),
            pps=MetricValue(value=1200, delta=1000, pct_change=500),
            jitter=MetricValue(value=15, delta=10, pct_change=200),
        )
        defaults.update(overrides)
        return MetricSnapshot(**defaults)

    def test_to_pattern(self):
        snap = self._make_snapshot()
        pattern = snap.to_pattern()
        assert pattern["pps"] == "spike"
        assert pattern["jitter"] == "spike"  # pct_change=200 > 100 → spike
        assert pattern["probes"] == "none"

    def test_to_pattern_with_probes(self):
        snap = self._make_snapshot(new_probes=["1.2.3.4", "5.6.7.8"])
        assert snap.to_pattern()["probes"] == "new"

    def test_to_deviations(self):
        snap = self._make_snapshot(
            cpu=MetricValue(value=45, deviation=2.5),
            pps=MetricValue(value=1200, deviation=5.0),
        )
        devs = snap.to_deviations()
        assert devs["cpu"] == 2.5
        assert devs["pps"] == 5.0

    def test_to_raw_dict(self):
        snap = self._make_snapshot()
        raw = snap.to_raw_dict()
        assert raw["cpu"] == 45
        assert raw["pps"] == 1200


class TestThreatEvent:
    def test_to_dict(self):
        event = ThreatEvent(
            timestamp=datetime(2026, 3, 3, 12, 0),
            event_type="correlation_fired",
            severity="critical",
            rule_id="coordinated_attack",
            description="Test event",
        )
        d = event.to_dict()
        assert d["severity"] == "critical"
        assert d["rule_id"] == "coordinated_attack"


class TestIncidentMatch:
    def test_to_dict(self):
        fp = IncidentFingerprint(
            id="abc123",
            timestamp=datetime(2026, 3, 1),
            pattern={"pps": "spike"},
            deviations={"pps": 5.0},
            outcome="dpi_throttling",
            resolution="Switch to Reality",
            resolution_worked=True,
        )
        match = IncidentMatch(fingerprint=fp, similarity=0.89, message="Test match")
        d = match.to_dict()
        assert d["similarity"] == 89
        assert d["outcome"] == "dpi_throttling"
        assert d["resolution_worked"] is True


class TestAIContext:
    def test_to_prompt_text_with_anomalies(self):
        ctx = AIContext(
            anomalies=["PPS: 1200 (↑500%)"],
            server_dna_summary="CPU normally 25-35%",
        )
        text = ctx.to_prompt_text()
        assert "PPS: 1200" in text
        assert "АНОМАЛИИ" in text

    def test_to_prompt_text_empty(self):
        ctx = AIContext(raw_metrics={"cpu": 10})
        text = ctx.to_prompt_text()
        assert "в норме" in text.lower() or "норме" in text.lower()

    def test_to_prompt_text_with_incidents(self):
        fp = IncidentFingerprint(
            id="x", timestamp=datetime(2026, 1, 1),
            pattern={}, deviations={}, outcome="ddos",
            resolution="Block IP", resolution_worked=True,
        )
        ctx = AIContext(
            anomalies=["test"],
            incident_matches=[IncidentMatch(fp, 0.9, "90% match")],
        )
        text = ctx.to_prompt_text()
        assert "INCIDENT MEMORY" in text
        assert "Block IP" in text
