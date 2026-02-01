
import sys
import os
import signal
import sqlite3
import pandas as pd
import time
import logging
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, Qt, QObject
from PySide6.QtQuickControls2 import QQuickStyle

# --- OPTIMIZATION FOR WINDOWS ---
os.environ["QSG_RHI_BACKEND"] = "opengl"
# QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # Deprecated in Qt6
# QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps) # Deprecated in Qt6

# Import Core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.dirname(__file__))  # Add src folder itself
from core.config import ConfigManager
from core.data_loader import DataLoader
from core.security_engine import SecurityEngine
from ai.bridge import EAIIWorker, AIAnalyzer
from viewmodels.MainViewModel import MainViewModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataBridge")

class DataBridge(QObject):
    def __init__(self, cfg, main_vm):
        super().__init__()
        self.cfg = cfg
        self.vm = main_vm
        self.loader = None
        self.eaii_worker = None
        self.ai_analyzer = None
        self.last_raw_packets = None
        self.last_metrics = {}
        self.discovery_data = {}
        
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
        self.loader = DataLoader(self.cfg)
        self.loader.finished.connect(self.on_data_ready)
        self.loader.start()

    def run_eaii(self):
        if not self.cfg.get("eaii_enabled", True): return
        if self.eaii_worker and self.eaii_worker.isRunning(): return
        
        logger.info("Starting Background EAII Analysis...")
        self.vm.set_eaii_analyzing(True)
        
        self.eaii_worker = EAIIWorker(self.cfg, self.last_metrics, self.discovery_data)
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
        
        self.ai_analyzer = AIAnalyzer(self.cfg, self.last_metrics, self.discovery_data)
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
            
        self.discovery_data = discovery or {}
        current_pps = 0
        current_jitter = 0.0
        probing_count = 0
        
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
            probing_count = len(probing_list)
            
        # 4. DB Data (CPU/RAM/Users)
        cpu = 0.0
        ram = 0.0
        users_list = []
        try:
            conn = sqlite3.connect(self.cfg.get("local_db"))
            
            # System stats
            query_sys = "SELECT cpu, ram FROM system_stats ORDER BY timestamp DESC LIMIT 1"
            df_sys = pd.read_sql(query_sys, conn)
            
            # User stats
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
                        "ip": "N/A", # IP is not directly in this table
                        "traffic": f"{round(row['d'] + row['u'], 2)} MB"
                    })
        except Exception as e:
            logger.error(f"DB Error: {e}")

        # 5. RISK
        risk_data = SecurityEngine.calculate_risk(current_pps, current_jitter, probing_count)
        
        self.last_metrics = {
            "cpu": cpu, "ram": ram, "pps": current_pps, "jitter": current_jitter,
            "risk_score": risk_data[2], "users_count": len(users_list)
        }
        
        # Run EAII on first successful sync (when data is available)
        if self._first_run and self.cfg.get("eaii_enabled", True):
            self._first_run = False
            self.run_eaii()

        # UPDATE VM
        self.vm.update_metrics(cpu, ram, current_pps, current_jitter, risk_data)
        self.vm.update_users(users_list)
        self.vm.update_probes(probing_list if security_data else [])

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(sys.argv)
    
    # Set application icon (shows in taskbar and window)
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/assets/logo.png"))
    app.setWindowIcon(QIcon(icon_path))
    
    engine = QQmlApplicationEngine()
    
    cfg = ConfigManager(config_path="config.json")
    main_vm = MainViewModel(None, SecurityEngine, cfg)
    bridge = DataBridge(cfg, main_vm)
    
    engine.rootContext().setContextProperty("mainVM", main_vm)
    
    def on_warnings(warnings):
        for w in warnings:
            try: print(f"QML Warning: {w.toString()}")
            except UnicodeEncodeError: pass
    engine.warnings.connect(on_warnings)
    
    qml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/qml/Main.qml"))
    engine.load("file:///" + qml_path.replace("\\", "/"))
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    bridge.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
