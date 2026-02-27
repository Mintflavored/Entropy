
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer
from core.localization import L
import random

class MainViewModel(QObject):
    # Signals
    cpuChanged = Signal()
    ramChanged = Signal()
    ppsChanged = Signal()
    jitterChanged = Signal()
    riskChanged = Signal()
    
    # EAII Properties (Background)
    eaiiChanged = Signal()
    
    # Interactive AI Properties (Manual Deep Scan)
    interactiveChanged = Signal()
    manualScanRequested = Signal()
    
    # Security/Users Properties
    usersChanged = Signal()
    probesChanged = Signal()
    
    @Property(float, notify=eaiiChanged)
    def aiRiskScore(self): return self._ai_risk_score
    
    @Property(str, notify=eaiiChanged)
    def aiExplanation(self): return self._ai_explanation
    
    @Property(bool, notify=eaiiChanged)
    def isEaiiAnalyzing(self): return self._is_eaii_analyzing

    @Property(bool, notify=interactiveChanged)
    def isInteractiveAnalyzing(self): return self._is_interactive_analyzing
    
    @Property(str, notify=interactiveChanged)
    def aiInteractiveResult(self): return self._ai_interactive_result

    def __init__(self, data_loader, security_engine, config_manager):
        super().__init__()
        self._data_loader = data_loader
        self._security_engine = security_engine
        self._cfg = config_manager
        
        # Current Stats
        self._cpu = 0.0
        self._ram = 0.0
        self._pps = 0
        self._jitter = 0.0
        self._risk_score = 0.0
        self._risk_label = "LOW"
        self._risk_color = "#00ff00"
        
        # EAII State (Background)
        self._ai_risk_score = 0.0
        self._ai_explanation = "Waiting for data..."
        self._is_eaii_analyzing = False
        
        # Interactive AI State (Manual)
        self._ai_interactive_result = "Ready for diagnostic..."
        self._is_interactive_analyzing = False
        
        # User Statistics
        self._users_data = []
        self._probes_data = []

        # Localization Binding
        L.language_changed.connect(lambda lang: self.languageChanged.emit())
        
        # History for charts
        self._cpu_history = [0.0] * 60
        self._ram_history = [0.0] * 60
        self._pps_history = [0.0] * 60
        self._jitter_history = [0.0] * 60
        self._max_history = 60
        
    @Slot(float, str)
    def update_eaii(self, score, explanation):
        self._ai_risk_score = score
        self._ai_explanation = explanation
        self._is_eaii_analyzing = False
        self.eaiiChanged.emit()
        
    @Slot(bool)
    def set_eaii_analyzing(self, state):
        if self._is_eaii_analyzing == state: return
        self._is_eaii_analyzing = state
        self.eaiiChanged.emit()

    @Slot(str)
    def update_interactive_ready(self, result):
        self._ai_interactive_result = result
        self._is_interactive_analyzing = False
        self.interactiveChanged.emit()
        
    @Slot(bool)
    def set_interactive_analyzing(self, state):
        if self._is_interactive_analyzing == state: return
        self._is_interactive_analyzing = state
        self.interactiveChanged.emit()
        
    @Slot()
    def startManualScan(self):
        """Action slot to trigger scan without causing a state-loop."""
        if not self._is_interactive_analyzing:
            self.manualScanRequested.emit()

    def update_users(self, user_list):
        self._users_data = user_list
        self.usersChanged.emit()
        
    def update_probes(self, probe_list):
        self._probes_data = probe_list
        self.probesChanged.emit()

    def update_metrics(self, cpu, ram, pps, jitter, risk_data):
        self._cpu = cpu
        self._ram = ram
        self._pps = pps
        self._jitter = jitter
        
        # Update Histories
        self._cpu_history.append(float(cpu))
        self._ram_history.append(float(ram))
        self._pps_history.append(float(pps))
        self._jitter_history.append(float(jitter))
        
        if len(self._cpu_history) > self._max_history:
            self._cpu_history.pop(0)
            self._ram_history.pop(0)
            self._pps_history.pop(0)
            self._jitter_history.pop(0)

        self._risk_label = risk_data[0]
        self._risk_color = risk_data[1]
        self._risk_score = risk_data[2] if len(risk_data) > 2 else 0.0
        
        self.cpuChanged.emit()
        self.ramChanged.emit()
        self.ppsChanged.emit()
        self.jitterChanged.emit()
        self.riskChanged.emit()

    # --- Properties for QML ---
    
    @Property(list, notify=cpuChanged)
    def cpuHistory(self): return self._cpu_history
    
    @Property(list, notify=ramChanged)
    def ramHistory(self): return self._ram_history
    
    @Property(list, notify=ppsChanged)
    def ppsHistory(self): return self._pps_history
    
    @Property(list, notify=jitterChanged)
    def jitterHistory(self): return self._jitter_history

    @Property(list, notify=usersChanged)
    def usersData(self): return self._users_data
    
    @Property(list, notify=probesChanged)
    def probesData(self): return self._probes_data

    @Property(float, notify=cpuChanged)
    def cpu(self): return self._cpu
    
    @Property(float, notify=ramChanged)
    def ram(self): return self._ram
    
    @Property(int, notify=ppsChanged)
    def pps(self): return self._pps
    
    @Property(float, notify=jitterChanged)
    def jitter(self): return self._jitter
    
    # Settings Properties
    settingsChanged = Signal()
    languageChanged = Signal()

    @Property(dict, notify=languageChanged)
    def trans(self): return L.get_all()
    
    @Property(bool, notify=settingsChanged)
    def eaiiEnabled(self): return self._cfg.get("eaii_enabled", True)
    
    @Property(int, notify=settingsChanged)
    def syncInterval(self): return self._cfg.get("sync_interval_ms", 10000)
    
    @Property(int, notify=settingsChanged)
    def eaiiInterval(self): return self._cfg.get("eaii_interval_min", 5)
    
    @Property(str, notify=settingsChanged)
    def language(self): return self._cfg.get("language", "ru")
    
    @Property(str, notify=settingsChanged)
    def eaiiProvider(self): return self._cfg.get("eaii_provider", "openai_compatible")
    
    @Property(str, notify=settingsChanged)
    def eaiiModel(self): return self._cfg.get("eaii_model", "gpt-4o-mini")
    
    @Property(str, notify=settingsChanged)
    def eaiiBaseUrl(self): return self._cfg.get("eaii_base_url", "https://api.openai.com/v1")
    
    @Property(str, notify=settingsChanged)
    def eaiiApiKey(self): return self._cfg.eaii_key

    # Main/Interactive AI Settings
    @Property(str, notify=settingsChanged)
    def aiProvider(self): return self._cfg.get("ai_provider", "openai_compatible")
    
    @Property(str, notify=settingsChanged)
    def aiModel(self): return self._cfg.get("ai_model", "gpt-4o")
    
    @Property(str, notify=settingsChanged)
    def aiBaseUrl(self): return self._cfg.get("ai_base_url", "https://api.openai.com/v1")
    
    @Property(str, notify=settingsChanged)
    def aiApiKey(self): return self._cfg.ai_key

    # EAIS (Entropy AI Sandbox) Settings
    @Property(bool, notify=settingsChanged)
    def eaisEnabled(self): return self._cfg.get("eais_enabled", False)

    # VPS Connection Settings
    @Property(str, notify=settingsChanged)
    def vpsIp(self): return self._cfg.get("ip", "127.0.0.1")
    
    @Property(str, notify=settingsChanged)
    def vpsPort(self): return str(self._cfg.get("port", 22))
    
    @Property(str, notify=settingsChanged)
    def vpsUser(self): return self._cfg.get("user", "root")
    
    @Property(str, notify=settingsChanged)
    def sshKeyPath(self): return self._cfg.get("key_path", "")

    @Slot(bool, int, int, str, str, str, str, str, str, str, str, str, str, str, str, str, bool)
    def applySettings(self, eaii_enabled, interval, eaii_interval, lang, eaii_provider, eaii_model, eaii_url, eaii_key, ai_provider, ai_model, ai_url, ai_key, vps_ip, vps_port, vps_user, ssh_key, eais_enabled):
        # VPS Connection
        self._cfg.set("ip", vps_ip)
        self._cfg.set("port", int(vps_port) if vps_port.isdigit() else 22)
        self._cfg.set("user", vps_user)
        self._cfg.set("key_path", ssh_key)
        
        # Background AI (EAII)
        self._cfg.set("eaii_enabled", eaii_enabled)
        self._cfg.set("sync_interval_ms", interval)
        self._cfg.set("eaii_interval_min", eaii_interval)
        self._cfg.set("language", lang)
        L.set_language(lang) # Update localization engine
        self._cfg.set("eaii_provider", eaii_provider)
        self._cfg.set("eaii_model", eaii_model)
        self._cfg.set("eaii_base_url", eaii_url)
        self._cfg.set("eaii_base_url", eaii_url)
        self._cfg.secrets["eaii_key"] = eaii_key
        self._cfg.settings["eaii_key"] = eaii_key
        
        # Interactive AI
        self._cfg.set("ai_provider", ai_provider)
        self._cfg.set("ai_model", ai_model)
        self._cfg.set("ai_base_url", ai_url)
        self._cfg.secrets["ai_key"] = ai_key
        self._cfg.settings["ai_key"] = ai_key
        
        # EAIS (Entropy AI Sandbox)
        self._cfg.set("eais_enabled", eais_enabled)
        
        self._cfg.save()
        self.settingsChanged.emit()
    
    @Property(float, notify=riskChanged)
    def riskScore(self): return self._risk_score
    
    @Property(str, notify=riskChanged)
    def riskLabel(self): return self._risk_label
    
    @Property(str, notify=riskChanged)
    def riskColor(self): return self._risk_color
