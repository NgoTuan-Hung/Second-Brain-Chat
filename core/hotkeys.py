"""
Global Hotkey Listener for Linux / Desktop.
Uses pynput to register system-wide shortcuts and emits PyQt signals.
"""

import threading
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyListener(QObject):
    hotkey_triggered = pyqtSignal()

    def __init__(self, hotkey_str: str = "<ctrl>+<shift>+s"):
        super().__init__()
        self.hotkey_str = hotkey_str
        self._listener = None
        self._thread = None
        self._running = False

    def start(self):
        try:
            from pynput import keyboard

            def on_activate():
                self.hotkey_triggered.emit()

            # Normalize hotkey format for pynput
            hotkey_mapping = {self.hotkey_str: on_activate}

            self._listener = keyboard.GlobalHotKeys(hotkey_mapping)
            self._listener.daemon = True
            self._listener.start()
            self._running = True
            print(f"[Hotkey] Listening for global shortcut: {self.hotkey_str}")
        except Exception as e:
            print(f"[Hotkey] Could not initialize global hotkey listener: {e}")
            print("[Hotkey] Note: Global hotkey may require X11 or input device permissions on Linux.")

    def stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
            self._running = False

    def update_hotkey(self, new_hotkey: str):
        self.stop()
        self.hotkey_str = new_hotkey
        self.start()
