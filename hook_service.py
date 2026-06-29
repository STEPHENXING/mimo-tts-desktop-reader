import time
from pynput import mouse
from PySide6.QtCore import QObject, Signal, QThread

class HookWorker(QObject):
    text_selected = Signal(str, int, int) # text, x, y

    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.mouse_listener = None
        self.is_running = False

    def start_hook(self):
        self.is_running = True
        self.mouse_listener = mouse.Listener(
            on_click=self.on_click
        )
        self.mouse_listener.start()

    def stop_hook(self):
        self.is_running = False
        if self.mouse_listener:
            self.mouse_listener.stop()

    def on_click(self, x, y, button, pressed):
        if not self.is_running:
            return

        if button == mouse.Button.left:
            if pressed:
                self.start_pos = (x, y)
            else:
                if self.start_pos:
                    end_pos = (x, y)
                    dx = abs(end_pos[0] - self.start_pos[0])
                    dy = abs(end_pos[1] - self.start_pos[1])
                    
                    if dx > 10 or dy > 10:
                        self.handle_selection(x, y)
                    
                    self.start_pos = None

    def handle_selection(self, x, y):
        time.sleep(0.05)
        self.text_selected.emit("", int(x), int(y))

class HookService(QThread):
    def __init__(self):
        super().__init__()
        self.worker = HookWorker()

    def run(self):
        self.worker.start_hook()
        self.exec() # Wait

    def stop(self):
        self.worker.stop_hook()
        self.quit()
        self.wait()
