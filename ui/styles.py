STYLE_SHEET = """
QMainWindow {
    background-color: #0d1117;
}

QTabWidget::pane {
    border: 1px solid #30363d;
    background: #0d1117;
    border-radius: 5px;
}

QTabBar::tab {
    background: #161a21;
    color: #8b949e;
    padding: 10px 20px;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:selected {
    background: #0d1117;
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}

QLabel {
    color: #c9d1d9;
    font-size: 13px;
}

QLineEdit, QSpinBox, QComboBox {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 3px;
    padding: 5px;
    color: #c9d1d9;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #58a6ff;
}

QPushButton {
    background: #238636;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px;
    font-weight: bold;
}

QPushButton:hover {
    background: #2ea043;
}

QPushButton:disabled {
    background: #161b22;
    color: #484f58;
}

QTableWidget {
    background-color: #0d1117;
    alternate-background-color: #161b22;
    color: #c9d1d9;
    gridline-color: #30363d;
    border: none;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 5px;
    border: 1px solid #30363d;
}

QTextEdit {
    background-color: #0d1117;
    color: #c9d1d9;
    border: 1px solid #30363d;
    font-family: 'Consolas', monospace;
}
"""
