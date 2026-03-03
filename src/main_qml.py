
import sys
import os
import signal
import sqlite3
import pandas as pd
import time
import logging

# --- PYINSTALLER FROZEN PATH DETECTION ---
if getattr(sys, 'frozen', False):
    # Running as bundled exe
    BASE_PATH = sys._MEIPASS
    # Персистентная папка для данных пользователя (config, db, logs)
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Entropy')
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(DATA_DIR, 'entropy.log'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    # Running from source
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = BASE_PATH  # При разработке — корень проекта
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("DataBridge")

# Add paths for imports
sys.path.insert(0, BASE_PATH)
sys.path.insert(0, os.path.join(BASE_PATH, 'src'))

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, Qt, QObject
from PySide6.QtQuickControls2 import QQuickStyle

# --- OPTIMIZATION FOR WINDOWS ---
os.environ["QSG_RHI_BACKEND"] = "opengl"

from core.config import ConfigManager
from core.data_loader import DataLoader
from core.ssh_manager import SSHConnectionManager
from core.security_engine import SecurityEngine
from core.edp.pipeline import EDPPipeline
from ai.bridge import EAIIWorker, AIAnalyzer
from viewmodels.MainViewModel import MainViewModel
from viewmodels.SandboxViewModel import SandboxViewModel

class DataBridge(QObject):
    def __init__(self, cfg, main_vm, ssh_manager):
        super().__init__()
        self.cfg = cfg
        self.vm = main_vm
        self.ssh = ssh_manager  # Persistent SSH connection
        self.loader = None
        self.eaii_worker = None
        self.ai_analyzer = None
        self.last_raw_packets = None
        self.last_metrics = {}
        self.discovery_data = {}
        self._discovery_done = False
        self._last_server_ip = None
        
        # EDP Pipeline — центральный обработчик данных
        self.edp = EDPPipeline(data_dir=DATA_DIR)
        self._last_ai_context = None
        
        # Connect manual trigger to Interactive Deep Scan
        self.vm.manualScanRequested.connect(self.run_interactive_analysis)
        
        # Timer for data sync
        self.timer = QTimer()
        self.timer.timeout.connect(self.request_data)
        self.interval = self.cfg.get("sync_interval_ms", 10000)
        
        # Timer for EAII periodic execution
        self._eaii_timer = QTimer()
        self._eaii_timer.timeout.connect(self.run_eaii)
        self._first_run = True
        
    def start(self):
        self.request_data()
        self.timer.start(self.interval)
        
        # Start EAII periodic timer if enabled
        if self.cfg.get("eaii_enabled", True):
            eaii_interval_ms = self.cfg.get("eaii_interval_min", 5) * 60 * 1000
            self._eaii_timer.start(eaii_interval_ms)

    def request_data(self):
        if self.loader and self.loader.isRunning():
            return
        
        # Проверяем нужно ли запускать discovery
        current_ip = self.cfg.get("ip")
        need_discovery = not self._discovery_done or current_ip != self._last_server_ip
        
        self.loader = DataLoader(self.ssh, self.cfg, skip_discovery=not need_discovery)
        self.loader.finished.connect(self.on_data_ready)
        self.loader.start()
        
        # Обновляем состояние после запуска
        if need_discovery:
            self._last_server_ip = current_ip

    def run_eaii(self):
        if not self.cfg.get("eaii_enabled", True): return
        if self.eaii_worker and self.eaii_worker.isRunning(): return
        
        logger.info("Starting Background EAII Analysis...")
        self.vm.set_eaii_analyzing(True)
        
        # EDP передаёт AIContext вместо сырых метрик
        self.eaii_worker = EAIIWorker(self.cfg, self.last_metrics, self.discovery_data, ai_context=self._last_ai_context)
        self.eaii_worker.analysis_ready.connect(self.on_eaii_ready)
        self.eaii_worker.start()

    def on_eaii_ready(self, score, explanation):
        logger.info(f"EAII Ready: {score}")
        self.vm.update_eaii(score, explanation)

    def run_interactive_analysis(self):
        """Triggers deep SSH-powered diagnostic."""
        if self.ai_analyzer and self.ai_analyzer.isRunning(): return
        
        logger.info("Starting Interactive Deep AI Scan...")
        self.vm.set_interactive_analyzing(True)
        
        # AIAnalyzer тоже получает EDP AIContext
        self.ai_analyzer = AIAnalyzer(self.cfg, self.last_metrics, self.discovery_data, ai_context=self._last_ai_context)
        self.ai_analyzer.result_ready.connect(self.on_interactive_ready)
        self.ai_analyzer.error_occurred.connect(self.on_interactive_error)
        self.ai_analyzer.start()

    def on_interactive_ready(self, result):
        logger.info("Interactive AI Scan Complete")
        self.vm.update_interactive_ready(result)

    def on_interactive_error(self, message):
        logger.error(f"Interactive AI Error: {message}")
        self.vm.update_interactive_ready(f"ERROR: {message}")

    def on_data_ready(self, success, message, discovery, security_data):
        if not success:
            logger.error(f"Sync fail: {message}")
            return
        
        # Обновляем discovery только если данные есть (не пропустили)
        if discovery:
            self.discovery_data = discovery
            self._discovery_done = True
        
        current_pps = 0
        current_jitter = 0.0
        probing_list = []
        
        if security_data:
            # 1. PPS
            raw_packets = security_data.get('raw_packets')
            if self.last_raw_packets:
                current_pps = SecurityEngine.calculate_pps(
                    raw_packets, self.last_raw_packets, self.interval
                )
            self.last_raw_packets = raw_packets
            
            # 2. JITTER
            current_jitter = SecurityEngine.calculate_jitter(security_data.get('latencies', []))
            
            # 3. PROBING
            probing_list = SecurityEngine.parse_probes(security_data.get('ssh_probes', []))
            
        # 4. DB Data (CPU/RAM/Users)
        cpu = 0.0
        ram = 0.0
        users_list = []
        try:
            conn = sqlite3.connect(self.cfg.get("local_db"))
            
            query_sys = "SELECT cpu, ram FROM system_stats ORDER BY timestamp DESC LIMIT 1"
            df_sys = pd.read_sql(query_sys, conn)
            
            query_users = "SELECT email, MAX(down)/1024/1024 as d, MAX(up)/1024/1024 as u FROM user_stats GROUP BY email ORDER BY d DESC"
            df_users = pd.read_sql(query_users, conn)
            
            conn.close()
            
            if not df_sys.empty:
                cpu = float(df_sys.iloc[0]['cpu'])
                ram = float(df_sys.iloc[0]['ram'])
                
            if not df_users.empty:
                for _, row in df_users.iterrows():
                    users_list.append({
                        "user": row['email'],
                        "ip": "N/A",
                        "traffic": f"{round(row['d'] + row['u'], 2)} MB"
                    })
        except sqlite3.OperationalError:
            pass
        except Exception as e:
            logger.error(f"DB Error: {e}")

        # === EDP Pipeline — единственный обработчик данных ===
        raw_edp = {
            "cpu": cpu, "ram": ram, "pps": current_pps, "jitter": current_jitter,
            "users_count": len(users_list),
            "probes": probing_list,
        }
        edp_result = self.edp.process(raw_edp)
        self._last_ai_context = edp_result.ai_context
        
        # Risk score теперь вычисляется EDP (не SecurityEngine)
        risk_data = edp_result.risk_data
        
        self.last_metrics = {
            "cpu": cpu, "ram": ram, "pps": current_pps, "jitter": current_jitter,
            "risk_score": risk_data[2], "users_count": len(users_list)
        }
        
        # EAII на первом успешном sync
        if self._first_run and self.cfg.get("eaii_enabled", True):
            self._first_run = False
            self.run_eaii()

        # UPDATE VM
        self.vm.update_metrics(cpu, ram, current_pps, current_jitter, risk_data)
        self.vm.update_metrics_edp(edp_result)
        self.vm.update_users(users_list)
        self.vm.update_probes(probing_list if security_data else [])

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(sys.argv)
    
    # Set application icon (shows in taskbar and window)
    icon_path = os.path.join(BASE_PATH, "resources", "assets", "logo.png")
    app.setWindowIcon(QIcon(icon_path))
    
    engine = QQmlApplicationEngine()
    
    # Конфиг и БД хранятся в персистентной папке DATA_DIR
    config_path = os.path.join(DATA_DIR, "config.json")
    cfg = ConfigManager(config_path=config_path)
    
    # Если local_db — относительный путь, привязать к DATA_DIR
    local_db = cfg.get("local_db", "local_stats.db")
    if not os.path.isabs(local_db):
        cfg.set("local_db", os.path.join(DATA_DIR, local_db))
    ssh_manager = SSHConnectionManager(cfg)  # SSH для DataBridge (sync)
    ssh_sandbox = SSHConnectionManager(cfg)  # Отдельное SSH для EAIS (sandbox)
    main_vm = MainViewModel(None, SecurityEngine, cfg)
    sandbox_vm = SandboxViewModel(ssh_sandbox, cfg)
    bridge = DataBridge(cfg, main_vm, ssh_manager)
    
    engine.rootContext().setContextProperty("mainVM", main_vm)
    engine.rootContext().setContextProperty("sandboxVM", sandbox_vm)
    
    def on_warnings(warnings):
        for w in warnings:
            try: print(f"QML Warning: {w.toString()}")
            except UnicodeEncodeError: pass
    engine.warnings.connect(on_warnings)
    
    qml_path = os.path.join(BASE_PATH, "resources", "qml", "Main.qml")
    engine.load("file:///" + qml_path.replace("\\", "/"))
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    bridge.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
