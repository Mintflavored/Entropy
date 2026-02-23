import os
import json
import pytest
from unittest.mock import patch
from core.config import ConfigManager

@patch('core.config._HAS_DOTENV', False)
@patch.dict(os.environ, {}, clear=True)
def test_config_default_values(tmp_path):
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    assert cfg.get("language") == "ru"
    assert cfg.get("port") == 22
    assert cfg.ai_key == ""

def test_config_save_load(tmp_path):
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    cfg.set("user", "test_user")
    cfg.save()
    
    # Новый экземпляр должен загрузить сохраненные данные
    cfg2 = ConfigManager(str(config_file))
    assert cfg2.get("user") == "test_user"

@patch('core.config._HAS_DOTENV', False)
def test_config_type_casting(tmp_path):
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    # Пытаемся передать строку вместо числа - должно успешно скастоваться
    cfg.set("port", "2222")
    assert cfg.get("port") == 2222
    
    # Передаем невалидную строку - должно откатываться к 22
    cfg.set("port", "not_a_number")
    assert cfg.get("port") == 22
    
    # Аналогично для sync_interval_ms
    cfg.set("sync_interval_ms", "invalid")
    assert cfg.get("sync_interval_ms") == 10000

@patch('core.config._HAS_DOTENV', False)
@patch.dict(os.environ, {"GLM_API_KEY": "env_key", "EAII_API_KEY": "eaii_key", "VPN_SSH_KEY_PATH": "/env/key.pem"})
def test_config_dotenv_loading(tmp_path):
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    assert cfg.secrets["ai_key"] == "env_key"
    assert cfg.secrets["eaii_key"] == "eaii_key"
    assert cfg.secrets["ssh_key_path"] == "/env/key.pem"
    
    # Фолбек SSH ключа: раз он есть в .env и не задан в дефолтном config, должен проставиться в настройки
    assert cfg.get("key_path") == "/env/key.pem"

@patch('core.config._HAS_DOTENV', False)
@patch.dict(os.environ, {"GLM_API_KEY": "env_key"})
def test_config_priority_over_dotenv(tmp_path):
    config_file = tmp_path / "test_config.json"
    
    # Создаем конфиг с приоритетным ai_key
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"ai_key": "config_json_key"}, f)
        
    cfg = ConfigManager(str(config_file))
    
    # Значение из config.json должно перезаписать значение из .env
    assert cfg.secrets["ai_key"] == "config_json_key"

def test_config_corrupted_json(tmp_path, capsys):
    config_file = tmp_path / "test_config.json"
    
    # Записываем невалидный JSON
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("{invalid_json: 123")
        
    # Менеджер должен перехватить Exception, вывести ошибку и загрузиться с дефолтами
    cfg = ConfigManager(str(config_file))
    
    assert cfg.get("port") == 22
    captured = capsys.readouterr()
    assert "Ошибка загрузки" in captured.out
