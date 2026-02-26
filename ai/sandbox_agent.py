"""
Entropy AI Sandbox (EAIS) - AI-Driven Experiment Agent v2
AI с полным контекстом сервера, SSH tool calling и расширенными параметрами
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import math

from ai.traffic_generator import RemoteTrafficGenerator, trimmed_mean
from ai.sandbox_metrics import MetricsStorage, ExperimentResult

logger = logging.getLogger("EAIS")

# Путь к локальным скриптам для загрузки на VPS
SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "server", "sandbox"
)

REMOTE_SANDBOX_DIR = "/tmp/entropy-sandbox"

# Расширенный системный промпт v2
EAIS_SYSTEM_PROMPT = """Ты — EAIS (Entropy AI Sandbox), продвинутый AI-инженер для оптимизации VPN-инфраструктуры.
Ты работаешь на реальном VPS через sandbox — изолированное окружение для безопасных экспериментов.

# ТВОЯ РОЛЬ
Ты проводишь эксперименты на VPS: меняешь сетевые параметры, тестируешь и находишь оптимальную конфигурацию VPN.
У тебя есть ПОЛНЫЙ контекст сервера и два инструмента: конфигурация параметров и SSH-диагностика.

# ДОСТУПНЫЕ ПАРАМЕТРЫ (tool: apply_config)
Ты можешь менять следующие параметры через конфигурацию эксперимента:

## Сетевые параметры
- **mtu**: MTU размер пакета (1500, 1420, 1360, 1280). Влияет на фрагментацию и пропускную способность.
- **congestion**: Алгоритм контроля перегрузки TCP (bbr, cubic). BBR лучше для высоколатентных каналов, Cubic — для стабильных.
- **buffer_size**: Размер сетевого буфера в KB (64, 128, 256, 512, 1024). Больше буфер = больше throughput, но больше latency и bufferbloat.

## Параметры VPN/REALITY
- **dest**: REALITY destination — домен для маскировки (google.com:443, microsoft.com:443, etc). Влияет на проходимость через DPI.
- **short_id**: REALITY short ID — идентификатор для REALITY протокола.

# ИНСТРУМЕНТЫ

## 1. apply_config — применить конфигурацию
Передай JSON с параметрами: {"mtu": 1400, "congestion": "bbr"}
После применения автоматически запустятся 10 тестов производительности.

## 2. execute_ssh_command — диагностика через SSH
Можешь выполнить ЛЮБУЮ диагностическую команду на сервере для анализа:
- Проверить текущие настройки: sysctl, ip link, ss, netstat
- Посмотреть конфиги Xray/V2Ray: cat /usr/local/x-ui/bin/config.json
- Проверить логи: journalctl, /var/log/
- Мониторинг: top, iotop, nethogs, iftop
- Сетевая диагностика: traceroute, mtr, iperf3

ОГРАНИЧЕНИЕ: Максимум 5 SSH-команд за сессию.

# ФОРМАТ ОТВЕТА (строго JSON)
{
    "reasoning": "Подробное обоснование выбора...",
    "action": "apply_config" | "ssh_command" | "finish",
    "config": {"mtu": 1400, "congestion": "bbr"},
    "ssh_command": "sysctl net.ipv4.tcp_congestion_control",
    "should_continue": true,
    "summary": "Краткий статус оптимизации"
}

# СТРАТЕГИЯ ОПТИМИЗАЦИИ
1. Начни с АНАЛИЗА — изучи baseline и контекст сервера
2. Если нужна доп. информация — используй SSH для диагностики
3. Меняй 1-2 параметра за раз для чистоты эксперимента
4. Анализируй ТРЕНД результатов — особенно bufferbloat и TLS handshake
5. **ОБЯЗАТЕЛЬНО проведи минимум 5 экспериментов** (apply_config)!
   - Протестируй ВСЕ алгоритмы congestion (bbr, cubic)
   - Протестируй разные MTU (1500, 1420, 1360, 1280)
   - Протестируй buffer_size с лучшим congestion
