from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QSlider, QPushButton, QFormLayout
from PySide6.QtCore import Qt
from config_manager import config, VOICES, DIALECTS, EMOTIONS

class ConfigPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiMo TTS 配置")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.resize(300, 200)
        
        layout = QFormLayout()
        
        self.voice_cb = QComboBox()
        self.voice_cb.addItems(VOICES)
        self.voice_cb.setCurrentText(config.get("voice", "mimo_default"))
        self.voice_cb.currentTextChanged.connect(self.on_voice_changed)
        
        self.dialect_cb = QComboBox()
        self.dialect_cb.addItems(DIALECTS)
        self.dialect_cb.setCurrentText(config.get("dialect", "无"))
        self.dialect_cb.currentTextChanged.connect(lambda t: config.set("dialect", t))
        
        self.emotion_cb = QComboBox()
        self.emotion_cb.addItems(EMOTIONS)
        self.emotion_cb.setCurrentText(config.get("emotion", "无"))
        self.emotion_cb.currentTextChanged.connect(lambda t: config.set("emotion", t))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(5)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(int(config.get("speed", 1.0) * 10))
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        layout.addRow("音色选择:", self.voice_cb)
        layout.addRow("方言选择:", self.dialect_cb)
        layout.addRow("情绪选择:", self.emotion_cb)
        layout.addRow("语速调节:", self.speed_slider)
        
        self.pause_btn = QPushButton("⏸️ 暂停朗读")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800; color: white; border-radius: 5px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)
        layout.addRow(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止朗读")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border-radius: 5px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        layout.addRow(self.stop_btn)
        
        self.setLayout(layout)

    def on_voice_changed(self, text):
        config.set("voice", text)

    def on_speed_changed(self, val):
        config.set("speed", val / 10.0)

    def set_paused(self, is_paused):
        if is_paused:
            self.pause_btn.setText("▶️ 继续朗读")
        else:
            self.pause_btn.setText("⏸️ 暂停朗读")

    def toggle_show(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
