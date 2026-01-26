import os
import json
import pytest
from core.config import ConfigManager

def test_config_default_values(tmp_path):
    # Указываем временный путь для конфига
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    assert cfg.get("language") == "ru"
    assert cfg.get("port") == 22

def test_config_save_load(tmp_path):
    config_file = tmp_path / "test_config.json"
    cfg = ConfigManager(str(config_file))
    
    cfg.set("user", "test_user")
    cfg.save()
    
    # Новый экземпляр должен загрузить сохраненные данные
    cfg2 = ConfigManager(str(config_file))
    assert cfg2.get("user") == "test_user"