6. Останавливайся (action: "finish") ТОЛЬКО после 5+ экспериментов
7. В финальном summary укажи лучшую конфигурацию и сравнение

# 10 МЕТРИК ТЕСТОВ
## Базовые
- **Latency** (ms): HTTP время ответа. Ниже = лучше.
- **Download** (Mbps): Скорость загрузки 10MB. Выше = лучше.
- **Upload** (Mbps): Скорость отдачи 5MB. Выше = лучше.
- **Jitter** (ms): Разброс RTT. Ниже = лучше.
- **Packet Loss** (%): Потеря пакетов. 0% = идеально.
- **DNS** (ms): DNS-резолвинг. Ниже = лучше.

## Продвинутые (наиболее информативные для VPN)
- **TCP Handshake** (ms): Время установки TCP-соединения. Чувствителен к congestion и MTU.
- **TLS Handshake** (ms): Время TLS/SSL handshake. Критично для REALITY-протокола. Зависит от congestion, MTU, dest.
- **Bufferbloat** (ms): Рост latency ПОД НАГРУЗКОЙ. Главный индикатор качества QoS.
- **Stability** (%CV): Коэффициент вариации скорости (3 замера). Ниже = стабильнее.

## Новая Телеметрия (Глубокий анализ)
- **TCP Retrans** (packets): Количество повторно отправленных TCP-пакетов под нагрузкой. Показывает нестабильность канала. 0 = идеально.
- **TC Backlog** (packets): Размер очереди на сетевом интерфейсе под нагрузкой. Высокое значение = плохой buffer_size/MTU.
- **Xray Drops** (count): Внутренние ошибки/дропы ядра Xray. Выше 0 = плохой конфиг (например, неверный REALITY dest).
- **ISP Anomaly** (bool 1/0): Если 1.0, это значит, что пинг до провайдера внезапно подскочил (внешняя проблема).

