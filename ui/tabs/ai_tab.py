from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QFrame, QHBoxLayout, QLabel, QSpinBox

class AITab(QWidget):
    """Вкладка ИИ-аналитики с управлением лимитами."""
    def __init__(self, run_ai_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Нажми 'Анализировать', чтобы получить глубокую расшифровка состояния сервера...")
        layout.addWidget(self.output)
        
        self.btn = QPushButton("🧠 СГЕНЕРИРОВАТЬ AI-ОТЧЕТ (С УЧЕТОМ КОНФИГА)")
        self.btn.clicked.connect(run_ai_callback)
        layout.addWidget(self.btn)
        
        # Настройки ИИ снизу
        bot_ctrl = QFrame()
        bot_ctrl.setStyleSheet("background: #1c2128; border-top: 1px solid #30363d; padding: 5px;")
        bot_layout = QHBoxLayout(bot_ctrl)
        
        bot_layout.addWidget(QLabel("Лимит SSH-запросов диагностике:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 20)
        self.limit_spin.setValue(5)
        self.limit_spin.setStyleSheet("background: #0d1117; color: #58a6ff; font-weight: bold;")
        bot_layout.addWidget(self.limit_spin)
        bot_layout.addStretch()
        
        layout.addWidget(bot_ctrl)

    def set_loading(self, is_loading):
        self.btn.setEnabled(not is_loading)
        if is_loading:
            self.output.append("\n--- ЗАПУСК ИИ-АНАЛИЗА (DEEP CONTEXT)... ---")

    def show_result(self, text):
        self.output.setText(text)

    def show_error(self, error):
        self.output.append(f"\n[ОШИБКА]: {error}")
