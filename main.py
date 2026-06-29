import sys
import os
import re
import uuid
import threading
import time
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import QObject, Signal, QThread, Slot
from PySide6.QtGui import QIcon, QPixmap, QColor
from hook_service import HookService
from ui_widgets.float_icon import FloatIcon
from ui_widgets.desktop_orb import DesktopOrb
from ui_widgets.config_panel import ConfigPanel
from tts_engine import generate_tts
from audio_player import AudioPlayer
from clipboard_reader import copy_selected_text_safely
from config_manager import get_app_dir

def create_tray_icon():
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("blue"))
    return QIcon(pixmap)

def chunk_text(text):
    """Split text intelligently using punctuation."""
    chunks = re.split(r'([。！？；\n])', text)
    sentences = []
    current_sentence = ""
    
    for part in chunks:
        current_sentence += part
        # If part is punctuation or we are at the last chunk
        if re.match(r'[。！？；\n]', part) or part == chunks[-1]:
            current_sentence = current_sentence.strip()
            if current_sentence:
                # Basic splitting, assumes sentences roughly under limit. 
                # Very long run-on sentences might still be long, but safe enough.
                sentences.append(current_sentence)
            current_sentence = ""
    return sentences

class TTSWorker(QObject):
    chunk_ready = Signal(str)
    finished = Signal()

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.is_cancelled = False
        self.is_paused = False
        self.temp_dir = os.path.join(get_app_dir(), "tts_temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def wait_if_paused(self):
        while self.is_paused and not self.is_cancelled:
            time.sleep(0.05)

    @Slot()
    def run(self):
        chunks = chunk_text(self.text)
        run_id = str(uuid.uuid4())[:8]
        
        for i, chunk in enumerate(chunks):
            self.wait_if_paused()

            if self.is_cancelled:
                break
            
            # Generate unique file for each chunk
            file_name = os.path.join(self.temp_dir, f"chunk_{run_id}_{i}.mp3")
            audio_path = generate_tts(chunk, file_name)
            
            if audio_path and not self.is_cancelled:
                # Safely emit path to main thread
                self.chunk_ready.emit(audio_path)
                
        self.finished.emit()

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.audio_player = AudioPlayer()
        
        self.float_icon = FloatIcon()
        self.desktop_orb = DesktopOrb()
        self.config_panel = ConfigPanel()
        
        self.desktop_orb.clicked.connect(self.config_panel.toggle_show)
        self.desktop_orb.stop_requested.connect(self.stop_current_read)
        self.desktop_orb.pause_requested.connect(self.toggle_pause_current_read)
        self.config_panel.pause_btn.clicked.connect(self.toggle_pause_current_read)
        self.config_panel.stop_btn.clicked.connect(self.stop_current_read)
        
        self.float_icon.read_requested.connect(self.on_read_requested)
        self.float_icon.read_forward_requested.connect(self.on_read_forward_requested)
        
        self.hook_service = HookService()
        self.hook_service.worker.text_selected.connect(self.on_text_selected)
        
        self.desktop_orb.show()
        self.hook_service.start()
        
        self.setup_tray()
        
        self.worker_thread = None
        self.worker = None
        self.old_threads = []

    def setup_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_tray_icon())
        self.tray.setToolTip("MiMo TTS 全局朗读助手")
        
        menu = QMenu()
        settings_action = menu.addAction("设置 (Settings)")
        settings_action.triggered.connect(self.config_panel.show)
        
        self.pause_action = menu.addAction("暂停朗读 (Pause)")
        self.pause_action.triggered.connect(self.toggle_pause_current_read)
        
        stop_action = menu.addAction("停止朗读 (Stop TTS)")
        stop_action.triggered.connect(self.stop_current_read)
        
        quit_action = menu.addAction("退出 (Quit)")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def on_text_selected(self, text, x, y):
        self.float_icon.show_at(x, y, text)

    def read_selection_safely(self, keyboard_controller):
        try:
            return copy_selected_text_safely(keyboard_controller)
        except Exception as e:
            print(f"Failed to read selected text: {e}")
            return ""

    def stop_current_read(self):
        """Immediately stops playback and cancels background fetching."""
        self.audio_player.clear_queue()
        if self.worker:
            self.worker.is_cancelled = True
            self.worker.is_paused = False
        self.update_pause_ui(False)
            
        if self.worker_thread:
            # Keep a reference to the old thread so Python doesn't garbage collect it 
            # while it's still blocking on a network request.
            self.old_threads.append((self.worker_thread, self.worker))
            self.worker_thread = None
            self.worker = None
            
        # Clean up already finished threads from the reference list safely
        valid_threads = []
        for t, w in self.old_threads:
            try:
                if t.isRunning():
                    valid_threads.append((t, w))
            except RuntimeError:
                # C++ object already deleted by deleteLater
                pass
        self.old_threads = valid_threads

    def update_pause_ui(self, is_paused):
        self.config_panel.set_paused(is_paused)
        if hasattr(self, "pause_action"):
            if is_paused:
                self.pause_action.setText("继续朗读 (Resume)")
            else:
                self.pause_action.setText("暂停朗读 (Pause)")

    def toggle_pause_current_read(self):
        has_audio_work = (
            self.worker
            or self.audio_player.is_playing
            or self.audio_player.playlist
            or self.audio_player.is_paused
        )
        if not has_audio_work:
            self.update_pause_ui(False)
            return

        is_paused = self.audio_player.toggle_pause()
        if self.worker:
            self.worker.is_paused = is_paused
        self.update_pause_ui(is_paused)

    def on_read_requested(self, text):
        if not text:
            from pynput.keyboard import Controller

            text = self.read_selection_safely(Controller())

        if not text or not text.strip():
            return

        self.stop_current_read()
        self.update_pause_ui(False)
        
        self.worker_thread = QThread()
        self.worker = TTSWorker(text.strip())
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.chunk_ready.connect(self.audio_player.enqueue_audio)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        self.worker_thread.start()
        
    def on_read_forward_requested(self):
        self.stop_current_read()
        
        def _simulate_and_read():
            from pynput.keyboard import Controller, Key
            import time
            
            kb = Controller()
            
            # Select to end of document
            with kb.pressed(Key.ctrl):
                with kb.pressed(Key.shift):
                    kb.press(Key.end)
                    kb.release(Key.end)
                    
            time.sleep(0.1)
            
            # Read the expanded selection without leaving it in the global clipboard.
            new_text = self.read_selection_safely(kb)
            
            if new_text and new_text.strip():
                # We can safely call on_read_requested from here as it handles thread wrapping
                self.on_read_requested(new_text.strip())

        threading.Thread(target=_simulate_and_read, daemon=True).start()

    def quit_app(self):
        self.stop_current_read()
        self.hook_service.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = MainApp()
    app.run()
