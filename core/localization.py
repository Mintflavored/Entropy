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
            "nav_sandbox": "AI Песочница",
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
            "lbl_enable_eais": "Включить EAIS",
            "lbl_eais_desc": "Entropy AI Sandbox — автооптимизация VPN конфигурации",
            "lbl_ai_provider": "AI Провайдер",
            "lbl_model_name": "Название модели",
            "lbl_base_url": "Базовый URL (API)",
            "lbl_api_key": "API Ключ",
            "lbl_enable_ai": "Включить AI Движок",
            "lbl_ai_desc": "Глубокий анализ трафика и проактивная защита",
            "lbl_eaii_interval": "Интервал проверки EAII",
            "lbl_minutes": "мин",
            "sec_vps_connection": "Подключение к VPS",
            "lbl_vps_ip": "IP адрес сервера",
            "lbl_vps_port": "SSH Порт",
            "lbl_vps_user": "Пользователь",
            "lbl_ssh_key_path": "Путь к SSH ключу",
            "btn_apply_all": "Применить все настройки",
            
            # Risks & Statuses
            "risk_low": "НИЗКИЙ",
            "risk_medium": "СРЕДНИЙ",
            "risk_high": "ВЫСОКИЙ",
            "risk_critical": "КРИТИЧЕСКИЙ",
            "status_init": "Инициализация...",
            "status_sync": "Синхронизация...",

            # Sandbox / EAIS
            "title_sandbox_view": "🧪 AI Sandbox",
            "eais_status_loading": "Загрузка...",
            "eais_desc": "AI автоматически тестирует различные настройки VPN в изолированной среде и находит оптимальную конфигурацию",
            "eais_progress": "Прогресс экспериментов",
            "btn_stop": "⏹ Остановить",
            "btn_start_opt": "▶ Запустить оптимизацию",
            "title_best_result": "🏆 Лучший результат",
            "lbl_baseline": "Baseline",
            "lbl_optimized": "Оптимизировано",
            "lbl_rec_config": "Рекомендуемая конфигурация:",
            "btn_apply_prod": "Применить к Production",
            "title_how_it_works": "ℹ️ Как это работает",
            "desc_how_it_works": "1. AI создаёт изолированную копию VPN (sandbox)\n2. Тестирует различные параметры (MTU, buffer, congestion)\n3. Генерирует реальный трафик и измеряет метрики\n4. Находит оптимальную конфигурацию\n5. Предлагает применить к production (с вашего подтверждения)",
            "dialog_apply_title": "Применить конфигурацию?",
            "dialog_apply_desc": "Вы уверены что хотите применить найденную\nконфигурацию к production VPN?\n\nЭто изменит настройки сервера.",
            "sb_stat_ready": "Готово к запуску",
            "sb_err_off": "EAIS отключён. Включите в Настройках → Интерактивный AI Аналитик",
            "sb_stat_off": "EAIS отключён",
            "sb_err_ssh": "SSH не подключён",
            "sb_err_key": "API ключ не настроен",
            "sb_stat_init": "Инициализация EAIS...",
            "sb_stat_stopped": "Остановлено пользователем",
            "sb_err_no_res": "Нет результатов для применения",
            "sb_stat_ready_apply": "Конфигурация готова к применению",
            "sb_stat_err": "Ошибка",
            "sb_err_no_opt": "Оптимизация завершилась без результата",
            "sb_stat_done": "Готово! Улучшение: {imp:.1f}%"
        },
        "en": {
            # Navigation
            "nav_dashboard": "Dashboard",
            "nav_security": "Security",
            "nav_ai": "AI Insights",
            "nav_sandbox": "AI Sandbox",
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
            "lbl_enable_eais": "Enable EAIS",
            "lbl_eais_desc": "Entropy AI Sandbox — auto-optimize VPN configuration",
            "lbl_ai_provider": "AI Provider",
            "lbl_model_name": "Model Name",
            "lbl_base_url": "Base URL",
            "lbl_api_key": "API Key",
            "lbl_enable_ai": "Enable AI Engine",
            "lbl_ai_desc": "Deep traffic analysis and proactive defense",
            "lbl_eaii_interval": "EAII Check Interval",
            "lbl_minutes": "min",
            "sec_vps_connection": "VPS Connection",
            "lbl_vps_ip": "Server IP Address",
            "lbl_vps_port": "SSH Port",
            "lbl_vps_user": "Username",
            "lbl_ssh_key_path": "SSH Key Path",
            "btn_apply_all": "Apply & Persist All Settings",

            # Risks & Statuses
            "risk_low": "LOW",
            "risk_medium": "MEDIUM",
            "risk_high": "HIGH",
            "risk_critical": "CRITICAL",
            "status_init": "Initializing...",
            "status_sync": "Synchronizing...",

            # Sandbox / EAIS
            "title_sandbox_view": "🧪 AI Sandbox",
            "eais_status_loading": "Loading...",
            "eais_desc": "AI automatically tests various VPN settings in an isolated environment to find the optimal configuration",
            "eais_progress": "Experiment Progress",
            "btn_stop": "⏹ Stop",
            "btn_start_opt": "▶ Start Optimization",
            "title_best_result": "🏆 Best Result",
            "lbl_baseline": "Baseline",
            "lbl_optimized": "Optimized",
            "lbl_rec_config": "Recommended Configuration:",
            "btn_apply_prod": "Apply to Production",
            "title_how_it_works": "ℹ️ How it works",
            "desc_how_it_works": "1. AI creates an isolated VPN copy (sandbox)\n2. Tests various parameters (MTU, buffer, congestion)\n3. Generates real traffic and metrics\n4. Finds the optimal configuration\n5. Suggests applying to production (upon confirmation)",
            "dialog_apply_title": "Apply configuration?",
            "dialog_apply_desc": "Are you sure you want to apply the found\nconfiguration to the production VPN?\n\nThis will change server settings.",
            "sb_stat_ready": "Ready to start",
            "sb_err_off": "EAIS is disabled. Enable it in Settings → Interactive AI Analyzer",
            "sb_stat_off": "EAIS disabled",
            "sb_err_ssh": "SSH is not connected",
            "sb_err_key": "API key is not configured",
            "sb_stat_init": "Initializing EAIS...",
            "sb_stat_stopped": "Stopped by user",
            "sb_err_no_res": "No results to apply",
            "sb_stat_ready_apply": "Configuration is ready to be applied",
            "sb_stat_err": "Error",
            "sb_err_no_opt": "Optimization finished without a result",
            "sb_stat_done": "Done! Improvement: {imp:.1f}%"
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
