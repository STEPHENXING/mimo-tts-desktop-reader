from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont

class FloatIcon(QWidget):
    read_requested = Signal(str)
    read_forward_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Prevents stealing focus
        self.setFocusPolicy(Qt.NoFocus)
        
        self.current_text = ""
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        btn_style = """
            QPushButton {
                background-color: #4CAF50; color: white; border-radius: 15px; padding: 8px 15px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """
        
        self.btn_read = QPushButton("🔊 朗读选中")
        self.btn_read.setFocusPolicy(Qt.NoFocus)
        self.btn_read.setStyleSheet(btn_style)
        self.btn_read.clicked.connect(self.on_read_click)
        
        self.btn_forward = QPushButton("⬇️ 从此往下读")
        self.btn_forward.setFocusPolicy(Qt.NoFocus)
        self.btn_forward.setStyleSheet(btn_style.replace("#4CAF50", "#2196F3").replace("#45a049", "#1976D2"))
        self.btn_forward.clicked.connect(self.on_forward_click)
        
        layout.addWidget(self.btn_read)
        layout.addWidget(self.btn_forward)
        
        self.setLayout(layout)
        self.setFixedSize(220, 40)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def show_at(self, x, y, text):
        self.current_text = text
        self.move(x + 15, y + 15)
        self.show()
        self.hide_timer.start(4000)

    def on_read_click(self):
        self.hide_timer.stop()
        self.hide()
        self.read_requested.emit(self.current_text)
            
    def on_forward_click(self):
        self.hide_timer.stop()
        self.hide()
        self.read_forward_requested.emit()
