"""
Floating Bubble Mascot Widget.
A cute, draggable circular mascot companion that sits on top of all windows.
"""

from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QCursor, QAction

from ui.assets import create_cute_mascot_pixmap

class BubbleMascot(QWidget):
    request_expand = pyqtSignal()
    request_settings = pyqtSignal()
    request_quick_log = pyqtSignal()
    request_instant_nudge = pyqtSignal()
    request_close = pyqtSignal()
    mascot_moved = pyqtSignal(QRect)

    def __init__(self, size: int = 68, parent=None):
        super().__init__(parent)
        self.mascot_size = size
        self._glow_intensity = 0.5
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._click_start_pos = QPoint()

        # Frameless, Always on Top, Transparent, Never Steals Focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(self.mascot_size + 16, self.mascot_size + 16)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Second Brain AI Companion\nNhấn để mở chat • Kéo để di chuyển")

        # Cache mascot pixmap
        self.pixmap = create_cute_mascot_pixmap(self.mascot_size, glow=True)

        # Gentle breathing glow animation
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_glow)
        self._glow_dir = 0.02
        self.anim_timer.start(50)

    def _update_glow(self):
        self._glow_intensity += self._glow_dir
        if self._glow_intensity >= 0.9:
            self._glow_dir = -0.02
        elif self._glow_intensity <= 0.3:
            self._glow_dir = 0.02
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw mascot at center
        offset = (self.width() - self.mascot_size) / 2
        painter.drawPixmap(int(offset), int(offset), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_start_pos = event.globalPosition().toPoint() - self.pos()
            self._click_start_pos = event.globalPosition().toPoint()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._click_start_pos
            if delta.manhattanLength() > 3:
                self._dragging = True
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                self.move(event.globalPosition().toPoint() - self._drag_start_pos)
                self.mascot_moved.emit(self.geometry())
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if not self._dragging:
                self.request_expand.emit()
            self._dragging = False
            event.accept()

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(24, 28, 42, 0.95);
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #6366F1;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                margin: 4px 6px;
            }
        """)

        act_expand = menu.addAction("💬 Mở Khung Chat")
        act_nudge = menu.addAction("💡 Gợi ý chủ động ngay")
        act_quick = menu.addAction("📝 Ghi nhanh Daily Log")
        menu.addSeparator()
        act_settings = menu.addAction("⚙️ Cài Đặt")
        act_close = menu.addAction("❌ Đóng Ứng Dụng")

        action = menu.exec(pos)
        if action == act_expand:
            self.request_expand.emit()
        elif action == act_nudge:
            self.request_instant_nudge.emit()
        elif action == act_quick:
            self.request_quick_log.emit()
        elif action == act_settings:
            self.request_settings.emit()
        elif action == act_close:
            self.request_close.emit()

