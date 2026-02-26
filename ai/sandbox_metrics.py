"""
Entropy AI Sandbox - Metrics Storage v2
10 метрик, экспоненциальная/логарифмическая формула score
"""

import sqlite3
import json
import os
import math
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger("SandboxMetrics")


@dataclass
class ExperimentResult:
    """Полный результат одного эксперимента (10 метрик)"""
    id: Optional[int]
    timestamp: str
    config: Dict[str, Any]
    # Оригинальные метрики
    latency_ms: float
    download_mbps: float
    jitter_ms: float
    packet_loss_pct: float
    dns_ms: float
    cpu_usage: float
    memory_mb: float
    score: float
    # Новые метрики v2
    upload_mbps: float = 0.0
    tcp_handshake_ms: float = 0.0
    tls_handshake_ms: float = 0.0
    bufferbloat_ms: float = 0.0
    stability_cv: float = 0.0
    tcp_retrans: float = 0.0
    tc_backlog: float = 0.0
    isp_anomaly: float = 0.0
    xray_drops: float = 0.0
    ai_reasoning: str = ""
    
    @property
    def metrics_dict(self) -> Dict[str, float]:
        return {
            "latency_ms": self.latency_ms,
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "jitter_ms": self.jitter_ms,
            "packet_loss_pct": self.packet_loss_pct,
            "dns_ms": self.dns_ms,
            "tcp_handshake_ms": self.tcp_handshake_ms,
            "tls_handshake_ms": self.tls_handshake_ms,
            "bufferbloat_ms": self.bufferbloat_ms,
            "stability_cv": self.stability_cv,
            "tcp_retrans": self.tcp_retrans,
            "tc_backlog": self.tc_backlog,
            "isp_anomaly": self.isp_anomaly,
            "xray_drops": self.xray_drops,
        }


