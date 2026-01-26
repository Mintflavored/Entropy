from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QFrame, QComboBox

class SettingsTab(QWidget):
    """Вкладка управления основными настройками и соединением."""
    def __init__(self, config_manager, save_callback):
        super().__init__()
        self.cfg = config_manager
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("⚙️ НАСТРОЙКИ СОЕДИНЕНИЯ:"))
        form_group = QFrame()
        form_group.setStyleSheet("background: #161a21; border-radius: 5px; padding: 10px;")
        form = QFormLayout(form_group)
        
        self.ip_field = QLineEdit(self.cfg.get("ip"))
        self.ip_field.setPlaceholderText("e.g. 1.2.3.4")
        self.port_field = QLineEdit(str(self.cfg.get("port")))
        self.port_field.setPlaceholderText("22")
        self.user_field = QLineEdit(self.cfg.get("user"))
        self.user_field.setPlaceholderText("root")
        self.key_field = QLineEdit(self.cfg.get("key_path"))
        self.key_field.setPlaceholderText("C:/path/to/private_key")
        
        form.addRow(QLabel("Server IP:"), self.ip_field)
        form.addRow(QLabel("SSH Port:"), self.port_field)
        form.addRow(QLabel("SSH User:"), self.user_field)
        form.addRow(QLabel("SSH Key Path:"), self.key_field)
        layout.addWidget(form_group)
        # --- AI Configuration ---
        layout.addWidget(QLabel("🤖 НАСТРОЙКИ ИИ:"))
        ai_group = QFrame()
        ai_group.setStyleSheet("background: #161a21; border-radius: 5px; padding: 10px;")
        ai_form = QFormLayout(ai_group)
        
        self.ai_prov_box = QComboBox()
        self.ai_prov_box.addItems(["openai_compatible", "openai", "claude", "gemini"])
        self.ai_prov_box.setCurrentText(self.cfg.get("ai_provider", "openai_compatible"))
        
        self.ai_key_field = QLineEdit(self.cfg.ai_key)
        self.ai_key_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key_field.setPlaceholderText("sk-...")
        
        self.ai_model_field = QLineEdit(self.cfg.get("ai_model", "gpt-4o"))
        self.ai_model_field.setPlaceholderText("gpt-4o")
        self.ai_url_field = QLineEdit(self.cfg.get("ai_base_url", "https://api.openai.com/v1"))
        self.ai_url_field.setPlaceholderText("https://api.openai.com/v1")
        
        ai_form.addRow(QLabel("Provider:"), self.ai_prov_box)
        ai_form.addRow(QLabel("API Key:"), self.ai_key_field)
        ai_form.addRow(QLabel("Model Name:"), self.ai_model_field)
        ai_form.addRow(QLabel("Base URL (API):"), self.ai_url_field)
        
        self.save_btn = QPushButton("💾 СОХРАНИТЬ ВСЕ НАСТРОЙКИ И ПЕРЕПОДКЛЮЧИТЬСЯ")
        self.save_btn.clicked.connect(self.on_save)
        self.save_callback = save_callback
        
        layout.addWidget(ai_group)
        layout.addWidget(self.save_btn)
        layout.addStretch()

    def on_save(self):
        # Connection
        self.cfg.set("ip", self.ip_field.text())
        self.cfg.set("port", int(self.port_field.text()))
        self.cfg.set("user", self.user_field.text())
        self.cfg.set("key_path", self.key_field.text())
        
        # AI
        self.cfg.set("ai_provider", self.ai_prov_box.currentText())
        self.cfg.set("ai_model", self.ai_model_field.text())
        self.cfg.set("ai_base_url", self.ai_url_field.text())
        self.cfg.set("ai_key", self.ai_key_field.text()) # Сохраняем ключ в конфиг
        
        self.cfg.save()
        self.cfg.load() # Перезагружаем секреты
        self.save_callback()
