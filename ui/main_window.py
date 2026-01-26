import sqlite3
import pandas as pd
import time
import logging
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QIcon

from core.data_loader import DataLoader
from core.security_engine import SecurityEngine
from ai.bridge import AIAnalyzer
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.security_tab import SecurityTab
from ui.tabs.ai_tab import AITab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.system_info_tab import SystemInfoTab
from ui.styles import STYLE_SHEET

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("Entropy v0.30.0 - Advanced VPN Analytics & Monitoring")
        self.resize(1000, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        # Window Icon
        self.setWindowIcon(QIcon("assets/logo.png"))
        
        # State
        self.last_metrics = {}
        self.server_meta = {}
        self.history_cpu = []
        self.history_ram = []
        self.history_pps = []
        self.history_jitter = []
        self.timestamps = []
        
        self.init_ui()
        
        # Workers
        self.data_worker = DataLoader(self.cfg)
        self.data_worker.finished.connect(self.on_data_ready)
        
        self.ai_worker = None
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(self.cfg.get("sync_interval_ms", 10000))
        
        self.refresh_data()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        
        # Status Bar Replacement (Top)
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background: #161b22; border-bottom: 1px solid #30363d; padding: 5px;")
        status_layout = QHBoxLayout(self.status_frame)
        
        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap("assets/logo.png")
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        status_layout.addWidget(self.logo_label)
        
        self.status_label = QLabel("🚀 Инициализация...")
        self.risk_label = QLabel("РИСК: UNKNOWN")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.risk_label)
        self.main_layout.addWidget(self.status_frame)
        
        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.tab_dash = DashboardTab()
        self.tab_sec = SecurityTab()
        self.tab_ai = AITab(self.run_ai_analysis)
        self.tab_settings = SettingsTab(self.cfg, self.on_settings_saved)
        self.tab_info = SystemInfoTab(self.cfg, None)
        
        self.tabs.addTab(self.tab_dash, "Dashboard")
        self.tabs.addTab(self.tab_sec, "Security Analytics")
        self.tabs.addTab(self.tab_ai, "AI Insights")
        self.tabs.addTab(self.tab_info, "System Info")
        self.tabs.addTab(self.tab_settings, "Settings")

    def refresh_data(self):
        if not self.data_worker.isRunning():
            self.status_label.setText("Синхронизация...")
            self.data_worker.start()

    def on_settings_saved(self):
        self.status_label.setText("Настройки сохранены. Переподключение...")
        self.timer.stop()
        self.timer.start(self.cfg.get("sync_interval_ms", 10000))
        self.refresh_data()

    def on_data_ready(self, success, message, discovery, security_data=None):
        if not success:
            self.status_label.setText(f"ОШИБКА: {message}")
            self.status_label.setStyleSheet("color: #ff4444;")
            return
            
        self.status_label.setText(f"Обновлено в {time.strftime('%H:%M:%S')}")
        self.status_label.setStyleSheet("color: #00ff00;")
        
        if discovery:
            self.server_meta = discovery
            self.tab_info.update_auto_data(discovery)
            
        # --- Process Security Metrics ---
        if security_data:
            # 1. PPS (from delta)
            raw_packets = security_data.get('raw_packets')
            current_pps = 0
            if hasattr(self, 'last_raw_packets'):
                current_pps = SecurityEngine.calculate_pps(
                    raw_packets, self.last_raw_packets, self.cfg.get("sync_interval_ms", 10000)
                )
            self.last_raw_packets = raw_packets
            
            # 2. Jitter (from latencies)
            current_jitter = SecurityEngine.calculate_jitter(security_data.get('latencies', []))
            
            # 3. Probing (from logs)
            probing_list = SecurityEngine.parse_probes(security_data.get('ssh_probes', []))
            
            # Update History
            self.history_pps.append(current_pps)
            self.history_jitter.append(current_jitter)
            self.timestamps.append(time.time())
            
            if len(self.history_pps) > 50:
                self.history_pps.pop(0); self.history_jitter.pop(0); self.timestamps.pop(0)
            
            # Update UI
            self.tab_sec.update_data(self.history_pps, self.timestamps, self.history_jitter, probing_list)
            
            risk_label, color = SecurityEngine.calculate_risk(current_pps, current_jitter)
            self.risk_label.setText(f"РИСК: {risk_label}")
            self.risk_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # Store for AI
            self.last_metrics.update({
                "pps": current_pps,
                "jitter": current_jitter,
                "risk_label": risk_label,
                "probing_count": len(probing_list)
            })

        self.process_local_db()

    def process_local_db(self):
        try:
            conn = sqlite3.connect(self.cfg.get("local_db"))
            
            # Users Stats (Corrected)
            query_users = "SELECT email, MAX(down)/1024/1024 as d, MAX(up)/1024/1024 as u FROM user_stats GROUP BY email ORDER BY d DESC"
            df_users = pd.read_sql(query_users, conn)
            
            # System Metrics (Corrected)
            query_sys = "SELECT cpu, ram, timestamp FROM system_stats ORDER BY timestamp DESC LIMIT 100"
            df_sys = pd.read_sql(query_sys, conn)
            conn.close()
            
            if not df_sys.empty:
                latest = df_sys.iloc[0]
                self.last_metrics = {
                    "cpu": latest['cpu'],
                    "ram": latest['ram'],
                    "users_count": len(df_users)
                }
                
                # Обновляем графики (реверс для правильного порядка времени)
                try:
                    def parse_ts(ts):
                        try:
                            # Try Unix float
                            return float(ts)
                        except:
                            # Try string format '2026-01-26 02:02:08'
                            from datetime import datetime
                            return datetime.strptime(str(ts), '%Y-%m-%d %H:%M:%S').timestamp()

                    self.history_cpu = [float(x) for x in df_sys['cpu'].values[::-1]]
                    self.history_ram = [float(x) for x in df_sys['ram'].values[::-1]]
                    db_timestamps = [parse_ts(x) for x in df_sys['timestamp'].values[::-1]]
                    
                    self.tab_dash.update_charts(self.history_cpu, self.history_ram, db_timestamps)
                except Exception as ge:
                    logger.error(f"Ошибка отрисовки графиков: {ge}")
                
                # Обновляем таблицу пользователей
                # Преобразуем для таба (User, IP, Traffic) - IP в этой БД может не быть, ставим N/A
                df_ui_users = pd.DataFrame({
                    'user': df_users['email'],
                    'ip': ['N/A'] * len(df_users),
                    'traffic': (df_users['d'] + df_users['u']).round(2).astype(str) + " MB"
                })
                self.tab_dash.update_users(df_ui_users)
                
                self.last_metrics.update({
                    "cpu": latest['cpu'],
                    "ram": latest['ram']
                })
                
        except Exception as e:
            logger.error(f"БД Ошибка: {e}")

    def run_ai_analysis(self):
        if self.ai_worker and self.ai_worker.isRunning():
            return
            
        context = self.tab_info.get_full_context(self.server_meta.get('detected_panels', 'N/A'))
        self.tab_ai.set_loading(True)
        
        self.ai_worker = AIAnalyzer(self.cfg, self.last_metrics, context)
        self.ai_worker.result_ready.connect(self.tab_ai.show_result)
        self.ai_worker.result_ready.connect(lambda: self.tab_ai.set_loading(False))
        self.ai_worker.error_occurred.connect(self.tab_ai.show_error)
        self.ai_worker.error_occurred.connect(lambda: self.tab_ai.set_loading(False))
        self.ai_worker.start()
