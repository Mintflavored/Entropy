import pytest
from core.localization import LocalizationManager

def test_localization_switching():
    L = LocalizationManager()
    
    L.set_language("en")
    assert L.current_lang == "en"
    assert L.tr("tab_dashboard") == "Dashboard"
    
    L.set_language("ru")
    assert L.current_lang == "ru"
    assert L.tr("tab_dashboard") == "Дашборд"

def test_localization_missing_key():
    L = LocalizationManager()
    assert L.tr("non_existent_key") == "non_existent_key"