⚠️ ОБРАТИ ВНИМАНИЕ: Используй новые метрики телеметрии для понимания узких мест. Если высокая скорость, но огромный TCP Retrans / TC Backlog, значит конфиг "грязный" (Cubic + большой буфер).
"""


class EAISAgent:
    """
    AI-управляемый агент оптимизации VPN v2.
    
    Возможности:
    - Полный контекст сервера (ОС, ядро, VPN, панель, текущая конфигурация)
    - SSH tool calling (AI сам может диагностировать)
    - Расширенные параметры (mtu, congestion, buffer, dest, short_id)
    - Умная стратегия оптимизации через LLM
    """
    
    def __init__(self, ssh_manager, config_manager):
        self.ssh = ssh_manager
        self.cfg = config_manager
        self.traffic_gen = RemoteTrafficGenerator(ssh_manager)
        self.metrics = MetricsStorage()
        self._cached_metrics = {}
        
        self._is_running = False
        self._current_experiment = 0
        self._total_experiments = 0
        self._best_result: Optional[ExperimentResult] = None
        self._status_callback: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None
        self._ssh_calls_used = 0
        self._max_ssh_calls = 5
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def progress(self) -> tuple:
        return (self._current_experiment, self._total_experiments)
    
    @property
    def best_result(self) -> Optional[ExperimentResult]:
        return self._best_result
    
    def set_callbacks(self, status_cb=None, progress_cb=None):
        self._status_callback = status_cb
        self._progress_callback = progress_cb
    
    def _update_status(self, text: str):
        logger.info(f"EAIS: {text}")
        if self._status_callback:
            self._status_callback(text)
    
    def _update_progress(self, current: int, total: int):
        self._current_experiment = current
        self._total_experiments = total
        if self._progress_callback:
            self._progress_callback(current, total)
    
    # --- Сбор контекста сервера ---
    
    def collect_server_context(self) -> Dict[str, Any]:
        """Собрать полный контекст VPS и VPN конфигурации"""
        self._update_status("Сбор информации о сервере...")
        
        context = {}
        
        # ОС и железо
        commands = {
            "os": "cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f 2",
            "kernel": "uname -r",
            "cpu_model": "lscpu | grep 'Model name' | cut -d ':' -f 2",
            "cpu_cores": "nproc",
            "ram_total": "free -h | grep Mem | awk '{print $2}'",
            "ram_used": "free -h | grep Mem | awk '{print $3}'",
            "disk_usage": "df -h / | tail -1 | awk '{print $5}'",
            "uptime": "uptime -p",
        }
        
        for key, cmd in commands.items():
            ok, output = self.ssh.exec_command(cmd, timeout=5)
            if ok and output.strip():
                context[key] = output.strip()
        
        # Сетевые настройки
        context["server_ip"] = self.cfg.get("ip", "unknown")
        net_commands = {
            "tcp_congestion": "sysctl -n net.ipv4.tcp_congestion_control",
            "tcp_rmem": "sysctl -n net.ipv4.tcp_rmem",
            "tcp_wmem": "sysctl -n net.ipv4.tcp_wmem",
            "mtu": "ip link show | grep -oP 'mtu \\K[0-9]+' | head -1",
            "ip_forward": "sysctl -n net.ipv4.ip_forward",
        }
        
        for key, cmd in net_commands.items():
            ok, output = self.ssh.exec_command(cmd, timeout=5)
            if ok and output.strip():
                context[key] = output.strip()
        
        # VPN панель и протокол
        ok, ps_output = self.ssh.exec_command("ps aux", timeout=5)
        if ok:
            ps_lower = ps_output.lower()
            panels = []
            if 'marzban' in ps_lower: panels.append("Marzban")
            if 'x-ui' in ps_lower or '3x-ui' in ps_lower: panels.append("3X-UI")
            if 'xray' in ps_lower: panels.append("Xray")
            if 'sing-box' in ps_lower: panels.append("Sing-box")
            context["vpn_panels"] = panels
        
        # Xray конфигурация (если есть)
        xray_configs = [
            "/usr/local/x-ui/bin/config.json",
            "/usr/local/etc/xray/config.json",
            "/etc/xray/config.json",
        ]
        for cfg_path in xray_configs:
            ok, output = self.ssh.exec_command(f"cat {cfg_path} 2>/dev/null | head -100", timeout=5)
            if ok and output.strip().startswith("{"):
                try:
                    xray_cfg = json.loads(output)
                    # Извлекаем ключевое: протокол, порт, настройки
                    inbounds = xray_cfg.get("inbounds", [])
                    if inbounds:
                        inbound = inbounds[0]
                        context["vpn_protocol"] = inbound.get("protocol", "unknown")
                        context["vpn_port"] = inbound.get("port", "unknown")
                        stream = inbound.get("streamSettings", {})
                        context["vpn_network"] = stream.get("network", "unknown")
                        context["vpn_security"] = stream.get("security", "unknown")
                        reality = stream.get("realitySettings", {})
                        if reality:
                            context["reality_dest"] = reality.get("dest", "unknown")
                            context["reality_server_names"] = reality.get("serverNames", [])
                except json.JSONDecodeError:
                    context["xray_config_raw"] = output[:500]
                break
        
        # Текущая нагрузка
        ok, load = self.ssh.exec_command("cat /proc/loadavg", timeout=5)
        if ok:
            context["load_avg"] = load.strip()
        
        # Кол-во активных соединений
        ok, conns = self.ssh.exec_command("ss -s | head -5", timeout=5)
        if ok:
            context["connections_summary"] = conns.strip()
        
        logger.info(f"Server context collected: {len(context)} fields")
        return context
    
    # --- Deploy и Setup ---
    
    def deploy_scripts(self) -> bool:
        """Загрузить скрипты sandbox на VPS через SFTP (батч)"""
        self._update_status("Загрузка скриптов на VPS...")
        
        ok, _ = self.ssh.exec_command(f"mkdir -p {REMOTE_SANDBOX_DIR}")
        if not ok:
            return False
        
        scripts = ["setup_cgroups.sh", "modify_config.sh", "run_in_sandbox.sh",
                    "create_xui_sandbox.sh", "cleanup_sandbox.sh"]
        
        sftp = self.ssh.get_sftp()
        if not sftp:
            return False
        
        try:
            for script in scripts:
                local_path = os.path.join(SCRIPTS_DIR, script)
                if not os.path.exists(local_path):
                    logger.warning(f"Script not found: {local_path}")
                    continue
                sftp.put(local_path, f"{REMOTE_SANDBOX_DIR}/{script}")
        except Exception as e:
            logger.error(f"SFTP upload failed: {e}")
            return False
        finally:
            sftp.close()
        
        self.ssh.exec_command(f"chmod +x {REMOTE_SANDBOX_DIR}/*.sh")
        return True
    
    def setup_sandbox(self) -> bool:
        self._update_status("Настройка sandbox на VPS...")
        ok, output = self.ssh.exec_command(
            f"bash {REMOTE_SANDBOX_DIR}/setup_cgroups.sh", timeout=30
        )
        if not ok:
            logger.error(f"Setup cgroups failed: {output}")
            return False
        return True
    
    # --- Применение конфига ---
    
    def apply_config(self, config: Dict[str, Any]) -> bool:
        for param, value in config.items():
            if param in ("baseline", "reasoning"):
                continue
            ok, output = self.ssh.exec_command(
                f"bash {REMOTE_SANDBOX_DIR}/modify_config.sh {param} {value}",
                timeout=10
            )
            if not ok:
                logger.warning(f"Failed to apply {param}={value}: {output}")
                return False
        time.sleep(1)
        return True
    
    # --- Тестирование ---
    
    def run_test(self, config: Dict[str, Any], ai_reasoning: str = "", is_baseline: bool = False) -> ExperimentResult:
        if not is_baseline and not config.get("baseline"):
            self.apply_config(config)
        
        baseline_score = getattr(self, '_baseline_result', None)
        baseline_score_val = baseline_score.score if baseline_score else 0.0

        scores = []
        all_summaries = []
        max_iters = 5
        
        # Интеграция Smart Skip и Adaptive Exit
        for i in range(max_iters):
            if i > 0:
                time.sleep(1)
                
            results = self.traffic_gen.run_full_test(cached_metrics=self._cached_metrics)
            
            # Сохраняем кэш только при Baseline тесте на первой итерации
            if is_baseline and i == 0:
                for k in ["latency", "tcp_handshake", "tls_handshake", "dns"]:
                    if k in results and results[k].success:
                        self._cached_metrics[k] = results[k]

            summary = RemoteTrafficGenerator.get_summary(results)
            all_summaries.append(summary)
            
            sc = MetricsStorage.calculate_score(summary)
            scores.append(sc)
            
            # Smart Skip: если после 2-го замера средний Score < 80% от Baseline
            if i == 1 and not is_baseline and baseline_score_val > 0:
                avg_score = sum(scores) / len(scores)
                if avg_score < baseline_score_val * 0.8:
                    logger.info(f"Smart Skip: Score {avg_score:.1f} < 80% baseline. Aborting.")
                    self._update_status(f"Конфиг отброшен (Smart Skip на итер. {i+1})")
                    break
            
            # Adaptive Exit: если за 3 замера CV < 5%
            if i == 2:
                mean_score = sum(scores) / len(scores)
                if mean_score > 0:
                    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
                    cv = (math.sqrt(variance) / mean_score) * 100
                    if cv < 5.0:
                        logger.info(f"Adaptive Exit: Score CV={cv:.1f}%. Stopping early.")
                        self._update_status(f"Досрочный выход (Стабильность: CV={cv:.1f}%)")
                        break

        # Вычисляем финальные метрики через Trimmed Mean
        final_summary = {}
        for key in all_summaries[0].keys():
            vals = [s[key] for s in all_summaries]
            final_summary[key] = trimmed_mean(vals, trim_pct=0.2)
            
        cpu, memory = self._get_resource_usage()
        final_score = MetricsStorage.calculate_score(final_summary)
        
        experiment = ExperimentResult(
            id=None, timestamp=datetime.now().isoformat(), config=config,
            latency_ms=final_summary["latency_ms"], download_mbps=final_summary["download_mbps"],
            jitter_ms=final_summary["jitter_ms"], packet_loss_pct=final_summary["packet_loss_pct"],
            dns_ms=final_summary["dns_ms"], cpu_usage=cpu, memory_mb=memory,
            score=final_score,
            upload_mbps=final_summary.get("upload_mbps", 0),
            tcp_handshake_ms=final_summary.get("tcp_handshake_ms", 0),
            tls_handshake_ms=final_summary.get("tls_handshake_ms", 0),
            bufferbloat_ms=final_summary.get("bufferbloat_ms", 0),
            stability_cv=final_summary.get("stability_cv", 0),
            tcp_retrans=final_summary.get("tcp_retrans", 0),
            tc_backlog=final_summary.get("tc_backlog", 0),
            isp_anomaly=final_summary.get("isp_anomaly", 0),
            xray_drops=final_summary.get("xray_drops", 0),
            ai_reasoning=ai_reasoning
        )
        
        experiment.id = self.metrics.save_experiment(experiment)
        
        if self._best_result is None or final_score > self._best_result.score:
            self._best_result = experiment
            logger.info(f"New best score: {final_score} with config {config}")
        
        return experiment
    
    def _get_resource_usage(self) -> tuple:
        cpu, memory = 0.0, 0.0
        ok, output = self.ssh.exec_command("cat /sys/fs/cgroup/entropy-sandbox/cpu.stat 2>/dev/null")
        if ok:
            for line in output.split('\n'):
                if line.startswith('usage_usec'):
                    try: cpu = float(line.split()[1]) / 1_000_000
                    except (ValueError, IndexError): pass
        
        ok, output = self.ssh.exec_command("cat /sys/fs/cgroup/entropy-sandbox/memory.current 2>/dev/null")
        if ok:
            try: memory = int(output.strip()) / (1024 * 1024)
            except ValueError: pass
        
        return cpu, memory
    
    # --- AI Client ---
    
    def _create_ai_client(self):
        from openai import OpenAI
        
        provider = self.cfg.get("ai_provider", "openai_compatible")
        api_key = self.cfg.ai_key
        base_url = self.cfg.get("ai_base_url")
        model = self.cfg.get("ai_model", "gpt-4o")
        
        if not api_key:
            raise ValueError("API Key не настроен")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url if provider == "openai_compatible" else None
        )
        return client, model
    
    def _ask_ai(self, client, model: str, messages: list) -> Dict[str, Any]:
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}")
            return {"action": "finish", "reasoning": "Parse error", "should_continue": False}
        except Exception as e:
            logger.error(f"AI API error: {e}")
            return {"action": "finish", "reasoning": str(e), "should_continue": False}
    
    # --- Главный цикл оптимизации ---
    
    def run_optimization(self, max_experiments: int = 10) -> Optional[ExperimentResult]:
        """
        AI-driven цикл оптимизации:
        1. Сбор контекста сервера
        2. Deploy + Setup sandbox
        3. Baseline
        4. AI loop: анализ → [SSH диагностика] → конфиг → тест → анализ
        5. Cleanup
        """
        self._is_running = True
        self._current_experiment = 0
        self._total_experiments = max_experiments
        self._best_result = None
        self._ssh_calls_used = 0
        self._cleaned_up = False
        self._cached_metrics = {}
        
        try:
            # 1. Сбор контекста
            server_context = self.collect_server_context()
            
            # 2. Deploy
            if not self.deploy_scripts():
                self._update_status("Ошибка: не удалось загрузить скрипты")
                return None
            
            # 3. Setup sandbox
            if not self.setup_sandbox():
                self._update_status("Ошибка: не удалось настроить sandbox")
                return None
            
            # 4. AI client
            self._update_status("Подключение к AI...")
            client, model = self._create_ai_client()
            
            # 5. Baseline
            self._update_status("Замер baseline...")
            self._update_progress(0, max_experiments)
            baseline = self.run_test({"baseline": True}, ai_reasoning="Baseline: текущая конфигурация", is_baseline=True)
            self._baseline_result = baseline  # Сохраняем baseline текущей сессии
            
            # 6. AI conversation
            messages = [
                {"role": "system", "content": EAIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"""Начинаем оптимизацию VPN.

