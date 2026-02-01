import json
import os

# python-dotenv is optional (may not be bundled in PyInstaller)
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

class ConfigManager:
    """Управляет загрузкой и сохранением настроек приложения."""
    
    DEFAULT_CONFIG_PATH = "config.json"
    
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.secrets = {}
        self.settings = {
            "ip": "127.0.0.1",
            "port": 22,
            "user": "root",
            "key_path": "path/to/key",
            "remote_db": "/home/user/monitor.db",
            "local_db": "local_stats.db",
            "sync_interval_ms": 10000,
            "ai_provider": "openai_compatible",
            "ai_model": "gpt-4o",
            "ai_base_url": "https://api.openai.com/v1",
            "ai_tool_limit": 5,
            "language": "ru",
            "eaii_enabled": False,
            "eaii_provider": "openai_compatible",
            "eaii_model": "gpt-4o-mini",
            "eaii_base_url": "https://api.openai.com/v1",
            "eaii_interval_min": 5
        }
        self.load()

    def load(self):
        """Загружает секреты из .env и настройки из config.json."""
        if _HAS_DOTENV:
            load_dotenv()
        self.secrets = {
            "ai_key": os.getenv("GLM_API_KEY", ""),
            "eaii_key": os.getenv("EAII_API_KEY", ""),
            "ssh_key_path": os.getenv("VPN_SSH_KEY_PATH", "")
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                    # Если в конфиге есть ключ, он приоритетнее .env
                    if "ai_key" in saved_settings:
                        self.secrets["ai_key"] = saved_settings["ai_key"]
            except Exception as e:
                print(f"Ошибка загрузки config.json: {e}")
        
        # Переопределяем путь к ключу, если он есть в .env и не задан в конфиге
        if self.secrets["ssh_key_path"] and not self.settings.get("key_path"):
            self.settings["key_path"] = self.secrets["ssh_key_path"]

    def save(self):
        """Сохраняет текущие настройки в config.json."""
        try:
            # Создаем копию для сохранения, чтобы не повредить живые данные
            data_to_save = self.settings.copy()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Конфигурация успешно сохранена в {self.config_path}")
        except Exception as e:
            print(f"Ошибка сохранения config.json: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        # Принудительное приведение типов для критических полей
        if key == "port":
            try:
                value = int(value)
            except:
                value = 22
        if key == "sync_interval_ms":
            try:
                value = int(value)
            except:
                value = 10000
        self.settings[key] = value

    @property
    def ai_key(self):
        return self.secrets.get("ai_key", "")
