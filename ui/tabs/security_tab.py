import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel

class SecurityTab(QWidget):
    """Вкладка аналитики безопасности трафика."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        sec_graph_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(sec_graph_widget)
        
        self.pps_plot = sec_graph_widget.addPlot(title="Packets Per Second (PPS)")
        self.pps_plot.setAxisItems({'bottom': pg.DateAxisItem()})
        self.pps_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pps_curve = self.pps_plot.plot(pen=pg.mkPen(color='#ffaa00', width=2))
        
        sec_graph_widget.nextRow()
        self.jitter_plot = sec_graph_widget.addPlot(title="Latency Jitter (ms)")
        self.jitter_plot.setAxisItems({'bottom': pg.DateAxisItem()})
        self.jitter_plot.showGrid(x=True, y=True, alpha=0.3)
        self.jitter_curve = self.jitter_plot.plot(pen=pg.mkPen(color='#ff00ff', width=2))
        
        # Активное сканирование
        layout.addWidget(QLabel("🕵️ Подозрительная активность (Active Probing):"))
        self.probe_table = QTableWidget()
        self.probe_table.setColumnCount(3)
        self.probe_table.setHorizontalHeaderLabels(["Source IP", "Attempts", "Last Seen"])
        self.probe_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.probe_table)

    def update_data(self, history_pps, timestamps, history_jitter, probing_data):
        self.pps_curve.setData(timestamps, history_pps)
        self.jitter_curve.setData(timestamps, history_jitter)
        
        self.probe_table.setRowCount(len(probing_data))
        for i, probe in enumerate(probing_data):
            self.probe_table.setItem(i, 0, QTableWidgetItem(probe['ip']))
            self.probe_table.setItem(i, 1, QTableWidgetItem(str(probe['attempts'])))
            self.probe_table.setItem(i, 2, QTableWidgetItem(probe['seen']))
        self.probe_table.scrollToBottom()
        self.jitter_plot.autoRange()
