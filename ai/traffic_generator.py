"""
Entropy AI Sandbox - Remote Traffic Generator v3
10 метрик производительности VPN через SSH на удалённом VPS
Оптимизированная версия: Параллелизм, Адаптивные таймеры, Aria2c
"""

import re
import time
import logging
import math
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("TrafficGenerator")


def trimmed_mean(values: List[float], trim_pct: float = 0.2) -> float:
    """Усечённое среднее (отбрасывает выбросы)"""
    if not values:
        return 0.0
    values = sorted(values)
    n = len(values)
    k = int(n * trim_pct)
    if k > 0 and n > 2 * k:
        values = values[k:-k]
    return sum(values) / len(values)


@dataclass
class TrafficTestResult:
    """Результат одного теста"""
    test_name: str
    success: bool
    value: float
    unit: str
    duration_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test": self.test_name,
            "success": self.success,
            "value": self.value,
            "unit": self.unit,
            "duration_ms": self.duration_ms,
            "error": self.error
        }


class RemoteTrafficGenerator:
    """
    Запускает 10 тестов через SSH на удалённом VPS.
    Оптимизировано пулами потоков (Pool A, Pool B, Pool C).
    """
    
    def __init__(self, ssh_manager):
        self.ssh = ssh_manager
        self.sandbox_exec = "/tmp/entropy-sandbox/run_in_sandbox.sh"
    
    def _ssh_exec(self, cmd: str, timeout: int = 30) -> tuple:
        return self.ssh.exec_command(cmd, timeout=timeout)
    
    def _sandbox_exec(self, cmd: str, timeout: int = 30) -> tuple:
        full_cmd = f"bash {self.sandbox_exec} {cmd}"
        return self._ssh_exec(full_cmd, timeout=timeout)
    
    # ── Group A (Прямой SSH: Connection Timing, DNS) ───────────────
    
    def test_connection_timing(self) -> Dict[str, TrafficTestResult]:
        start = time.time()
        urls = ["https://www.google.com", "https://www.cloudflare.com", "https://www.microsoft.com"]
        
        lats, tcps, tlss = [], [], []
        
        for url in urls:
            ok, output = self._ssh_exec(
                f"curl -o /dev/null -s --no-keepalive -w '%{{time_connect}}|%{{time_appconnect}}|%{{time_total}}' --connect-timeout 5 {url}",
                timeout=20
            )
            if ok:
                try:
                    parts = output.strip().replace("'", "").split("|")
                    if len(parts) == 3:
                        tcp_s, tls_s, total_s = float(parts[0]), float(parts[1]), float(parts[2])
                        lats.append(total_s * 1000)
                        if tcp_s > 0:
                            tcps.append(tcp_s * 1000)
                        if tls_s > 0:
                            tlss.append(tls_s * 1000)
                except (ValueError, IndexError):
                    pass
        
        duration = (time.time() - start) * 1000
        
        results = {}
        # Используем обычное среднее для массива из 3-х (trimmed mean нет смысла делать для <=3)
        results["latency"] = (
            TrafficTestResult("latency", True, round(sum(lats)/len(lats), 2), "ms", duration)
            if lats else TrafficTestResult("latency", False, 0.0, "ms", duration, "Latency failed")
        )
        results["tcp_handshake"] = (
            TrafficTestResult("tcp_handshake", True, round(sum(tcps)/len(tcps), 2), "ms", 0)
            if tcps else TrafficTestResult("tcp_handshake", False, 0.0, "ms", 0, "TCP handshake failed")
        )
        results["tls_handshake"] = (
            TrafficTestResult("tls_handshake", True, round(sum(tlss)/len(tlss), 2), "ms", 0)
            if tlss else TrafficTestResult("tls_handshake", False, 0.0, "ms", 0, "TLS handshake failed")
        )
        return results
    
    def test_dns(self) -> TrafficTestResult:
        domains = ["google.com", "cloudflare.com", "github.com", "microsoft.com", "apple.com"]
        times = []
        
        for domain in domains:
            ok, output = self._ssh_exec(f"dig +noall +stats @8.8.8.8 {domain}", timeout=10)
            if ok:
                match = re.search(r'Query time: (\d+) msec', output)
                if match:
                    times.append(float(match.group(1)))
        
        if times:
            # Для 5 значений trimmed mean отбросит min и max
            avg_time = trimmed_mean(times, trim_pct=0.2)
            return TrafficTestResult("dns", True, round(avg_time, 2), "ms", 0)
        return TrafficTestResult("dns", False, 0.0, "ms", 0, "DNS tests failed")
    
    # ── Group B (Легкая сеть Sandbox: Jitter, Packet Loss) ───────────────
    
    def test_jitter(self) -> TrafficTestResult:
        """Агрессивный пинг (10 пакетов с интервалом 0.1)"""
        ok, output = self._sandbox_exec("ping -c 10 -i 0.1 8.8.8.8", timeout=5)
        
        if not ok:
            return TrafficTestResult("jitter", False, 0.0, "ms", 0, "Ping failed")
        
        times = re.findall(r'time=(\d+\.?\d*)', output)
        if len(times) < 2:
            return TrafficTestResult("jitter", False, 0.0, "ms", 0, "Not enough responses")
        
        rtts = [float(t) for t in times]
        avg_rtt = sum(rtts) / len(rtts)
        jitter = sum(abs(rtt - avg_rtt) for rtt in rtts) / len(rtts)
        
        return TrafficTestResult("jitter", True, round(jitter, 2), "ms", 0)
    
    def test_packet_loss(self) -> TrafficTestResult:
        """Быстрый тест потерь (30 пакетов с интервалом 0.1)"""
        ok, output = self._sandbox_exec("ping -c 30 -i 0.1 -q 8.8.8.8", timeout=10)
        
        match = re.search(r'(\d+)% packet loss', output)
        if match:
            return TrafficTestResult("packet_loss", True, float(match.group(1)), "%", 0)
        
        return TrafficTestResult("packet_loss", False, 0.0, "%", 0, "Could not parse")
    
    # ── Group C (Тяжелая сеть Sandbox: Download, Upload, Bufferbloat) ────────
    
    def test_download_and_stability(self, fast_mode: bool = False) -> Dict[str, TrafficTestResult]:
        """
        Комбайн: Скачивает 10MB (или 3MB в fast_mode) в 16 потоков через aria2c,
        парсит прогресс для вычисления скорости и Stability (CV).
        """
        start = time.time()
        file_size = "3MB" if fast_mode else "10MB"
        # aria2c позволяет выжать весь канал за милисекунды (16 conn)
        ok, output = self._sandbox_exec(
            f"aria2c -x 16 -s 16 -d /tmp -o test_dl.zip --summary-interval=1 http://speedtest.tele2.net/{file_size}.zip 2>&1; rm -f /tmp/test_dl.zip",
            timeout=20 if fast_mode else 30
        )
        duration = (time.time() - start) * 1000
        res = {"download": None, "stability": None}
        
        DL_speeds_mbps = []
        if ok:
            # Парсим все 'DL:X.XMiB' из логов aria2c
            matches = re.finditer(r'DL:(\d+\.?\d*)(MiB|KiB|B)', output)
            for m in matches:
                val = float(m.group(1))
                unit = m.group(2)
                if unit == "MiB":
                    DL_speeds_mbps.append(val * 8)
                elif unit == "KiB":
                    DL_speeds_mbps.append(val * 8 / 1024)
                else:
                    DL_speeds_mbps.append(val * 8 / 1024 / 1024)
        
        if DL_speeds_mbps:
            # Усечённое среднее (Trimmed Mean) пиков скорости Download
            avg_speed = trimmed_mean(DL_speeds_mbps, trim_pct=0.1)
            if avg_speed == 0 and sum(DL_speeds_mbps) > 0:
                avg_speed = sum(DL_speeds_mbps) / len(DL_speeds_mbps)
                
            res["download"] = TrafficTestResult("download", True, round(avg_speed, 2), "Mbps", duration)
            
            # Stability = CV = StdDev / Mean * 100
            if len(DL_speeds_mbps) >= 2 and avg_speed > 0:
                variance = sum((s - avg_speed) ** 2 for s in DL_speeds_mbps) / len(DL_speeds_mbps)
                cv = (math.sqrt(variance) / avg_speed) * 100
                res["stability"] = TrafficTestResult("stability", True, round(cv, 2), "%cv", 0)
            else:
                res["stability"] = TrafficTestResult("stability", True, 0.0, "%cv", 0)
        else:
            # Фоллбэк на wget (однопоток 10MB/3MB) если aria2c нет в системе
            ok_w, out_w = self._sandbox_exec(
                f"wget -O /dev/null http://speedtest.tele2.net/{file_size}.zip 2>&1 | tail -1",
                timeout=20 if fast_mode else 30
            )
            duration_w = (time.time() - start) * 1000
            if ok_w and duration_w > 0:
                match = re.search(r'\((\d+\.?\d*)\s*(MB/s|KB/s)\)', out_w)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    speed_mbps = val * 8 if unit == "MB/s" else val * 8 / 1024
                    res["download"] = TrafficTestResult("download", True, round(speed_mbps, 2), "Mbps", duration_w)
                    res["stability"] = TrafficTestResult("stability", False, 0.0, "%cv", 0, "Fallback used")
                else:
                    # Ручной рассчёт скорости
                    size_mb = 3.0 if fast_mode else 10.0
                    speed_mbps = (size_mb * 8) / (duration_w / 1000)
                    res["download"] = TrafficTestResult("download", True, round(speed_mbps, 2), "Mbps", duration_w)
                    res["stability"] = TrafficTestResult("stability", False, 0.0, "%cv", 0, "Fallback used")
            else:
                res["download"] = TrafficTestResult("download", False, 0.0, "Mbps", duration, "Download failed")
                res["stability"] = TrafficTestResult("stability", False, 0.0, "%cv", 0)
        
        return res
    
    def test_upload_speed(self, fast_mode: bool = False) -> TrafficTestResult:
        """Снижен объем до 1MB в fast_mode, 2MB стандартно"""
        start = time.time()
        mb_count = 1 if fast_mode else 2
        ok, output = self._sandbox_exec(
            f"dd if=/dev/urandom bs=1M count={mb_count} 2>/dev/null | "
            "curl -s -w '%{speed_upload}' -X POST -d @- "
            "http://httpbin.org/post -o /dev/null",
            timeout=20 if fast_mode else 30
        )
        duration = (time.time() - start) * 1000
        
        if ok:
            try:
                speed_bytes = float(output.strip().replace("'", ""))
                speed_mbps = (speed_bytes * 8) / 1_000_000
                if speed_mbps > 0:
                    return TrafficTestResult("upload", True, round(speed_mbps, 2), "Mbps", duration)
            except ValueError:
                pass
        
        if duration > 100:
            speed_mbps = (float(mb_count) * 8) / (duration / 1000)
            return TrafficTestResult("upload", True, round(speed_mbps, 2), "Mbps", duration)
        
        return TrafficTestResult("upload", False, 0.0, "Mbps", duration, "Upload test failed")
    
    def test_load_telemetry(self) -> Dict[str, TrafficTestResult]:
        """Тест Bufferbloat + TCP Retransmissions + tc backlog под нагрузкой"""
        ok_idle, idle_output = self._sandbox_exec("ping -c 5 -i 0.1 8.8.8.8", timeout=5)
        idle_rtts = [float(t) for t in re.findall(r'time=(\d+\.?\d*)', idle_output)] if ok_idle else []
        idle_avg = sum(idle_rtts) / len(idle_rtts) if idle_rtts else 0
        
        start = time.time()
        ok_loaded, loaded_output = self._sandbox_exec(
            "wget -O /dev/null http://speedtest.tele2.net/10MB.zip >/dev/null 2>&1 & "
            "sleep 1; ping -c 10 -i 0.2 8.8.8.8; "
            "ss -i -n -t state established; "
            "tc -s qdisc show dev veth-sandbox; "
            "kill %1 2>/dev/null",
            timeout=25
        )
        duration = (time.time() - start) * 1000
        
        # Parse Bufferbloat
        loaded_rtts = [float(t) for t in re.findall(r'time=(\d+\.?\d*)', loaded_output)] if ok_loaded else []
        loaded_avg = sum(loaded_rtts) / len(loaded_rtts) if loaded_rtts else 0
        bloat_ms = max(0.0, loaded_avg - idle_avg) if (idle_avg > 0 and loaded_avg > 0) else 0.0
        
        # Parse TCP Retransmissions
        # Format ss: `retrans:0/1` or `retrans:1`
        retrans_total = 0
        retrans_matches = re.finditer(r'retrans:\d*/?(\d+)', loaded_output)
        for m in retrans_matches:
            retrans_total += int(m.group(1))
            
        # Parse tc backlog (packets or bytes)
        # Format tc: `backlog 1000b 2p` => 2 packets
        backlog_p = 0
        backlog_match = re.search(r'backlog\s+\d+[bB]\s+(\d+)[pP]', loaded_output)
        if backlog_match:
            backlog_p = int(backlog_match.group(1))
            
        return {
            "bufferbloat": TrafficTestResult(
                "bufferbloat", (idle_avg > 0 and loaded_avg > 0), round(bloat_ms, 2), "ms", duration
            ),
            "tcp_retrans": TrafficTestResult(
                "tcp_retrans", ok_loaded, float(retrans_total), "packets", 0
            ),
            "tc_backlog": TrafficTestResult(
                "tc_backlog", ok_loaded, float(backlog_p), "packets", 0
            )
        }
    
    def test_mtr(self) -> TrafficTestResult:
        """Geo-routing and ISP anomaly check"""
        ok, output = self._ssh_exec("mtr -c 1 -n -r 8.8.8.8", timeout=15)
        isp_anomaly = 0.0
        if ok:
            # Парсим задержки на первых 3х хопах. 
            lines = output.strip().split('\n')
            for line in lines[1:4]: # Пропускаем header
                match = re.search(r'\d+\.\|--\s+\S+\s+[\d\.]+%[ \t]+\d+[ \t]+([\d\.]+)', line)
                if match:
                    try:
                        ping_ms = float(match.group(1))
                        if ping_ms > 150.0: # Если на первых хопах провайдера огромный пинг
                            isp_anomaly = 1.0
                    except ValueError:
                        pass
            return TrafficTestResult("isp_anomaly", True, isp_anomaly, "bool", 0)
        return TrafficTestResult("isp_anomaly", False, 0.0, "bool", 0)
    
    def test_xray_stats(self) -> TrafficTestResult:
        """Сбор Xray Telemetry (Drop Rate и Errors)"""
        ok, output = self._sandbox_exec(
            "/opt/entropy-sandbox/x-ui/bin/xray api statsquery -server=127.0.0.1:10085",
            timeout=10
        )
        drops = 0.0
        if ok and '"stat"' in output:
            try:
                import json
                data = json.loads(output)
                stats = data.get("stat", [])
                for s in stats:
                    if s.get("name", "").endswith("drop") or s.get("name", "").endswith("error"):
                        drops += float(s.get("value", 0))
                return TrafficTestResult("xray_drops", True, drops, "count", 0)
            except Exception:
                pass
        return TrafficTestResult("xray_drops", False, 0.0, "count", 0)
    
    # ── Orchestrator (Параллельный запуск) ────────────────────────────────
    
    def run_full_test(self, cached_metrics: Optional[Dict[str, TrafficTestResult]] = None, fast_mode: bool = False) -> Dict[str, TrafficTestResult]:
        """Запуск тестов с разделением на независимые параллельные пулы и поддержкой Fast-Fail"""
        mode_str = "FAST " if fast_mode else "Full "
        logger.info(f"Starting optimized {mode_str}remote traffic tests (v3) on VPS...")
        
        results: Dict[str, TrafficTestResult] = {}
        
        # Инжектируем закэшированные метрики (обычно Timing и DNS)
        if cached_metrics:
            for key in ["latency", "tcp_handshake", "tls_handshake", "dns"]:
                if key in cached_metrics:
                    results[key] = cached_metrics[key]
        
        # Fast-Fail Check: перед тяжелыми загрузками проверяем жив ли вообще коннект
        ok_ff, out_ff = self._sandbox_exec("ping -c 1 -W 1 8.8.8.8", timeout=2)
        if not ok_ff or "100% packet loss" in out_ff:
            logger.warning("Fast-Fail triggered: Sandbox has no internet or high packet loss. Aborting heavy tests.")
            # Возвращаем "пустые" значения, чтобы AI понял, что конфиг нерабочий
            return {
                "latency": TrafficTestResult("latency", False, 0, "ms", 0, "Fast-Fail"),
                "download": TrafficTestResult("download", False, 0, "Mbps", 0, "Fast-Fail"),
                "upload": TrafficTestResult("upload", False, 0, "Mbps", 0, "Fast-Fail"),
            }
            
        def run_group_a() -> Dict[str, TrafficTestResult]:
            # Прямой SSH, не грузит канал
            res = {}
            if "latency" not in results:
                res.update(self.test_connection_timing())
            if "dns" not in results:
                res["dns"] = self.test_dns()
            return res
        
        def run_group_b() -> Dict[str, TrafficTestResult]:
            # Sandbox: Ping'и + Geo-routing
            return {
                "jitter": self.test_jitter(),
                "packet_loss": self.test_packet_loss(),
                "isp_anomaly": self.test_mtr()
            }
        
        def run_group_c() -> Dict[str, TrafficTestResult]:
            # Sandbox: Ширина канала + Telemetry
            res = {}
            res.update(self.test_download_and_stability(fast_mode=fast_mode))
            res["upload"] = self.test_upload_speed(fast_mode=fast_mode)
            res.update(self.test_load_telemetry())
            res["xray_drops"] = self.test_xray_stats()
            return res
        
        # Запускаем группы параллельно
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_a = executor.submit(run_group_a)
            future_b = executor.submit(run_group_b)
            future_c = executor.submit(run_group_c)
            
            for future in as_completed([future_a, future_b, future_c]):
                try:
                    results.update(future.result())
                except Exception as e:
                    logger.error(f"Error in test group: {e}")
        
        return {
            "latency": results.get("latency", TrafficTestResult("latency", False, 0, "ms", 0)),
            "tcp_handshake": results.get("tcp_handshake", TrafficTestResult("tcp", False, 0, "ms", 0)),
            "tls_handshake": results.get("tls_handshake", TrafficTestResult("tls", False, 0, "ms", 0)),
            "dns": results.get("dns", TrafficTestResult("dns", False, 0, "ms", 0)),
            "jitter": results.get("jitter", TrafficTestResult("jitter", False, 0, "ms", 0)),
            "packet_loss": results.get("packet_loss", TrafficTestResult("packet_loss", False, 0, "%", 0)),
            "download": results.get("download", TrafficTestResult("download", False, 0, "Mbps", 0)),
            "upload": results.get("upload", TrafficTestResult("upload", False, 0, "Mbps", 0)),
            "bufferbloat": results.get("bufferbloat", TrafficTestResult("bufferbloat", False, 0, "ms", 0)),
            "stability": results.get("stability", TrafficTestResult("stability", False, 0, "%cv", 0)),
            "tcp_retrans": results.get("tcp_retrans", TrafficTestResult("tcp_retrans", False, 0, "packets", 0)),
            "tc_backlog": results.get("tc_backlog", TrafficTestResult("tc_backlog", False, 0, "packets", 0)),
            "isp_anomaly": results.get("isp_anomaly", TrafficTestResult("isp_anomaly", False, 0, "bool", 0)),
            "xray_drops": results.get("xray_drops", TrafficTestResult("xray_drops", False, 0, "count", 0)),
        }
    
    @staticmethod
    def get_summary(results: Dict[str, TrafficTestResult]) -> Dict[str, float]:
        """Сводка результатов для AI и score"""
        def val(key):
            r = results.get(key)
            return float(r.value) if r and r.success else 0.0
        
        return {
            "latency_ms": val("latency"),
            "download_mbps": val("download"),
            "upload_mbps": val("upload"),
            "jitter_ms": val("jitter"),
            "packet_loss_pct": val("packet_loss"),
            "dns_ms": val("dns"),
            "tcp_handshake_ms": val("tcp_handshake"),
            "tls_handshake_ms": val("tls_handshake"),
            "bufferbloat_ms": val("bufferbloat"),
            "stability_cv": val("stability"),
            "tcp_retrans": val("tcp_retrans"),
            "tc_backlog": val("tc_backlog"),
            "isp_anomaly": val("isp_anomaly"),
            "xray_drops": val("xray_drops"),
        }