## КОНТЕКСТ СЕРВЕРА
{json.dumps(server_context, ensure_ascii=False, indent=2)}

## BASELINE МЕТРИКИ (score: {baseline.score})
### Базовые
- Latency: {baseline.latency_ms} ms
- Download: {baseline.download_mbps} Mbps
- Upload: {baseline.upload_mbps} Mbps
- Jitter: {baseline.jitter_ms} ms
- Packet Loss: {baseline.packet_loss_pct}%
- DNS: {baseline.dns_ms} ms
### Продвинутые и Телеметрия
- TCP Handshake: {baseline.tcp_handshake_ms} ms
- TLS Handshake: {baseline.tls_handshake_ms} ms
- Bufferbloat: {baseline.bufferbloat_ms} ms
- Stability: {baseline.stability_cv}% CV
- TCP Retrans: {baseline.tcp_retrans} pkts
- TC Backlog: {baseline.tc_backlog} pkts
- ISP Anomaly: {baseline.isp_anomaly}
- Xray Drops: {baseline.xray_drops} errs

Проанализируй контекст и предложи первое действие. Ты можешь:
1. Выполнить SSH-команду для дополнительной диагностики (action: "ssh_command")
2. Предложить конфигурацию для тестирования (action: "apply_config")

Ответь в JSON формате."""}
            ]
            
            # AI Decision Loop
            experiment_idx = 0
            for step in range(max_experiments * 2):  # Запас на SSH-команды
                if not self._is_running:
                    break
                
                if experiment_idx >= max_experiments:
                    break
                
                ai_response = self._ask_ai(client, model, messages)
                action = ai_response.get("action", "apply_config")
                reasoning = ai_response.get("reasoning", "")
                should_continue = ai_response.get("should_continue", True)
                
                messages.append({"role": "assistant", "content": json.dumps(ai_response, ensure_ascii=False)})
                
                # --- SSH диагностика ---
                if action == "ssh_command":
                    ssh_cmd = ai_response.get("ssh_command", "")
                    if ssh_cmd and self._ssh_calls_used < self._max_ssh_calls:
                        self._ssh_calls_used += 1
                        self._update_status(f"AI SSH [{self._ssh_calls_used}/{self._max_ssh_calls}]: {ssh_cmd[:50]}...")
                        logger.info(f"AI SSH command ({self._ssh_calls_used}): {ssh_cmd}")
                        
                        ok, output = self.ssh.exec_command(ssh_cmd, timeout=15)
                        result_text = output if ok else f"Error: {output}"
                        
                        messages.append({"role": "user", "content": f"""Результат SSH-команды `{ssh_cmd}`:
