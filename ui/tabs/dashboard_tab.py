import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel

class DashboardTab(QWidget):
    """Вкладка мониторинга ресурсов сервера."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.graph_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_widget)
        
        # CPU Plot
        self.cpu_plot = self.graph_widget.addPlot(title="CPU Load (%)")
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setAxisItems({'bottom': pg.DateAxisItem()})
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color='#58a6ff', width=2))
        
        self.graph_widget.nextRow()
        # RAM Plot
        self.ram_plot = self.graph_widget.addPlot(title="RAM Usage (%)")
        self.ram_plot.setYRange(0, 100)
        self.ram_plot.setAxisItems({'bottom': pg.DateAxisItem()})
        self.ram_plot.showGrid(x=True, y=True, alpha=0.3)
        self.ram_curve = self.ram_plot.plot(pen=pg.mkPen(color='#238636', width=2))
        
        # Таблица пользователей
        layout.addWidget(QLabel("👥 Активные пользователи:"))
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["User", "IP", "Traffic"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.user_table)

    def update_charts(self, cpu_history, ram_history, timestamps):
        self.cpu_curve.setData(timestamps, cpu_history)
        self.ram_curve.setData(timestamps, ram_history)

    def update_users(self, df_users):
        self.user_table.setRowCount(len(df_users))
        for i, row in df_users.iterrows():
            self.user_table.setItem(i, 0, QTableWidgetItem(str(row['user'])))
            self.user_table.setItem(i, 1, QTableWidgetItem(str(row['ip'])))
            self.user_table.setItem(i, 2, QTableWidgetItem(str(row['traffic'])))
