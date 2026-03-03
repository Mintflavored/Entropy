import logging
import math

logger = logging.getLogger(__name__)

class SecurityEngine:
    """Утилиты парсинга сетевых метрик. Risk scoring перенесён в EDP Pipeline."""
    
    @staticmethod
    def calculate_pps(current_raw, last_raw, interval_ms):
        """Вычисляет пакеты в секунду на основе дельты счетчиков."""
        try:
            if last_raw is None or current_raw is None:
                return 0
            
            delta = int(current_raw) - int(last_raw)
            if delta < 0: return 0 # Reset interface
            
            pps = delta / (interval_ms / 1000.0)
            return round(pps, 2)
        except Exception as e:
            logger.warning(f"PPS calculation error: {e}")
            return 0

    @staticmethod
    def calculate_jitter(latencies):
        """Вычисляет джиттер как стандартное отклонение задержек."""
        try:
            if not latencies or len(latencies) < 2:
                return 0.0
            
            mean = sum(latencies) / len(latencies)
            variance = sum((l - mean) ** 2 for l in latencies) / len(latencies)
            return round(math.sqrt(variance), 2)
        except Exception as e:
            logger.warning(f"Jitter calculation error: {e}")
            return 0.0

    @staticmethod
    def parse_probes(ssh_probes):
        """Превращает сырые IP из лога в список для таблицы UI."""
        if not ssh_probes:
            return []
            
        results = []
        from collections import Counter
        counts = Counter(ssh_probes)
        
        for ip, count in counts.items():
            results.append({
                "ip": ip,
                "attempts": count,
                "seen": "Recent (auth.log)"
            })
        return results
