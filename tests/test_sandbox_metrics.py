import pytest
import os
import json
from ai.sandbox_metrics import MetricsStorage, ExperimentResult

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_sandbox_metrics.db"
    return str(db_file)

@pytest.fixture
def storage(temp_db):
    return MetricsStorage(db_path=temp_db)

def test_storage_init(storage, temp_db):
    assert os.path.exists(temp_db)
    count = storage.get_experiment_count()
    assert count == 0

def test_save_and_get_experiment(storage):
    result = ExperimentResult(
        id=None,
        timestamp="2026-01-01T12:00:00",
        config={"cpu": "test"},
        latency_ms=10.5,
        download_mbps=100.0,
        jitter_ms=2.0,
        packet_loss_pct=0.0,
        dns_ms=5.0,
        cpu_usage=10.0,
        memory_mb=512.0,
        score=95.5,
        upload_mbps=50.0,
        tcp_handshake_ms=10.0,
        tls_handshake_ms=20.0,
        bufferbloat_ms=5.0,
        stability_cv=1.0,
        ai_reasoning="Test"
    )
    
    saved_id = storage.save_experiment(result)
    assert saved_id > 0
    
    assert storage.get_experiment_count() == 1
    
    # test get all
    all_experiments = storage.get_all_experiments()
    assert len(all_experiments) == 1
    saved = all_experiments[0]
    
    assert saved.id == saved_id
    assert saved.timestamp == "2026-01-01T12:00:00"
    assert saved.latency_ms == 10.5
    assert saved.download_mbps == 100.0
    assert saved.upload_mbps == 50.0
    assert saved.score == 95.5
    assert saved.ai_reasoning == "Test"
    assert saved.metrics_dict["download_mbps"] == 100.0

def test_get_best_experiments(storage):
    # Add a worst score
    storage.save_experiment(ExperimentResult(None, "t1", {}, 1, 1, 1, 1, 1, 1, 1, 10.0))
    # Add a better score
    storage.save_experiment(ExperimentResult(None, "t2", {}, 1, 1, 1, 1, 1, 1, 1, 90.0))
    # Add best score
    storage.save_experiment(ExperimentResult(None, "t3", {}, 1, 1, 1, 1, 1, 1, 1, 95.0))
    
    best = storage.get_best_experiments(limit=2)
    assert len(best) == 2
    assert best[0].score == 95.0
    assert best[1].score == 90.0

def test_get_baseline(storage):
    assert storage.get_baseline() is None
    storage.save_experiment(ExperimentResult(None, "t1", {}, 1, 1, 1, 1, 1, 1, 1, 10.0))
    storage.save_experiment(ExperimentResult(None, "t2", {}, 1, 1, 1, 1, 1, 1, 1, 90.0))
    # Baseline should be the first one added
    baseline = storage.get_baseline()
    assert baseline is not None
    assert baseline.timestamp == "t1"
    assert baseline.score == 10.0

def test_clear_storage(storage):
    storage.save_experiment(ExperimentResult(None, "t1", {}, 1, 1, 1, 1, 1, 1, 1, 10.0))
    assert storage.get_experiment_count() == 1
    storage.clear()
    assert storage.get_experiment_count() == 0

def test_calculate_score():
    metrics = {
        "latency_ms": 15,    # exp(-1) * 10 = ~3.68
        "download_mbps": 1,  # log2(2) * 10(max100) = 10
        "upload_mbps": 1,    # log2(2) * 12(max100) = 12
        "jitter_ms": 3,      # exp(-1) * 10 = ~3.68
        "packet_loss_pct": 0,# exp(0) * 10 = 10
        "dns_ms": 15,        # exp(-1) * 5 = ~1.84
        "tcp_handshake_ms": 20,# exp(-1) * 10 = ~3.68
        "tls_handshake_ms": 30,# exp(-1) * 15 = ~5.52
        "bufferbloat_ms": 10,# exp(-1) * 15 = ~5.52
        "stability_cv": 15   # exp(-1) * 5 = ~1.84
    }
    score = MetricsStorage.calculate_score(metrics)
    assert 0 <= score <= 100
    
    # Test perfect score basically
    perfect = MetricsStorage.calculate_score({
        "latency_ms": 0, "download_mbps": 1000, "upload_mbps": 1000,
        "jitter_ms": 0, "packet_loss_pct": 0, "dns_ms": 0,
        "tcp_handshake_ms": 0, "tls_handshake_ms": 0, "bufferbloat_ms": 0,
        "stability_cv": 0
    })
    # Since download_mbps uses log scale, it needs to be high to max out
    # 10 * log2(1001) ~ 10 * 9.96 = 99.6
    # 12 * log2(1001) is maxed to 100. But max possible throughput score is capped.
    assert perfect > 90

def test_db_migration(temp_db):
    # Create DB with old schema
    import sqlite3
    with sqlite3.connect(temp_db) as conn:
        conn.execute("""
            CREATE TABLE experiments (
                id INTEGER PRIMARY KEY,
                timestamp TEXT, config TEXT, latency_ms REAL, download_mbps REAL,
                jitter_ms REAL, packet_loss_pct REAL, dns_ms REAL, cpu_usage REAL,
                memory_mb REAL, score REAL, ai_reasoning TEXT
            )
        """)
        conn.commit()
    
    # Instance should run migration
    storage = MetricsStorage(db_path=temp_db)
    
    # Verify migration (should be able to insert full result)
    result = ExperimentResult(None, "t1", {}, 1, 1, 1, 1, 1, 1, 1, 10.0, upload_mbps=100)
    storage.save_experiment(result)
    
    res = storage.get_all_experiments()
    assert res[0].upload_mbps == 100
