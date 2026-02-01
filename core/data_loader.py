import paramiko
import os
import logging
import time
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)

class DataLoader(QThread):
    """Поток для загрузки данных и выполнения авто-дискавери на сервере."""
    finished = Signal(bool, str, dict, dict) # success, message, discovery, security

    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager

    def run(self):
        ssh = None
        discovery_data = {}
        try:
            ip = self.cfg.get("ip")
            port = self.cfg.get("port")
            user = self.cfg.get("user")
            key_path = self.cfg.get("key_path")
            
            logger.info(f"Подключение к {ip}:{port}...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if not key_path or not os.path.exists(key_path):
                raise FileNotFoundError(f"SSH ключ не найден: {key_path}")

            ssh.connect(
                hostname=ip, port=port, 
                username=user, key_filename=key_path, 
                timeout=15, banner_timeout=30 # Увеличиваем таймауты
            )
            
            # --- AUTO DISCOVERY ---
            try:
                stdin, stdout, stderr = ssh.exec_command("lscpu | grep 'Model name' | cut -d ':' -f 2")
                discovery_data['cpu_model'] = stdout.read().decode().strip()
                
                stdin, stdout, stderr = ssh.exec_command("free -h | grep Mem | awk '{print $2}'")
                discovery_data['ram_total'] = stdout.read().decode().strip()
                
                stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release | grep PRETTY_NAME | cut -d '\"' -f 2")
                discovery_data['os_version'] = stdout.read().decode().strip()
                
                panels = []
                stdin, stdout, stderr = ssh.exec_command("ps aux")
                ps_output = stdout.read().decode().lower()
                if 'marzban' in ps_output: panels.append("Marzban")
                if 'x-ui' in ps_output: panels.append("X-UI")
                if 'v2ray' in ps_output: panels.append("Xray/V2Ray")
                if 'sing-box' in ps_output: panels.append("Sing-box")
                discovery_data['detected_panels'] = ", ".join(panels) if panels else "Не определено"
                
                logger.info(f"Auto-discovery complete: {discovery_data}")
            except Exception as de:
                logger.warning(f"Discovery fail: {de}")

            # --- SECURITY METRICS ---
            security_data = {}
            try:
                # 1. Packet Counters for PPS (Cumulative)
                # Robustly find the first non-lo interface and get packet count
                # sed removes interface name (e.g. eth0:), then awk takes 2nd field (packets)
                cmd_pps = "cat /proc/net/dev | grep -v 'lo:' | grep ':' | head -n 1 | sed 's/.*://' | awk '{print $2}' | tr -cd '0-9'"
                stdin, stdout, stderr = ssh.exec_command(cmd_pps)
                security_data['raw_packets'] = stdout.read().decode().strip()
                
                # 2. Jitter simulation (Ping to 8.8.8.8)
                # We do 4 quick pings and calculate the variation later or just send the result
                cmd_jit = "ping -c 4 -i 0.2 8.8.8.8 | grep 'time=' | awk -F'time=' '{print $2}' | awk '{print $1}'"
                stdin, stdout, stderr = ssh.exec_command(cmd_jit)
                latencies = stdout.read().decode().strip().split('\n')
                security_data['latencies'] = [float(l) for l in latencies if l]
                
                # 3. Probing (Failed SSH logins)
                cmd_ssh = "grep 'Failed password' /var/log/auth.log | tail -n 5 | awk '{print $(NF-3)}'"
                stdin, stdout, stderr = ssh.exec_command(cmd_ssh)
                probes = stdout.read().decode().strip().split('\n')
                security_data['ssh_probes'] = [p for p in probes if p]
                
                logger.info(f"Security metrics collected: Probes={len(security_data['ssh_probes'])}")
            except Exception as se:
                logger.warning(f"Security data collection failed: {se}")

            # --- DOWNLOAD DB ---
            sftp = ssh.open_sftp()
            try:
                remote_db = self.cfg.get("remote_db")
                local_db = self.cfg.get("local_db")
                logger.info(f"Загрузка БД: {remote_db} -> {local_db}")
                sftp.get(remote_db, local_db)
                self.finished.emit(True, "Данные обновлены", discovery_data, security_data)
            except Exception as e:
                error_msg = f"Ошибка SFTP: {e}"
                logger.error(error_msg)
                self.finished.emit(False, error_msg, discovery_data, security_data)
            finally:
                sftp.close()
                
        except Exception as e:
            error_msg = f"Ошибка SSH: {e}"
            logger.error(error_msg)
            self.finished.emit(False, error_msg, {}, {})
        finally:
            if ssh:
                ssh.close()
