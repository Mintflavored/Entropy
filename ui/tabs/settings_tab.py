from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QFrame, QComboBox
from core.localization import L

class SettingsTab(QWidget):
    """Вкладка управления основными настройками и соединением."""
    def __init__(self, config_manager, save_callback):
        super().__init__()
        self.cfg = config_manager
        layout = QVBoxLayout(self)
        
        self.lbl_conn_title = QLabel()
        layout.addWidget(self.lbl_conn_title)
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
        
        self.lbl_ip = QLabel(); self.lbl_port = QLabel(); self.lbl_user = QLabel(); self.lbl_key = QLabel()
        
        form.addRow(self.lbl_ip, self.ip_field)
        form.addRow(self.lbl_port, self.port_field)
        form.addRow(self.lbl_user, self.user_field)
        form.addRow(self.lbl_key, self.key_field)
        layout.addWidget(form_group)
        
        # --- AI Configuration ---
        self.lbl_ai_title = QLabel()
        layout.addWidget(self.lbl_ai_title)
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
        
        # Language Selector
        self.lang_box = QComboBox()
        self.lang_box.addItems(["ru", "en"])
        self.lang_box.setCurrentText(self.cfg.get("language", "ru"))
        
        self.lbl_prov = QLabel(); self.lbl_akey = QLabel(); self.lbl_mod = QLabel(); self.lbl_url = QLabel(); self.lbl_lang = QLabel()
        
        ai_form.addRow(self.lbl_prov, self.ai_prov_box)
        ai_form.addRow(self.lbl_akey, self.ai_key_field)
        ai_form.addRow(self.lbl_mod, self.ai_model_field)
        ai_form.addRow(self.lbl_url, self.ai_url_field)
        ai_form.addRow(self.lbl_lang, self.lang_box)
        
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.on_save)
        self.save_callback = save_callback
        
        layout.addWidget(ai_group)
        layout.addWidget(self.save_btn)
        layout.addStretch()
        
        self.retranslate_ui()

    def retranslate_ui(self):
        self.lbl_conn_title.setText("⚙️ CONNECTION " + L.tr("tab_settings"))
        self.lbl_ip.setText(L.tr("lbl_server_ip"))
        self.lbl_port.setText(L.tr("lbl_ssh_port"))
        self.lbl_user.setText(L.tr("lbl_ssh_user"))
        self.lbl_key.setText(L.tr("lbl_ssh_key"))
        
        self.lbl_ai_title.setText("🤖 AI " + L.tr("tab_settings"))
        self.lbl_prov.setText(L.tr("lbl_ai_provider"))
        self.lbl_akey.setText("API Key:")
        self.lbl_mod.setText(L.tr("lbl_ai_model"))
        self.lbl_url.setText("Base URL:")
        self.lbl_lang.setText(L.tr("lbl_language"))
        self.save_btn.setText("💾 " + L.tr("btn_save"))

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
        self.cfg.set("ai_key", self.ai_key_field.text()) 
        
        # Language
        self.cfg.set("language", self.lang_box.currentText())
        
        self.cfg.save()
        self.cfg.load()
        self.save_callback()
