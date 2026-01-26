from PyQt6.QtCore import QObject, pyqtSignal

class LocalizationManager(QObject):
    """
    Manages application-wide translations and language switching.
    Implemented as a singleton to be accessible from any UI component.
    """
    language_changed = pyqtSignal(str)
    _instance = None

    STRINGS = {
        "ru": {
            # main_window
            "window_title": "Entropy v0.31.0 - Продвинутая VPN Аналитика",
            "status_init": "🚀 Инициализация...",
            "status_sync": "Синхронизация...",
            "status_error": "ОШИБКА: {}",
            "status_updated": "Обновлено в {}",
            "status_settings_saved": "Настройки сохранены. Переподключение...",
            "risk_label": "РИСК: {}",
            "risk_unknown": "UNKNOWN",
            
            # tabs
            "tab_dashboard": "Дашборд",
            "tab_security": "Безопасность",
            "tab_ai": "AI Анализ",
            "tab_info": "Инфо",
            "tab_settings": "Настройки",
            
            # dashboard_tab
            "chart_cpu": "Загрузка CPU (%)",
            "chart_ram": "Загрузка RAM (%)",
            "chart_pps": "Сетевые пакеты (PPS)",
            "chart_jitter": "Джиттер (ms)",
            "table_user": "Пользователь",
            "table_ip": "IP-адрес",
            "table_traffic": "Трафик",
            
            # security_tab
            "sec_title": "Анализ сетевой активности",
            "sec_probing": "Подозрительная активность (Brute Force)",
            "table_time": "Время",
            "table_event": "Событие",
            
            # ai_tab
            "ai_btn_analyze": "Запустить AI Диагностику",
            "ai_placeholder": "Нажмите кнопку для анализа состояния сервера...",
            "ai_loading": "ИИ анализирует данные...",
            
            # settings_tab
            "settings_title": "Настройки подключения и AI",
            "btn_save": "Сохранить настройки",
            "lbl_server_ip": "IP Сервера:",
            "lbl_ssh_port": "SSH Порт:",
            "lbl_ssh_user": "SSH Пользователь:",
            "lbl_ssh_key": "Путь к SSH ключу:",
            "lbl_ai_provider": "AI Провайдер:",
            "lbl_ai_model": "Модель:",
            "lbl_ai_limit": "Лимит запросов ИИ:",
            "lbl_language": "Язык Интерфейса:",
            
            # system_info_tab
            "info_title": "Характеристики сервера",
            "lbl_os": "Операционная система:",
            "lbl_cpu_cores": "Ядра CPU:",
            "lbl_panels": "Обнаруженные панели:",
            "lbl_uptime": "Аптайм:"
        },
        "en": {
            # main_window
            "window_title": "Entropy v0.31.0 - Advanced VPN Analytics",
            "status_init": "🚀 Initializing...",
            "status_sync": "Synchronizing...",
            "status_error": "ERROR: {}",
            "status_updated": "Updated at {}",
            "status_settings_saved": "Settings saved. Reconnecting...",
            "risk_label": "RISK: {}",
            "risk_unknown": "UNKNOWN",
            
            # tabs
            "tab_dashboard": "Dashboard",
            "tab_security": "Security",
            "tab_ai": "AI Insights",
            "tab_info": "System Info",
            "tab_settings": "Settings",
            
            # dashboard_tab
            "chart_cpu": "CPU Load (%)",
            "chart_ram": "RAM Load (%)",
            "chart_pps": "Network Packets (PPS)",
            "chart_jitter": "Jitter (ms)",
            "table_user": "User",
            "table_ip": "IP Address",
            "table_traffic": "Traffic",
            
            # security_tab
            "sec_title": "Network Activity Analysis",
            "sec_probing": "Suspicious Activity (Brute Force)",
            "table_time": "Time",
            "table_event": "Event",
            
            # ai_tab
            "ai_btn_analyze": "Run AI Diagnostics",
            "ai_placeholder": "Click the button to analyze server state...",
            "ai_loading": "AI is analyzing data...",
            
            # settings_tab
            "settings_title": "Connection & AI Settings",
            "btn_save": "Save Settings",
            "lbl_server_ip": "Server IP:",
            "lbl_ssh_port": "SSH Port:",
            "lbl_ssh_user": "SSH User:",
            "lbl_ssh_key": "SSH Key Path:",
            "lbl_ai_provider": "AI Provider:",
            "lbl_ai_model": "Model:",
            "lbl_ai_limit": "AI Request Limit:",
            "lbl_language": "Interface Language:",
            
            # system_info_tab
            "info_title": "Server Specifications",
            "lbl_os": "Operating System:",
            "lbl_cpu_cores": "CPU Cores:",
            "lbl_panels": "Detected Panels:",
            "lbl_uptime": "Uptime:"
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

    def tr(self, key):
        """Translate a key to the current language."""
        return self.STRINGS.get(self.current_lang, {}).get(key, key)

# Access helper
L = LocalizationManager()
