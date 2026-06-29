import ctypes
import threading
import time
import uuid
from dataclasses import dataclass


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_bool
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.c_bool
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = ctypes.c_bool
user32.EnumClipboardFormats.argtypes = [ctypes.c_uint]
user32.EnumClipboardFormats.restype = ctypes.c_uint
user32.GetClipboardData.argtypes = [ctypes.c_uint]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p

kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_bool
kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
kernel32.GlobalSize.restype = ctypes.c_size_t

_clipboard_lock = threading.RLock()


@dataclass
class ClipboardItem:
    format_id: int
    data: bytes


class ClipboardSnapshot:
    def __init__(self, items):
        self.items = items

    @classmethod
    def capture(cls):
        items = []
        with _open_clipboard():
            format_id = 0
            while True:
                format_id = user32.EnumClipboardFormats(format_id)
                if format_id == 0:
                    break

                handle = user32.GetClipboardData(format_id)
                if not handle:
                    continue

                size = kernel32.GlobalSize(handle)
                if size <= 0:
                    continue

                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    continue

                try:
                    items.append(ClipboardItem(format_id, ctypes.string_at(pointer, size)))
                finally:
                    kernel32.GlobalUnlock(handle)

        return cls(items)

    def restore(self):
        with _open_clipboard():
            user32.EmptyClipboard()
            for item in self.items:
                handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(item.data))
                if not handle:
                    continue

                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    continue

                ctypes.memmove(pointer, item.data, len(item.data))
                kernel32.GlobalUnlock(handle)

                if not user32.SetClipboardData(item.format_id, handle):
                    continue


class _open_clipboard:
    def __enter__(self):
        deadline = time.time() + 0.5
        while time.time() < deadline:
            if user32.OpenClipboard(None):
                return self
            time.sleep(0.01)
        raise RuntimeError("Could not open clipboard")

    def __exit__(self, exc_type, exc, tb):
        user32.CloseClipboard()


def _set_clipboard_text(text):
    data = text.encode("utf-16-le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        raise RuntimeError("Could not allocate clipboard memory")

    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        raise RuntimeError("Could not lock clipboard memory")

    ctypes.memmove(pointer, data, len(data))
    kernel32.GlobalUnlock(handle)

    with _open_clipboard():
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise RuntimeError("Could not set clipboard text")


def _get_clipboard_text():
    with _open_clipboard():
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""

        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return ""

        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)


def _press_copy_hotkey(keyboard_controller):
    from pynput import keyboard

    with keyboard_controller.pressed(keyboard.Key.ctrl):
        keyboard_controller.press("c")
        keyboard_controller.release("c")


def copy_selected_text_safely(keyboard_controller, timeout=0.8):
    """
    Read the current selection through Ctrl+C, then restore the user's clipboard.

    Cross-application selection APIs are inconsistent on Windows. This keeps the
    compatible copy route but makes the copied text an internal return value
    instead of leaving it in the global clipboard.
    """
    with _clipboard_lock:
        snapshot = ClipboardSnapshot.capture()
        marker = f"__MIMOREADER_CLIPBOARD_PROBE_{uuid.uuid4().hex}__"
        text = ""

        try:
            _set_clipboard_text(marker)
            _press_copy_hotkey(keyboard_controller)

            deadline = time.time() + timeout
            while time.time() < deadline:
                current = _get_clipboard_text()
                if current and current != marker:
                    text = current
                    break
                time.sleep(0.03)

            return text.strip()
        finally:
            snapshot.restore()
