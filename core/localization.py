from PySide6.QtCore import QObject, Signal

class LocalizationManager(QObject):
    """
    Manages application-wide translations and language switching.
    Exposes a dictionary of strings to QML via MainViewModel.
    """
    language_changed = Signal(str)
    _instance = None

    STRINGS = {
        "ru": {
            # Navigation
            "nav_dashboard": "Дашборд",
            "nav_security": "Безопасность",
            "nav_ai": "AI Анализ",
            "nav_settings": "Настройки",

            # Dashboard
            "title_dashboard": "Обзор сервера",
            "lbl_cpu": "ЗАГРУЗКА CPU",
            "lbl_ram": "ПАМЯТЬ RAM",
            "lbl_pps": "СЕТЬ PPS",
            "lbl_risk": "AI РИСК",
            "chart_cpu_history": "История загрузки CPU",
            "chart_ram_history": "История использования RAM",
            "chart_pps_history": "Сетевой трафик (PPS)",
            "chart_jitter_history": "Сетевой джиттер (мс)",
            "lbl_users": "Подключенные пользователи",
            "tbl_user_id": "ID ПОЛЬЗОВАТЕЛЯ",
            "tbl_ip_address": "IP АДРЕС",
            "tbl_traffic_total": "ВСЕГО ТРАФИКА",
            
            # Dashboard subtitles
            "sub_current_load": "текущая нагрузка",
            "sub_current_usage": "текущее использование",
            "sub_packets_sec": "пакетов/сек",
            "sub_eaii_score": "индекс EAII",
            "lbl_time_60s": "← 60 сек",

            # Security
            "title_security": "Аналитика Безопасности",
            "lbl_entropy_index": "ИНДЕКС ЭНТРОПИИ",
            "lbl_threat_level": "Текущий уровень угрозы серверной среды",
            "title_invasion_logic": "Логика вторжений в реальном времени",
            "log_bruteforce": "⚠️ Обнаружен брутфорс: ",
            "lbl_attempts": "попыток",
            "log_clean": "Подозрительная активность не обнаружена. Сервер в безопасности.",

            # AI View
            "title_ai_intelligence": "Entropy AI Интеллект",
            "sec_eaii_status": "Фоновый Мониторинг Рисков (EAII)",
            "sec_deep_diagnostic": "Глубокий Диагностический Отчет",
            "ai_status_analyzing": "ИИ анализирует трафик сервера...",
            "ai_status_idle": "EAII: Система в норме",
            "ai_interactive_idle": "Готов к глубокой диагностике...",
            "ai_interactive_analyzing": "ИИ выполняет SSH-команды и анализирует логи...",
            "btn_ai_scan": "Запустить Глубокую Диагностику",

            # Settings
            "title_settings": "Настройки приложения",
            "sec_general": "Общие настройки",
            "lbl_lang_selection": "Язык интерфейса",
            "lbl_sync_interval": "Интервал синхронизации",
            "sec_interactive_ai": "Интерактивный AI Аналитик",
            "sec_background_ai": "Фоновый AI Анализ (EAII)",
            "lbl_ai_provider": "AI Провайдер",
            "lbl_model_name": "Название модели",
            "lbl_base_url": "Базовый URL (API)",
            "lbl_api_key": "API Ключ",
            "lbl_enable_ai": "Включить AI Движок",
            "lbl_ai_desc": "Глубокий анализ трафика и проактивная защита",
            "lbl_eaii_interval": "Интервал проверки EAII",
            "lbl_minutes": "мин",
            "btn_apply_all": "Применить все настройки",
            
            # Risks & Statuses
            "risk_low": "НИЗКИЙ",
            "risk_medium": "СРЕДНИЙ",
            "risk_high": "ВЫСОКИЙ",
            "risk_critical": "КРИТИЧЕСКИЙ",
            "status_init": "Инициализация...",
            "status_sync": "Синхронизация..."
        },
        "en": {
            # Navigation
            "nav_dashboard": "Dashboard",
            "nav_security": "Security",
            "nav_ai": "AI Insights",
            "nav_settings": "Settings",

            # Dashboard
            "title_dashboard": "Server Overview",
            "lbl_cpu": "CPU LOAD",
            "lbl_ram": "RAM USAGE",
            "lbl_pps": "NETWORK PPS",
            "lbl_risk": "AI RISK SCORE",
            "chart_cpu_history": "CPU Load History",
            "chart_ram_history": "RAM Usage History",
            "chart_pps_history": "Network Traffic (PPS)",
            "chart_jitter_history": "Network Jitter (ms)",
            "lbl_users": "Connected Users",
            "tbl_user_id": "USER ID",
            "tbl_ip_address": "IP ADDRESS",
            "tbl_traffic_total": "TRAFFIC TOTAL",
            
            # Dashboard subtitles
            "sub_current_load": "current load",
            "sub_current_usage": "current usage",
            "sub_packets_sec": "packets/sec",
            "sub_eaii_score": "EAII score",
            "lbl_time_60s": "← 60s",

            # Security
            "title_security": "Security Intelligence",
            "lbl_entropy_index": "ENTROPY INDEX",
            "lbl_threat_level": "Current server environment threat level",
            "title_invasion_logic": "Real-time Invasion Logic",
            "log_bruteforce": "⚠️ Brute-force detected: ",
            "lbl_attempts": "attempts",
            "log_clean": "No hostile activity detected recently. Server is clean.",

            # AI View
            "title_ai_intelligence": "Entropy AI Intelligence",
            "sec_eaii_status": "Background Risk Monitoring (EAII)",
            "sec_deep_diagnostic": "Deep Diagnostic Report",
            "ai_status_analyzing": "AI is currently analyzing server traffic...",
            "ai_status_idle": "EAII: System is healthy",
            "ai_interactive_idle": "Ready for deep diagnostic...",
            "ai_interactive_analyzing": "AI is executing SSH commands and analyzing logs...",
            "btn_ai_scan": "Trigger Deep Analysis",

            # Settings
            "title_settings": "Application Settings",
            "sec_general": "General",
            "lbl_lang_selection": "Language / Язык",
            "lbl_sync_interval": "Sync Interval",
            "sec_interactive_ai": "Interactive AI Analyzer",
            "sec_background_ai": "Background AI Analyzer (EAII)",
            "lbl_ai_provider": "AI Provider",
            "lbl_model_name": "Model Name",
            "lbl_base_url": "Base URL",
            "lbl_api_key": "API Key",
            "lbl_enable_ai": "Enable AI Engine",
            "lbl_ai_desc": "Deep traffic analysis and proactive defense",
            "lbl_eaii_interval": "EAII Check Interval",
            "lbl_minutes": "min",
            "btn_apply_all": "Apply & Persist All Settings",

            # Risks & Statuses
            "risk_low": "LOW",
            "risk_medium": "MEDIUM",
            "risk_high": "HIGH",
            "risk_critical": "CRITICAL",
            "status_init": "Initializing...",
            "status_sync": "Synchronizing..."
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalizationManager, cls).__new__(cls)
            cls._instance.current_lang = "ru"
        return cls._instance

    def set_language(self, lang):
        if lang in self.STRINGS and lang != self.current_lang:
            self.current_lang = lang
            self.language_changed.emit(lang)

    def get_all(self):
        """Returns all strings for the current language."""
        return self.STRINGS.get(self.current_lang, self.STRINGS["ru"])

    def tr(self, key):
        """Translate a key to the current language."""
        return self.get_all().get(key, key)

# Access helper
L = LocalizationManager()
