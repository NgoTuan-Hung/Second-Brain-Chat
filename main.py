"""
Second Brain AI Companion - Floating Desktop Client.
Entry point for running the floating desktop overlay chatbot.
"""

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer

from ui.floating_widget import FloatingCompanionApp
from ui.assets import create_cute_mascot_pixmap

def main():
    # Graceful handling for Ctrl+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Linux rendering optimizations & Wayland/X11 drag support
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    if "QT_QPA_PLATFORM" not in os.environ and os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("SecondBrainCompanion")
    app.setApplicationDisplayName("Second Brain AI Companion")
    app.setQuitOnLastWindowClosed(False)

    # Set app icon from cute mascot
    app_icon = QIcon(create_cute_mascot_pixmap(64, glow=False))
    app.setWindowIcon(app_icon)

    # Typography
    font = QFont()
    font.setFamilies(["Inter", "SF Pro Display", "Segoe UI", "Roboto", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(13)
    app.setFont(font)

    # Periodic timer to allow Python to process SIGINT signals
    sig_timer = QTimer()
    sig_timer.start(500)
    sig_timer.timeout.connect(lambda: None)

    # Instantiate floating companion app
    companion = FloatingCompanionApp()

    print("==================================================")
    print("🤖 Second Brain AI Companion is running!")
    print("💡 Nhấn vào Bubble Mascot hoặc dùng Hotkey để mở chat.")
    print("⚙️ Nhập Gemini API Key trong menu Cài đặt nếu chưa có.")
    print("==================================================")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
