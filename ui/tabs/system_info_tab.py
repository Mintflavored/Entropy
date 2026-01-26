from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QFrame, QPushButton
from core.localization import L

class SystemInfoTab(QWidget):
    """Вкладка характеристик сервера и специфики VPN."""
    def __init__(self, config_manager, save_callback):
        super().__init__()
        self.cfg = config_manager
        layout = QVBoxLayout(self)
        
        info_group = QFrame()
        info_group.setStyleSheet("background: #161a11; border-radius: 5px; padding: 10px;")
        form = QFormLayout(info_group)
        
        self.field_vps = QLineEdit(); self.field_vps.setPlaceholderText("e.g. Hetzner, Finland")
        self.field_cpu = QLineEdit(); self.field_ram = QLineEdit(); self.field_os = QLineEdit()
        self.field_vpn = QLineEdit(); self.field_vpn.setPlaceholderText("e.g. Marzban, VLESS+Reality")
        
        # Предзаполнение из конфига (если сохранено)
        self.field_vps.setText(self.cfg.get("vps_info", ""))
        self.field_vpn.setText(self.cfg.get("vpn_config", ""))
        
        self.lbl_vps = QLabel(); self.lbl_cpu = QLabel(); self.lbl_ram = QLabel(); self.lbl_os = QLabel(); self.lbl_vpn = QLabel()
        
        form.addRow(self.lbl_vps, self.field_vps)
        form.addRow(self.lbl_cpu, self.field_cpu)
        form.addRow(self.lbl_ram, self.field_ram)
        form.addRow(self.lbl_os, self.field_os)
        form.addRow(self.lbl_vpn, self.field_vpn)
        
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.on_save)
        self.save_callback = save_callback
        
        self.lbl_context_title = QLabel()
        layout.addWidget(self.lbl_context_title)
        layout.addWidget(info_group)
        layout.addWidget(self.save_btn)
        
        self.auto_info_label = QLabel()
        layout.addWidget(self.auto_info_label)
        layout.addStretch()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.lbl_vps.setText("VPS Provider/Location:")
        self.lbl_cpu.setText("CPU Model (Auto):")
        self.lbl_ram.setText("Total RAM (Auto):")
        self.lbl_os.setText(L.tr("lbl_os"))
        self.lbl_vpn.setText("VPN Config / Panel:")
        
        self.lbl_context_title.setText("📂 " + L.tr("info_title"))
        self.save_btn.setText("📥 " + L.tr("btn_save"))
        
        # Detected panels part
        current_panels = self.auto_info_label.text().split(": ")[-1] if ": " in self.auto_info_label.text() else "N/A"
        self.auto_info_label.setText(f"{L.tr('lbl_panels')}: {current_panels}")

    def update_auto_data(self, discovery):
        self.field_cpu.setText(discovery.get('cpu_model', ''))
        self.field_ram.setText(discovery.get('ram_total', ''))
        self.field_os.setText(discovery.get('os_version', ''))
        self.auto_info_label.setText(f"{L.tr('lbl_panels')}: {discovery.get('detected_panels', 'N/A')}")

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
