import sys
import logging
from PyQt6.QtWidgets import QApplication
from core.config import ConfigManager
from ui.main_window import MainWindow

def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("vpn_monitor.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    app = QApplication(sys.argv)
    
    # Загрузка конфигурации
    cfg = ConfigManager()
    
    # Запуск окна
    window = MainWindow(cfg)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
