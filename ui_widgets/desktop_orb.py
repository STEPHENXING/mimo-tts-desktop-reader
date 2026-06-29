from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication

class DesktopOrb(QWidget):
    clicked = Signal()
    stop_requested = Signal()
    pause_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(50, 50)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("🔊")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 144, 255, 0.8);
                color: white;
                border-radius: 25px;
                font-size: 20px;
            }
            QLabel:hover {
                background-color: rgba(0, 191, 255, 0.9);
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.move_to_edge()

    def move_to_edge(self):
        screen = QGuiApplication.primaryScreen().geometry()
        # Move to right edge, middle vertically
        x = screen.width() - self.width() - 10
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MiddleButton:
            self.pause_requested.emit()
        elif event.button() == Qt.RightButton:
            self.stop_requested.emit()
            
    def enterEvent(self, event):
        self.setCursor(Qt.PointingHandCursor)
