"""
Floating Speech & Thought Bubble Widget.
A modern glassmorphism speech bubble anchored to the Mascot with auto-positioning,
interactive action pills, fade animations, and auto-dismiss.
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QCursor, QGuiApplication, QFont

class ActionPillButton(QPushButton):
    """Sleek rounded pill action button."""
    def __init__(self, text: str, is_primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if is_primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                    color: #FFFFFF;
                    border: none;
                    border-radius: 12px;
                    padding: 5px 12px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
                }
                QPushButton:pressed {
                    background: #4338CA;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    color: #CBD5E1;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 12px;
                    padding: 5px 11px;
                    font-size: 11.5px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.16);
                    color: #FFFFFF;
                    border-color: rgba(255, 255, 255, 0.25);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.05);
                }
            """)


class SpeechBubble(QWidget):
    """
    Speech Bubble attached to BubbleMascot.
    Displays proactive notifications with action buttons.
    """
    action_clicked = pyqtSignal(str, dict)  # (action_id, nudge_data)
    body_clicked = pyqtSignal(dict)         # (nudge_data)
    bubble_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nudge_data: Dict[str, Any] = {}
        self.pointer_side = "right"  # "right", "left", "bottom", "top"
        self._mascot_rect = QRect()
        self._is_paused = False

        # Window configuration - HUD Notification: never steal focus from user typing
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedWidth(360)

        # Opacity animation for smooth fade
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(220)

        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide_bubble)

        self._setup_ui()

    def _setup_ui(self):
        # Outer layout with margins for pointer tail
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(16, 16, 16, 16)
        self.outer_layout.setSpacing(0)

        # Card container
        self.card = QWidget(self)
        self.card.setObjectName("BubbleCard")
        self.card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # 1. Header row (Tag Badge + Close button)
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        self.badge_label = QLabel("✨ PROACTIVE NUDGE")
        self.badge_label.setStyleSheet("""
            QLabel {
                background: rgba(139, 92, 246, 0.22);
                color: #C4B5FD;
                border: 1px solid rgba(139, 92, 246, 0.4);
                border-radius: 6px;
                padding: 2px 7px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
        """)
        header_row.addWidget(self.badge_label)
        header_row.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
            }
        """)
        self.close_btn.clicked.connect(self.hide_bubble)
        header_row.addWidget(self.close_btn)
        card_layout.addLayout(header_row)

        # 2. Title
        self.title_label = QLabel("Gợi ý từ Second Brain")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #F8FAFC;
                font-size: 13px;
                font-weight: 700;
                line-height: 1.3;
            }
        """)
        card_layout.addWidget(self.title_label)

        # 3. Message Body (enclosed in a sleek glassmorphic QScrollArea)
        self.scroll_area = QScrollArea(self.card)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.04);
                width: 5px;
                margin: 0px;
                border-radius: 2.5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 92, 246, 0.45);
                min-height: 20px;
                border-radius: 2.5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(168, 85, 247, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        # Inner container for scrollable text
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(0, 2, 4, 2)
        scroll_layout.setSpacing(0)

        self.body_label = QLabel("Nội dung thông báo chi tiết...")
        self.body_label.setWordWrap(True)
        self.body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body_label.setStyleSheet("""
            QLabel {
                color: #CBD5E1;
                font-size: 12px;
                line-height: 1.45;
                background: transparent;
            }
        """)
        scroll_layout.addWidget(self.body_label)
        self.scroll_area.setWidget(self.scroll_content)

        card_layout.addWidget(self.scroll_area)

        # 4. Action buttons container
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(6)
        self.actions_layout.setContentsMargins(0, 4, 0, 0)
        card_layout.addLayout(self.actions_layout)

        self.outer_layout.addWidget(self.card)

    def set_nudge(self, data: Dict[str, Any]):
        """Populates the speech bubble with nudge payload."""
        self.nudge_data = data

        # Category Badge
        category = data.get("category", "PROACTIVE").upper()
        emoji = data.get("emoji", "✨")
        self.badge_label.setText(f"{emoji} {category}")

        # Accent color per category
        color_map = {
            "MORNING": ("rgba(245, 158, 11, 0.22)", "#FCD34D", "rgba(245, 158, 11, 0.4)"),
            "EVENING": ("rgba(168, 85, 247, 0.22)", "#E9D5FF", "rgba(168, 85, 247, 0.4)"),
            "SPACED REPETITION": ("rgba(59, 130, 246, 0.22)", "#93C5FD", "rgba(59, 130, 246, 0.4)"),
            "TODO": ("rgba(16, 185, 129, 0.22)", "#6EE7B7", "rgba(16, 185, 129, 0.4)"),
        }
        bg, fg, border = color_map.get(category, ("rgba(139, 92, 246, 0.22)", "#C4B5FD", "rgba(139, 92, 246, 0.4)"))
        self.badge_label.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 2px 7px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)

        # Title and message
        self.title_label.setText(data.get("title", "Thông Báo"))
        self.body_label.setText(data.get("message", ""))

        # Reset scroll position to top
        self.scroll_area.verticalScrollBar().setValue(0)

        # Clear previous action buttons
        while self.actions_layout.count() > 0:
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Re-populate action buttons
        actions = data.get("actions", [])
        if not actions:
            actions = [{"id": "open_chat", "label": "Mở Chat", "primary": True}]

        for idx, act in enumerate(actions):
            is_primary = act.get("primary", (idx == 0))
            btn = ActionPillButton(act.get("label", "Xem"), is_primary=is_primary, parent=self.card)
            act_id = act.get("id", "default")
            btn.clicked.connect(lambda checked=False, aid=act_id: self._on_action_click(aid))
            self.actions_layout.addWidget(btn)

        self.actions_layout.addStretch()

        # Dynamically size scroll area based on text content
        # Inner width is ~300px
        content_w = 300
        text_h = self.body_label.heightForWidth(content_w)
        # Cap height between 35px and 190px
        scroll_h = max(35, min(190, text_h + 10))
        self.scroll_area.setFixedHeight(scroll_h)

        # Adjust height according to contents
        self.card.adjustSize()
        self.adjustSize()

    def _on_action_click(self, action_id: str):
        self.action_clicked.emit(action_id, self.nudge_data)
        self.hide_bubble()

    def keyPressEvent(self, event):
        """Ignore all key presses to avoid accidental dismissal or capturing user typing."""
        event.ignore()

    def wheelEvent(self, event):
        """Pass mouse wheel scrolling anywhere on bubble directly to the scroll area."""
        self.scroll_area.wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If clicked inside scroll area, allow text selection and scrolling without closing
            pos_in_scroll = self.scroll_area.mapFrom(self, event.pos())
            if self.scroll_area.rect().contains(pos_in_scroll):
                super().mousePressEvent(event)
                return

            # Click on bubble card header, title or empty space opens main chat panel
            self.body_clicked.emit(self.nudge_data)
            self.hide_bubble()
            event.accept()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        """User is reading the bubble - pause auto-dismiss."""
        self._is_paused = True
        self.dismiss_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """User moved away - resume dismiss timer according to user's configured duration."""
        self._is_paused = False
        duration = getattr(self, "_auto_dismiss_sec", 15)
        if duration > 0:
            # Continue counting down for the full configured duration
            self.dismiss_timer.start(duration * 1000)
        super().leaveEvent(event)

    def show_nudge(self, data: Dict[str, Any], mascot_rect: QRect, auto_dismiss_sec: int = 15):
        """Prepares, positions, and animates showing the speech bubble."""
        self._mascot_rect = mascot_rect
        self._auto_dismiss_sec = auto_dismiss_sec
        self.set_nudge(data)
        self.reposition(mascot_rect)

        # Animate Fade In
        self.show()
        self.raise_()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_anim.start()

        # Start countdown
        if auto_dismiss_sec > 0:
            self.dismiss_timer.start(auto_dismiss_sec * 1000)

    def reposition(self, mascot_rect: QRect):
        """Calculates optimal position relative to Mascot and screen bounds."""
        self._mascot_rect = mascot_rect
        screen = QGuiApplication.screenAt(mascot_rect.center())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        bw = self.width()
        bh = self.height()
        gap = 8

        # Decide horizontal placement: Left or Right of mascot
        center_x = mascot_rect.center().x()
        if center_x > screen_geo.center().x():
            # Mascot is on right side -> place bubble to LEFT of mascot
            target_x = mascot_rect.left() - bw - gap
            self.pointer_side = "right"
        else:
            # Mascot is on left side -> place bubble to RIGHT of mascot
            target_x = mascot_rect.right() + gap
            self.pointer_side = "left"

        # Align vertically with mascot center
        target_y = mascot_rect.center().y() - (bh // 2)

        # Clamping within screen bounds
        min_x = screen_geo.left() + 10
        max_x = screen_geo.right() - bw - 10
        min_y = screen_geo.top() + 10
        max_y = screen_geo.bottom() - bh - 10

        target_x = max(min_x, min(max_x, target_x))
        target_y = max(min_y, min(max_y, target_y))

        self.move(int(target_x), int(target_y))
        self.update()

    def hide_bubble(self):
        """Animates fade out and closes."""
        self.dismiss_timer.stop()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_anim.finished.connect(self._on_fade_out_finished)
        self.fade_anim.start()

    def _on_fade_out_finished(self):
        try:
            self.fade_anim.finished.disconnect(self._on_fade_out_finished)
        except Exception:
            pass
        self.hide()
        self.bubble_closed.emit()

    def paintEvent(self, event):
        """Draws glowing glassmorphism rounded bubble with pointer tail."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Card rect
        card_geo = self.card.geometry()
        radius = 14.0

        # Create main rounded bubble path
        path = QPainterPath()
        path.addRoundedRect(
            card_geo.x(), card_geo.y(),
            card_geo.width(), card_geo.height(),
            radius, radius
        )

        # Draw tail pointer pointing towards mascot
        if self._mascot_rect.isValid():
            mascot_center = self._mascot_rect.center()
            bubble_local_mascot = self.mapFromGlobal(mascot_center)

            tail_path = QPainterPath()
            tail_w = 14
            tail_h = 10

            if self.pointer_side == "right":
                # Tail points to the right towards mascot
                base_y = card_geo.y() + (card_geo.height() // 2)
                tail_path.moveTo(card_geo.right(), base_y - tail_w // 2)
                tail_path.lineTo(card_geo.right() + tail_h, base_y)
                tail_path.lineTo(card_geo.right(), base_y + tail_w // 2)
                tail_path.closeSubpath()
            elif self.pointer_side == "left":
                # Tail points to the left towards mascot
                base_y = card_geo.y() + (card_geo.height() // 2)
                tail_path.moveTo(card_geo.left(), base_y - tail_w // 2)
                tail_path.lineTo(card_geo.left() - tail_h, base_y)
                tail_path.lineTo(card_geo.left(), base_y + tail_w // 2)
                tail_path.closeSubpath()

            path = path.united(tail_path)

        # 1. Fill background with glassmorphism gradient
        gradient_brush = QBrush(QColor(18, 22, 34, 238))
        painter.fillPath(path, gradient_brush)

        # 2. Draw subtle glowing purple/blue border
        pen = QPen(QColor(139, 92, 246, 90), 1.2)
        painter.setPen(pen)
        painter.drawPath(path)