```
{result_text[:2000]}
```
Осталось SSH-запросов: {self._max_ssh_calls - self._ssh_calls_used}/{self._max_ssh_calls}.
Осталось экспериментов: {max_experiments - experiment_idx}/{max_experiments}.
Продолжай анализ."""})
                    else:
                        messages.append({"role": "user", "content": 
                            f"Лимит SSH-запросов исчерпан ({self._max_ssh_calls}). Используй apply_config или finish."})
                    continue
                
                # --- Финиш ---
                if action == "finish" or not should_continue:
                    # Guard: не позволяем AI выйти раньше 5 экспериментов
                    if experiment_idx < 5:
                        messages.append({"role": "user", "content": 
                            f"Рано останавливаться! Проведено только {experiment_idx} экспериментов из минимум 5. "
                            f"Протестируй другие значения congestion, MTU или buffer_size. Продолжай."})
                        continue
                    summary = ai_response.get("summary", "Оптимизация завершена")
                    self._update_status(f"AI: {summary}")
                    break
                
                # --- Применение конфига ---
                config = ai_response.get("config", {})
                if not config:
                    messages.append({"role": "user", "content": "Пустой config. Предложи параметры или установи action: finish."})
                    continue
                
                experiment_idx += 1
                self._update_progress(experiment_idx, max_experiments)
                self._update_status(f"Эксперимент {experiment_idx}: {json.dumps(config)}")
                
                result = self.run_test(config, ai_reasoning=reasoning)
                
                logger.info(f"Experiment {experiment_idx}: score={result.score}, config={config}")
                
                messages.append({"role": "user", "content": f"""Результаты эксперимента {experiment_idx}:
- Config: {json.dumps(config)}
- Score: {result.score} (baseline: {baseline.score}, лучший: {self._best_result.score})
### Базовые метрики
- Latency: {result.latency_ms} ms (baseline: {baseline.latency_ms})
- Download: {result.download_mbps} Mbps (baseline: {baseline.download_mbps})
- Upload: {result.upload_mbps} Mbps (baseline: {baseline.upload_mbps})
- Jitter: {result.jitter_ms} ms (baseline: {baseline.jitter_ms})
- Packet Loss: {result.packet_loss_pct}% (baseline: {baseline.packet_loss_pct})
- DNS: {result.dns_ms} ms (baseline: {baseline.dns_ms})
### Продвинутые метрики и Телеметрия
- TCP Handshake: {result.tcp_handshake_ms} ms (baseline: {baseline.tcp_handshake_ms})
- TLS Handshake: {result.tls_handshake_ms} ms (baseline: {baseline.tls_handshake_ms})
- Bufferbloat: {result.bufferbloat_ms} ms (baseline: {baseline.bufferbloat_ms})
- Stability: {result.stability_cv}% CV (baseline: {baseline.stability_cv})
- TCP Retrans: {result.tcp_retrans} pkts (baseline: {baseline.tcp_retrans})
- TC Backlog: {result.tc_backlog} pkts (baseline: {baseline.tc_backlog})
- ISP Anomaly: {result.isp_anomaly} (baseline: {baseline.isp_anomaly})
- Xray Drops: {result.xray_drops} errs (baseline: {baseline.xray_drops})