class MetricsStorage:
    """SQLite хранилище экспериментов (локально на клиенте)"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base, "sandbox_experiments.db")
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация схемы БД с миграцией для новых колонок"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    config TEXT NOT NULL,
                    latency_ms REAL,
                    download_mbps REAL,
                    jitter_ms REAL,
                    packet_loss_pct REAL,
                    dns_ms REAL,
                    cpu_usage REAL,
                    memory_mb REAL,
                    score REAL,
                    ai_reasoning TEXT,
                    upload_mbps REAL DEFAULT 0,
                    tcp_handshake_ms REAL DEFAULT 0,
                    tls_handshake_ms REAL DEFAULT 0,
                    bufferbloat_ms REAL DEFAULT 0,
                    stability_cv REAL DEFAULT 0,
                    tcp_retrans REAL DEFAULT 0,
                    tc_backlog REAL DEFAULT 0,
                    isp_anomaly REAL DEFAULT 0,
                    xray_drops REAL DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON experiments(score DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON experiments(timestamp DESC)")
            
            # Миграция: добавить новые колонки если таблица старая
            existing = {row[1] for row in conn.execute("PRAGMA table_info(experiments)").fetchall()}
            new_columns = {
                "upload_mbps": "REAL DEFAULT 0",
                "tcp_handshake_ms": "REAL DEFAULT 0",
                "tls_handshake_ms": "REAL DEFAULT 0",
                "bufferbloat_ms": "REAL DEFAULT 0",
                "stability_cv": "REAL DEFAULT 0",
                "tcp_retrans": "REAL DEFAULT 0",
                "tc_backlog": "REAL DEFAULT 0",
                "isp_anomaly": "REAL DEFAULT 0",
                "xray_drops": "REAL DEFAULT 0",
            }
            for col, col_type in new_columns.items():
                if col not in existing:
                    conn.execute(f"ALTER TABLE experiments ADD COLUMN {col} {col_type}")
                    logger.info(f"DB migration: added column {col}")
            
            conn.commit()
    
    def save_experiment(self, result: ExperimentResult) -> int:
        """Сохранить результат, вернуть ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO experiments 
                (timestamp, config, latency_ms, download_mbps, jitter_ms, 
                 packet_loss_pct, dns_ms, cpu_usage, memory_mb, score, ai_reasoning,
                 upload_mbps, tcp_handshake_ms, tls_handshake_ms, bufferbloat_ms, stability_cv,
                 tcp_retrans, tc_backlog, isp_anomaly, xray_drops)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp, json.dumps(result.config),
                result.latency_ms, result.download_mbps, result.jitter_ms,
                result.packet_loss_pct, result.dns_ms, result.cpu_usage,
                result.memory_mb, result.score, result.ai_reasoning,
                result.upload_mbps, result.tcp_handshake_ms, result.tls_handshake_ms,
                result.bufferbloat_ms, result.stability_cv,
                result.tcp_retrans, result.tc_backlog, result.isp_anomaly, result.xray_drops
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_best_experiments(self, limit: int = 10) -> List[ExperimentResult]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM experiments ORDER BY score DESC LIMIT ?", (limit,)
            )
            return [self._row_to_result(row) for row in cursor.fetchall()]
    
    def get_all_experiments(self) -> List[ExperimentResult]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM experiments ORDER BY id ASC")
            return [self._row_to_result(row) for row in cursor.fetchall()]
    
    def get_baseline(self) -> Optional[ExperimentResult]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM experiments ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            return self._row_to_result(row) if row else None
    
    def get_experiment_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM experiments")
            return cursor.fetchone()[0]
    
    def clear(self):
        """Очистить все эксперименты"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM experiments")
            conn.commit()
    
    def _row_to_result(self, row: sqlite3.Row) -> ExperimentResult:
        """Конвертация строки БД в ExperimentResult (с поддержкой старых записей)"""
        return ExperimentResult(
            id=row["id"], timestamp=row["timestamp"],
            config=json.loads(row["config"]),
            latency_ms=row["latency_ms"], download_mbps=row["download_mbps"],
            jitter_ms=row["jitter_ms"], packet_loss_pct=row["packet_loss_pct"],
            dns_ms=row["dns_ms"], cpu_usage=row["cpu_usage"],
            memory_mb=row["memory_mb"], score=row["score"],
            upload_mbps=row["upload_mbps"] or 0,
            tcp_handshake_ms=row["tcp_handshake_ms"] or 0,
            tls_handshake_ms=row["tls_handshake_ms"] or 0,
            bufferbloat_ms=row["bufferbloat_ms"] or 0,
            stability_cv=row["stability_cv"] or 0,
            tcp_retrans=row["tcp_retrans"] or 0,
            tc_backlog=row["tc_backlog"] or 0,
            isp_anomaly=row["isp_anomaly"] or 0,
            xray_drops=row["xray_drops"] or 0,
            ai_reasoning=row["ai_reasoning"] or ""
        )
    
    @staticmethod
    def calculate_score(metrics: Dict[str, float]) -> float:
        """
        Рассчитать score по 10 метрикам (0-100, выше = лучше).
        
        Экспоненциальное затухание для "меньше=лучше" метрик,
        логарифмическая шкала для throughput. Ужесточённые τ-значения
        для различения высокопроизводительных серверов.
        
        Веса:
        - Latency:       10%  (exp, τ=15ms)
        - Download:      10%  (log scale)
        - Upload:        10%  (log scale)
        - Jitter:        10%  (exp, τ=3ms)
        - Packet loss:   10%  (exp, τ=0.5%)
        - DNS:            5%  (exp, τ=15ms)
        - TCP Handshake: 10%  (exp, τ=20ms)
        - TLS Handshake: 15%  (exp, τ=30ms) — критично для VPN
        - Bufferbloat:   15%  (exp, τ=10ms) — главный QoS индикатор
        - Stability:      5%  (exp, τ=15%cv)
        """
        latency = metrics.get("latency_ms", 100)
        download = metrics.get("download_mbps", 0)
        upload = metrics.get("upload_mbps", 0)
        jitter = metrics.get("jitter_ms", 50)
        loss = metrics.get("packet_loss_pct", 0)
        dns = metrics.get("dns_ms", 100)
        tcp_hs = metrics.get("tcp_handshake_ms", 100)
        tls_hs = metrics.get("tls_handshake_ms", 200)
        bloat = metrics.get("bufferbloat_ms", 50)
        stability = metrics.get("stability_cv", 50)
        
        # Экспоненциальное затухание с ужесточёнными τ
        latency_score = 100 * math.exp(-latency / 15)
        jitter_score = 100 * math.exp(-jitter / 3)
        loss_score = 100 * math.exp(-loss * 2)
        dns_score = 100 * math.exp(-dns / 15)
        tcp_score = 100 * math.exp(-tcp_hs / 20)
        tls_score = 100 * math.exp(-tls_hs / 30)
        bloat_score = 100 * math.exp(-bloat / 10)
        stability_score = 100 * math.exp(-stability / 15)
        
        # Логарифмическая шкала для throughput: 10 * log2(1 + mbps)
        download_score = min(100, 10 * math.log2(1 + download)) if download > 0 else 0
        upload_score = min(100, 12 * math.log2(1 + upload)) if upload > 0 else 0
        
        score = (
            latency_score * 0.10 +
            download_score * 0.10 +
            upload_score * 0.10 +
            jitter_score * 0.10 +
            loss_score * 0.10 +
            dns_score * 0.05 +
            tcp_score * 0.10 +
            tls_score * 0.15 +
            bloat_score * 0.15 +
            stability_score * 0.05
        )
        return round(score, 2)
