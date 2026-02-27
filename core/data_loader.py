"""
Entropy - Data Loader
Loads metrics from VPS using persistent SSH connection
"""

import logging
import time
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class DataLoader(QThread):
    """Поток для загрузки данных с использованием persistent SSH соединения."""
    finished = Signal(bool, str, dict, dict)  # success, message, discovery, security

    def __init__(self, ssh_manager, config_manager, skip_discovery: bool = False):
        super().__init__()
        self.ssh = ssh_manager
        self.cfg = config_manager
        self.skip_discovery = skip_discovery

    def run(self):
        discovery_data = {}
        security_data = {}
        
        try:
            # Подключаемся (или используем существующее соединение)
            if not self.ssh.connect():
                self.finished.emit(False, "SSH connection failed", {}, {})
                return
            
            # --- AUTO DISCOVERY (только при первом запуске или смене сервера) ---
            if not self.skip_discovery:
                try:
                    success, cpu_model = self.ssh.exec_command("lscpu | grep 'Model name' | cut -d ':' -f 2")
                    if success:
                        discovery_data['cpu_model'] = cpu_model.strip()
                    
                    success, ram_total = self.ssh.exec_command("free -h | grep Mem | awk '{print $2}'")
                    if success:
                        discovery_data['ram_total'] = ram_total.strip()
                    
                    success, os_version = self.ssh.exec_command("cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f 2")
                    if success:
                        discovery_data['os_version'] = os_version.strip()
                    
                    panels = []
                    success, ps_output = self.ssh.exec_command("ps aux")
                    if success:
                        ps_lower = ps_output.lower()
                        if 'marzban' in ps_lower: panels.append("Marzban")
                        if 'x-ui' in ps_lower: panels.append("X-UI")
                        if 'v2ray' in ps_lower: panels.append("Xray/V2Ray")
                        if 'sing-box' in ps_lower: panels.append("Sing-box")
                    discovery_data['detected_panels'] = ", ".join(panels) if panels else "Не определено"
                    
                    logger.info(f"Auto-discovery complete: {discovery_data}")
                except Exception as de:
                    logger.warning(f"Discovery fail: {de}")
            else:
                logger.debug("Skipping auto-discovery (cached)")

            # --- SECURITY METRICS ---
            try:
                # 1. Packet Counters for PPS
                cmd_pps = "cat /proc/net/dev | grep -v 'lo:' | grep ':' | head -n 1 | sed 's/.*://' | awk '{print $2}' | tr -cd '0-9'"
                success, raw_packets = self.ssh.exec_command(cmd_pps)
                if success:
                    security_data['raw_packets'] = raw_packets.strip()
                
                # 2. Jitter (Ping to 8.8.8.8)
                cmd_jit = "ping -c 4 -i 0.2 8.8.8.8 | grep 'time=' | awk -F'time=' '{print $2}' | awk '{print $1}'"
                success, latencies_raw = self.ssh.exec_command(cmd_jit, timeout=15)
                if success:
                    latencies = latencies_raw.strip().split('\n')
                    security_data['latencies'] = [float(l) for l in latencies if l]
                
                # 3. Probing (Failed SSH logins)
                cmd_ssh = "grep 'Failed password' /var/log/auth.log | tail -n 5 | awk '{print $(NF-3)}'"
                success, probes_raw = self.ssh.exec_command(cmd_ssh)
                if success:
                    probes = probes_raw.strip().split('\n')
                    security_data['ssh_probes'] = [p for p in probes if p]
                
                logger.info(f"Security metrics collected: Probes={len(security_data.get('ssh_probes', []))}")
            except Exception as se:
                logger.warning(f"Security data collection failed: {se}")

            # --- DOWNLOAD DB ---
            remote_db = self.cfg.get("remote_db")
            local_db = self.cfg.get("local_db")
            
            logger.info(f"Загрузка БД: {remote_db} -> {local_db}")
            if self.ssh.download_file(remote_db, local_db):
                self.finished.emit(True, "Данные обновлены", discovery_data, security_data)
            else:
                self.finished.emit(False, "SFTP download failed", discovery_data, security_data)
                
        except Exception as e:
            error_msg = f"DataLoader error: {e}"
            logger.error(error_msg)
            self.finished.emit(False, error_msg, {}, {})
