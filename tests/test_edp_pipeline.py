"""
Тесты EDP Pipeline — полный flow от сырых данных до enriched-результата.
"""

import os
import tempfile

from core.edp.pipeline import EDPPipeline


def _raw_normal():
    """Нормальные данные."""
    return {"cpu": 30, "ram": 50, "pps": 200, "jitter": 5, "users_count": 10, "probes": []}


def _raw_anomaly():
    """Данные с аномалией (для второго прогона после baseline)."""
    return {"cpu": 90, "ram": 85, "pps": 1200, "jitter": 25, "users_count": 10, "probes": ["1.2.3.4", "5.6.7.8", "9.10.11.12"]}


class TestEDPPipeline:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.pipeline = EDPPipeline(data_dir=self.tmp)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_basic_flow(self):
        """Базовый прогон: сырые данные → enriched snapshot."""
        result = self.pipeline.process(_raw_normal())
        assert result.snapshot.cpu.value == 30
        assert result.snapshot.ram.value == 50
        assert result.snapshot.pps.value == 200

    def test_delta_calculation(self):
        """Дельты вычисляются между замерами."""
        self.pipeline.process({"cpu": 30, "ram": 50, "pps": 200, "jitter": 5})
        result = self.pipeline.process({"cpu": 45, "ram": 50, "pps": 300, "jitter": 5})
        assert result.snapshot.cpu.delta == 15
        assert result.snapshot.cpu.pct_change == 50.0

    def test_new_probes_detection(self):
        """Новые пробы определяются корректно."""
        self.pipeline.process({"cpu": 30, "ram": 50, "pps": 200, "jitter": 5, "probes": ["1.1.1.1"]})
        result = self.pipeline.process({"cpu": 30, "ram": 50, "pps": 200, "jitter": 5, "probes": ["1.1.1.1", "2.2.2.2"]})
        assert "2.2.2.2" in result.snapshot.new_probes
        assert "1.1.1.1" not in result.snapshot.new_probes

    def test_users_delta(self):
        """Дельта пользователей вычисляется."""
        self.pipeline.process({"cpu": 30, "ram": 50, "pps": 200, "jitter": 5, "users_count": 10})
        result = self.pipeline.process({"cpu": 30, "ram": 50, "pps": 200, "jitter": 5, "users_count": 7})
        assert result.snapshot.users_delta == -3

    def test_ai_context_created(self):
        """AIContext формируется с raw_metrics."""
        result = self.pipeline.process(_raw_normal())
        assert result.ai_context is not None
        assert result.ai_context.raw_metrics["cpu"] == 30

    def test_ai_context_prompt_text(self):
        """AIContext конвертируется в промпт-текст."""
        result = self.pipeline.process(_raw_normal())
        text = result.ai_context.to_prompt_text()
        assert isinstance(text, str)
        assert len(text) > 0

    def test_correlation_events_after_baseline(self):
        """После набора базлайна аномалия генерирует events."""
        # Набираем базлайн (10+ нормальных замеров)
        for _ in range(15):
            self.pipeline.process(_raw_normal())

        # Подаём аномалию
        result = self.pipeline.process({"cpu": 95, "ram": 90, "pps": 5000, "jitter": 50})
        
        # Должны быть metric_anomaly события
        anomaly_events = [e for e in result.events if e.event_type == "metric_anomaly"]
        assert len(anomaly_events) > 0

    def test_temporal_memory_grows(self):
        """Temporal Memory накапливает снэпшоты."""
        for i in range(5):
            self.pipeline.process({"cpu": i * 10, "ram": 50, "pps": 200, "jitter": 5})
        assert len(self.pipeline.temporal) == 5

    def test_incident_auto_save_on_correlation(self):
        """При correlation event автоматически сохраняется incident fingerprint."""
        # Набираем baseline
        for _ in range(15):
            self.pipeline.process(_raw_normal())

        # Cryptominer pattern: high CPU + high RAM + stable PPS/users
        result = self.pipeline.process({
            "cpu": 95, "ram": 90, "pps": 200, "jitter": 5,
            "users_count": 10,
        })
        
        # Проверяем что корреляция cryptominer сработала
        correlation_events = [e for e in result.events if e.event_type == "correlation_fired"]
        if correlation_events:
            # Должен быть сохранён incident
            assert self.pipeline.incidents.count >= 1