Осталось экспериментов: {max_experiments - experiment_idx}/{max_experiments}. SSH запросов: {self._max_ssh_calls - self._ssh_calls_used}/{self._max_ssh_calls}.
Предложи следующее действие."""})
            
            if self._best_result:
                self._update_status(f"Готово! Лучший score: {self._best_result.score}")
            
            return self._best_result
            
        except Exception as e:
            logger.error(f"EAIS optimization error: {e}")
            self._update_status(f"Ошибка: {e}")
            return None
        finally:
            self._cleanup()
            self._is_running = False
    
    def _cleanup(self):
        if not hasattr(self, '_cleaned_up') or self._cleaned_up:
            return
        self._cleaned_up = True
        self._update_status("Очистка sandbox...")
        self.ssh.exec_command(f"bash {REMOTE_SANDBOX_DIR}/cleanup_sandbox.sh 2>/dev/null")
        self.ssh.exec_command(f"rm -rf {REMOTE_SANDBOX_DIR}")
    
    def get_recommendation(self) -> Dict[str, Any]:
        if self._best_result is None:
            return {"error": "Эксперименты не проводились"}
        
        # Используем baseline текущей сессии, а не первый эксперимент из БД
        baseline = getattr(self, '_baseline_result', None) or self.metrics.get_baseline()
        improvement = 0.0
        if baseline and baseline.score > 0:
            improvement = ((self._best_result.score - baseline.score) / baseline.score) * 100
        
        return {
            "config": self._best_result.config,
            "score": self._best_result.score,
            "baseline_score": baseline.score if baseline else None,
            "improvement_pct": round(improvement, 2),
            "metrics": self._best_result.metrics_dict,
            "ai_reasoning": self._best_result.ai_reasoning,
            "experiments_run": self.metrics.get_experiment_count()
        }
    
    def stop(self):
        self._is_running = False
        logger.info("EAIS: Stopping experiments...")
