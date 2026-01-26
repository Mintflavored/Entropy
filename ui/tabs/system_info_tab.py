from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QFrame, QPushButton

class SystemInfoTab(QWidget):
    """Вкладка характеристик сервера и специфики VPN."""
    def __init__(self, config_manager, save_callback):
        super().__init__()
        self.cfg = config_manager
        layout = QVBoxLayout(self)
        
        info_group = QFrame()
        info_group.setStyleSheet("background: #161a11; border-radius: 5px; padding: 10px;")
        form = QFormLayout(info_group)
        
        self.field_vps = QLineEdit(); self.field_vps.setPlaceholderText("Напр. Hetzner, Финляндия")
        self.field_cpu = QLineEdit(); self.field_ram = QLineEdit(); self.field_os = QLineEdit()
        self.field_vpn = QLineEdit(); self.field_vpn.setPlaceholderText("Напр. Marzban, VLESS+Reality")
        
        # Предзаполнение из конфига (если сохранено)
        self.field_vps.setText(self.cfg.get("vps_info", ""))
        self.field_vpn.setText(self.cfg.get("vpn_config", ""))
        
        form.addRow(QLabel("VPS Провайдер/Локация:"), self.field_vps)
        form.addRow(QLabel("Модель CPU (Auto):"), self.field_cpu)
        form.addRow(QLabel("Всего RAM (Auto):"), self.field_ram)
        form.addRow(QLabel("ОС Сервера (Auto):"), self.field_os)
        form.addRow(QLabel("Конфиг VPN / Панель:"), self.field_vpn)
        
        self.save_btn = QPushButton("📥 СОХРАНИТЬ ХАРАКТЕРИСТИКИ В КОНФИГ")
        self.save_btn.clicked.connect(self.on_save)
        self.save_callback = save_callback
        
        layout.addWidget(QLabel("📂 ХАРАКТЕРИСТИКИ (Контекст для ИИ):"))
        layout.addWidget(info_group)
        layout.addWidget(self.save_btn)
        
        self.auto_info_label = QLabel("Детектированные панели: Ожидание данных...")
        layout.addWidget(self.auto_info_label)
        layout.addStretch()

    def update_auto_data(self, discovery):
        self.field_cpu.setText(discovery.get('cpu_model', ''))
        self.field_ram.setText(discovery.get('ram_total', ''))
        self.field_os.setText(discovery.get('os_version', ''))
        self.auto_info_label.setText(f"Детектированные панели: {discovery.get('detected_panels', 'N/A')}")

    def on_save(self):
        self.cfg.set("vps_info", self.field_vps.text())
        self.cfg.set("vpn_config", self.field_vpn.text())
        self.cfg.save()
        if self.save_callback: self.save_callback()

    def get_full_context(self, detected_panels):
        return {
            'vps_info': self.field_vps.text(),
            'cpu_model': self.field_cpu.text(),
            'ram_total': self.field_ram.text(),
            'os_version': self.field_os.text(),
            'vpn_config': self.field_vpn.text(),
            'detected_panels': detected_panels
        }
