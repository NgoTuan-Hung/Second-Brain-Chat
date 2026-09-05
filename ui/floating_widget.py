"""
Main Floating Desktop Widget & Controller.
Coordinates the Frameless Chat Window, Mascot Bubble, Drag/Resize mechanics, and Hotkeys.
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizeGrip
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import QMouseEvent

from config import config
from ui.styles import DARK_GLASS_STYLE
from ui.chat_panel import ChatPanel
from ui.bubble_mascot import BubbleMascot
from ui.settings_dialog import SettingsDialog
from core.agent import SecondBrainAgent
from core.hotkeys import HotkeyListener

class FloatingChatWindow(QWidget):
    EDGE_MARGIN = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_start_pos = QPoint()

        # 8-Direction Resize tracking
        self._is_resizing = False
        self._resizing_dir = None
        self._resize_start_pos = QPoint()
        self._resize_start_geo = QRect()

        # Frameless, Always On Top, Translucent
        self._apply_window_flags(config.always_on_top)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_GLASS_STYLE)

        # Restore size and position
        w = config.get("window_width", 430)
        h = config.get("window_height", 640)
        x = config.get("last_x", 150)
        y = config.get("last_y", 150)
        self.setGeometry(x, y, w, h)
        self.setMinimumSize(340, 450)

        self._is_maximized = False
        self._normal_geo = self.geometry()

        self._setup_ui()
        self.setMouseTracking(True)
        self.main_container.setMouseTracking(True)
        self.main_container.installEventFilter(self)

    def toggle_maximize(self):
        if self._is_maximized:
            self.setGeometry(self._normal_geo)
            self._is_maximized = False
        else:
            self._normal_geo = self.geometry()
            screen = self.screen().availableGeometry()
            # Leave small padding for screen aesthetics
            self.setGeometry(screen.adjusted(10, 10, -10, -10))
            self._is_maximized = True

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.chat_panel.request_minimize.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _apply_window_flags(self, always_on_top: bool):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _setup_ui(self):
        # Outer container layout for drop shadow / border radius and edge resize margin
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(0)

        self.main_container = QWidget()
        self.main_container.setObjectName("MainContainer")
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Chat Panel
        self.chat_panel = ChatPanel(self.main_container)
        container_layout.addWidget(self.chat_panel, 1)

        # Bottom bar with size grip
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(14)
        bottom_bar.setStyleSheet("background: transparent;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 0, 4, 1)
        bottom_layout.addStretch()

        self.size_grip = QSizeGrip(self)
        self.size_grip.setToolTip("Kéo để thay đổi kích thước")
        bottom_layout.addWidget(self.size_grip)

        container_layout.addWidget(bottom_bar)
        outer_layout.addWidget(self.main_container)

    def _get_resize_direction(self, pos: QPoint) -> Optional[str]:
        w = self.width()
        h = self.height()
        m = self.EDGE_MARGIN

        x = pos.x()
        y = pos.y()

        left = x <= m
        right = x >= (w - m)
        top = y <= m
        bottom = y >= (h - m)

        if top and left:
            return "top-left"
        if top and right:
            return "top-right"
        if bottom and left:
            return "bottom-left"
        if bottom and right:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _update_cursor_for_direction(self, direction: Optional[str]):
        if direction in ("top-left", "bottom-right"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif direction in ("top-right", "bottom-left"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif direction in ("left", "right"):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif direction in ("top", "bottom"):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def eventFilter(self, obj, event):
        if obj == self.main_container:
            if event.type() == event.Type.MouseMove:
                if not self._is_resizing:
                    win_pos = self.main_container.mapTo(self, event.position().toPoint())
                    dir_name = self._get_resize_direction(win_pos)
                    self._update_cursor_for_direction(dir_name)
                elif self._is_resizing and (event.buttons() & Qt.MouseButton.LeftButton):
                    self._handle_resize_move(event.globalPosition().toPoint())
                    return True

            elif event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    win_pos = self.main_container.mapTo(self, event.position().toPoint())
                    dir_name = self._get_resize_direction(win_pos)
                    if dir_name:
                        self._is_resizing = True
                        self._resizing_dir = dir_name
                        self._resize_start_pos = event.globalPosition().toPoint()
                        self._resize_start_geo = self.geometry()
                        return True

            elif event.type() == event.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton and self._is_resizing:
                    self._is_resizing = False
                    self._resizing_dir = None
                    self._update_cursor_for_direction(None)
                    self._save_geometry()
                    return True

        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            dir_name = self._get_resize_direction(event.position().toPoint())
            if dir_name:
                self._is_resizing = True
                self._resizing_dir = dir_name
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geo = self.geometry()
                event.accept()
                return

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_resizing and self._resizing_dir and (event.buttons() & Qt.MouseButton.LeftButton):
            self._handle_resize_move(event.globalPosition().toPoint())
            event.accept()
        else:
            dir_name = self._get_resize_direction(event.position().toPoint())
            self._update_cursor_for_direction(dir_name)
            super().mouseMoveEvent(event)

    def _handle_resize_move(self, cur_global_pos: QPoint):
        dx = cur_global_pos.x() - self._resize_start_pos.x()
        dy = cur_global_pos.y() - self._resize_start_pos.y()

        orig = self._resize_start_geo
        min_w, min_h = 340, 450

        new_x = orig.x()
        new_y = orig.y()
        new_w = orig.width()
        new_h = orig.height()

        if "left" in self._resizing_dir:
            calculated_w = orig.width() - dx
            if calculated_w >= min_w:
                new_w = calculated_w
                new_x = orig.x() + dx
            else:
                new_w = min_w
                new_x = orig.right() - min_w + 1

        elif "right" in self._resizing_dir:
            new_w = max(min_w, orig.width() + dx)

        if "top" in self._resizing_dir:
            calculated_h = orig.height() - dy
            if calculated_h >= min_h:
                new_h = calculated_h
                new_y = orig.y() + dy
            else:
                new_h = min_h
                new_y = orig.bottom() - min_h + 1

        elif "bottom" in self._resizing_dir:
            new_h = max(min_h, orig.height() + dy)

        self.setGeometry(new_x, new_y, new_w, new_h)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_resizing:
                self._is_resizing = False
                self._resizing_dir = None
                self._update_cursor_for_direction(None)
                self._save_geometry()
                event.accept()
                return

    def leaveEvent(self, event):
        if not self._is_resizing:
            self._update_cursor_for_direction(None)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._save_geometry()

    def _save_geometry(self):
        config.set("last_x", self.x())
        config.set("last_y", self.y())
        config.set("window_width", self.width())
        config.set("window_height", self.height())


class FloatingCompanionApp:
    """
    Root controller orchestrating the Chat Window, Bubble Mascot, AI Agent, and Hotkeys.
    """
    def __init__(self):
        self.chat_window = FloatingChatWindow()
        self.bubble = BubbleMascot(size=64)
        self.agent = SecondBrainAgent()
        self.hotkey_listener = HotkeyListener(config.hotkey)
        self.settings_dialog = None

        self._connect_signals()
        self.hotkey_listener.start()

        # Start by showing the Chat Window
        self.chat_window.show()

    def _connect_signals(self):
        # Chat Panel UI to AI Agent
        self.chat_window.chat_panel.message_sent.connect(self.agent.send_message)
        self.chat_window.chat_panel.request_minimize.connect(self.minimize_to_bubble)
        self.chat_window.chat_panel.request_settings.connect(self.open_settings)
        self.chat_window.chat_panel.request_close.connect(self.hide_to_bubble)
        self.chat_window.chat_panel.request_pin.connect(self._toggle_pin)

        # AI Agent to Chat Panel UI
        self.agent.chunk_received.connect(self.chat_window.chat_panel.on_chunk_received)
        self.agent.tool_started.connect(self.chat_window.chat_panel.on_tool_started)
        self.agent.tool_finished.connect(self.chat_window.chat_panel.on_tool_finished)
        self.agent.thinking_updated.connect(self.chat_window.chat_panel.on_thinking_updated)
        self.agent.token_usage_updated.connect(self.chat_window.chat_panel.on_token_usage_updated)
        self.agent.response_finished.connect(self.chat_window.chat_panel.on_response_finished)
        self.agent.error_occurred.connect(self.chat_window.chat_panel.on_error)

        # Bubble Mascot to Controller
        self.bubble.request_expand.connect(self.expand_from_bubble)
        self.bubble.request_settings.connect(self.open_settings)
        self.bubble.request_quick_log.connect(self._on_quick_log_from_bubble)
        self.bubble.request_close.connect(self.quit_app)

        # Global Hotkey
        self.hotkey_listener.hotkey_triggered.connect(self.toggle_visibility)

    def _toggle_pin(self, is_pinned: bool):
        config.set("always_on_top", is_pinned)
        pos = self.chat_window.pos()
        size = self.chat_window.size()
        self.chat_window._apply_window_flags(is_pinned)
        self.chat_window.setGeometry(pos.x(), pos.y(), size.width(), size.height())
        self.chat_window.show()

    def minimize_to_bubble(self):
        pos = self.chat_window.pos()
        self.chat_window.hide()
        bx = max(20, pos.x() + self.chat_window.width() - 80)
        by = max(20, pos.y())
        self.bubble.move(bx, by)
        self.bubble.show()
        self.bubble.raise_()

    def hide_to_bubble(self):
        self.minimize_to_bubble()

    def expand_from_bubble(self):
        bubble_pos = self.bubble.pos()
        self.bubble.hide()
        target_x = max(20, bubble_pos.x() - self.chat_window.width() + 80)
        target_y = max(20, bubble_pos.y())
        self.chat_window.move(target_x, target_y)
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()
        self.chat_window.chat_panel.prompt_input.setFocus()

    def _on_quick_log_from_bubble(self):
        self.expand_from_bubble()
        self.chat_window.chat_panel._quick_prompt("Ghi nhật ký: ")

    def toggle_visibility(self):
        if self.chat_window.isVisible():
            self.minimize_to_bubble()
        else:
            self.expand_from_bubble()

    def open_settings(self):
        self.settings_dialog = SettingsDialog(self.chat_window)
        self.settings_dialog.settings_saved.connect(self._on_settings_saved)
        self.settings_dialog.exec()

    def _on_settings_saved(self):
        self.chat_window.chat_panel.refresh_vault_status()
        self.chat_window.chat_panel._update_thinking_btn_style()
        self.hotkey_listener.update_hotkey(config.hotkey)
        self._toggle_pin(config.always_on_top)

    def quit_app(self):
        self.hotkey_listener.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

