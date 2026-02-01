import pytest
from core.localization import LocalizationManager

# Используем глобальный singleton вместо создания новых экземпляров
# Это корректно для PySide6 QObject-based классов

@pytest.fixture
def localization():
    """Возвращает существующий singleton LocalizationManager."""
    # Сбрасываем singleton для чистого теста
    LocalizationManager._instance = None
    return LocalizationManager()

def test_localization_switching(localization):
    L = localization
    
    L.set_language("en")
    assert L.current_lang == "en"
    assert L.tr("nav_dashboard") == "Dashboard"
    
    L.set_language("ru")
    assert L.current_lang == "ru"
    assert L.tr("nav_dashboard") == "Дашборд"

def test_localization_missing_key(localization):
    L = localization
    assert L.tr("non_existent_key") == "non_existent_key"
