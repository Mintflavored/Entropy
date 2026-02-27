import logging
import math
import time

logger = logging.getLogger(__name__)

class SecurityEngine:
    """Логика анализа реальных сетевых метрик и безопасности."""
    
    @staticmethod
    @staticmethod
    def calculate_risk(pps, jitter, brute_force_count=0):
        """
        Оценивает риск на основе плавной взвешенной модели (Entropy Index).
        Возвращает (Label, Color, NumericScore)
        """
        try:
            # 1. PPS Score (0-100) - Насыщение около 1000 PPS
            # Используем atan для плавного роста: arctan(1) = 45 deg = 0.5 * pi
            p_score = math.atan(pps / 400) * (2 / math.pi) * 100
            
            # 2. Jitter Score (0-100) - Насыщение около 50ms
            j_score = math.atan(jitter / 30) * (2 / math.pi) * 100
            
            # 3. Security Score (0-100)
            b_score = min(100, brute_force_count * 10)
            
            # Взвешенная сумма: Jitter (40%), PPS (30%), Security (30%)
            total_risk = (j_score * 0.4) + (p_score * 0.3) + (b_score * 0.3)
            
            # Корреляционный множитель: если Jitter высокий, а PPS падает - это DPI
            # (не реализовано в этой версии, но заложено в архитектуру)
            
            score = round(total_risk, 1)
            
            if score >= 70:
                return "CRITICAL", "#ff4444", score
            elif score >= 40:
                return "HIGH", "#ff7744", score
            elif score >= 15:
                return "MEDIUM", "#ffaa00", score
            else:
                return "LOW", "#00ff00", score
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            return "UNKNOWN", "#888888", 0

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
        # Считаем количество попыток для каждого IP в текущем срезе
        from collections import Counter
        counts = Counter(ssh_probes)
        
        for ip, count in counts.items():
            results.append({
                "ip": ip,
                "attempts": count,
                "seen": "Recent (auth.log)"
            })
        return results
