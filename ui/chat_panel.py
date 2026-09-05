"""
Modern Glassmorphism Chat Panel Widget for Second Brain AI Companion.
Provides rich markdown rendering, quick action pills, tool badges, and streaming output.
"""

import re
import json
import time
import markdown2
from datetime import datetime
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QFrame, QApplication, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPixmap, QClipboard, QMouseEvent

from pygments.formatters import HtmlFormatter
from config import config
from ui.assets import create_cute_mascot_pixmap
from core.vault_reader import VaultReader

def format_markdown_html(text: str) -> str:
    """
    Converts markdown text to premium styled HTML for PyQt's rich text engine.
    Supports Pygments code highlighting, Obsidian callouts, wikilinks, task items, and styled tables.
    """
    if not text:
        return ""

    processed_text = text

    # 1. Auto-close code blocks if streaming text ends with an unclosed fence
    fence_count = processed_text.count("```")
    if fence_count % 2 != 0:
        processed_text += "\n```"

    # 2. Obsidian Callouts: > [!TYPE] Header
    def replace_callout(match):
        c_type = match.group(1).upper()
        c_title = match.group(2).strip() or c_type.capitalize()
        c_body = match.group(3).strip()
        icons = {
            "NOTE": "📝", "TIP": "💡", "WARNING": "⚠️",
            "IMPORTANT": "🔥", "INFO": "ℹ️", "CAUTION": "🛑", "SUCCESS": "✅"
        }
        icon = icons.get(c_type, "📌")
        return f'\n<div class="callout callout-{c_type.lower()}"><div class="callout-title">{icon} {c_title}</div><div class="callout-body">{c_body}</div></div>\n'

    processed_text = re.sub(
        r'>\s*\[!([A-Za-z]+)\]\s*([^\n]*)\n((?:>[^\n]*\n?)*)',
        lambda m: replace_callout(re.match(r'>\s*\[!([A-Za-z]+)\]\s*([^\n]*)\n?([\s\S]*)', m.group(0).replace('\n>', '\n'))),
        processed_text
    )

    # 3. Parse markdown with markdown2 (prior to wikilink span insertion so **bold** around wikilinks works)
    html = markdown2.markdown(
        processed_text,
        extras=["fenced-code-blocks", "tables", "strike", "cuddled-lists"]
    )

    # 4. Post-process Obsidian [[wikilinks]] -> <span class="wikilink">📄 Note Name</span>
    html = re.sub(r'\[\[(.*?)\]\]', r'<span class="wikilink">📄 \1</span>', html)

    # 5. Post-process task checkboxes
    html = re.sub(r'\[x\]', r'<span class="task-done">☑</span>', html)
    html = re.sub(r'\[ \]', r'<span class="task-todo">☐</span>', html)

    # 6. Enhance Tables for Qt Rich Text Engine
    html = re.sub(r'<table>', '<table border="1" cellpadding="6" cellspacing="0" class="md-table">', html)

    # 7. Pygments Nord Theme Stylesheet
    formatter = HtmlFormatter(style="nord")
    pygments_css = formatter.get_style_defs(".codehilite")

    styled_html = f"""
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #E2E8F0;
            line-height: 1.5;
            margin: 0;
            padding: 0;
        }}
        p {{ margin: 5px 0; }}
        h1, h2, h3, h4 {{ color: #F1F5F9; margin: 10px 0 4px 0; font-weight: 600; }}
        h1 {{ font-size: 15px; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 3px; color: #A78BFA; }}
        h2 {{ font-size: 14px; color: #CBD5E1; }}
        h3 {{ font-size: 13px; color: #38BDF8; }}
        h4 {{ font-size: 12.5px; color: #94A3B8; }}
        strong {{ color: #FFFFFF; font-weight: 600; }}
        em {{ color: #E2E8F0; font-style: italic; }}
        code {{
            background-color: rgba(15, 23, 42, 0.85);
            color: #38BDF8;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 11.5px;
        }}
        .codehilite {{
            background-color: #0B0F19 !important;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            margin: 8px 0;
            padding: 8px 10px;
        }}
        .codehilite pre {{
            background: transparent !important;
            margin: 0;
            padding: 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 11.5px;
            line-height: 1.45;
            color: #F8FAFC;
        }}
        ul, ol {{ margin: 5px 0; padding-left: 20px; }}
        li {{ margin-bottom: 3px; color: #E2E8F0; }}
        .wikilink {{
            color: #C084FC;
            background: rgba(139, 92, 246, 0.18);
            border: 1px solid rgba(167, 139, 250, 0.35);
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .task-done {{ color: #34D399; font-weight: bold; }}
        .task-todo {{ color: #94A3B8; font-weight: bold; }}
        .md-table {{
            border-collapse: collapse;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.12);
            margin: 8px 0;
            background: rgba(15, 23, 42, 0.55);
            font-size: 12px;
        }}
        .md-table th {{
            background: rgba(30, 41, 59, 0.9);
            color: #F8FAFC;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 6px 8px;
            text-align: left;
        }}
        .md-table td {{
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 5px 8px;
            color: #E2E8F0;
        }}
        .callout {{
            border-left: 3px solid #8B5CF6;
            background: rgba(139, 92, 246, 0.12);
            padding: 7px 10px;
            margin: 6px 0;
            border-radius: 6px;
        }}
        .callout-title {{
            color: #A78BFA;
            font-weight: 600;
            font-size: 11.5px;
            margin-bottom: 2px;
        }}
        .callout-body {{
            color: #CBD5E1;
            font-size: 12px;
            line-height: 1.4;
        }}
        .callout-tip {{ border-left-color: #10B981; background: rgba(16, 185, 129, 0.12); }}
        .callout-tip .callout-title {{ color: #34D399; }}
        .callout-warning {{ border-left-color: #F59E0B; background: rgba(245, 158, 11, 0.12); }}
        .callout-warning .callout-title {{ color: #FBBF24; }}
        .callout-important {{ border-left-color: #EC4899; background: rgba(236, 72, 153, 0.12); }}
        .callout-important .callout-title {{ color: #F472B6; }}
        .callout-info {{ border-left-color: #38BDF8; background: rgba(56, 189, 248, 0.12); }}
        .callout-info .callout-title {{ color: #38BDF8; }}
        .callout-caution {{ border-left-color: #EF4444; background: rgba(239, 68, 68, 0.12); }}
        .callout-caution .callout-title {{ color: #F87171; }}
        .callout-success {{ border-left-color: #34D399; background: rgba(52, 211, 153, 0.12); }}
        .callout-success .callout-title {{ color: #34D399; }}
        blockquote {{
            border-left: 3px solid #8B5CF6;
            background: rgba(139, 92, 246, 0.08);
            margin: 6px 0;
            padding: 6px 10px;
            border-radius: 4px;
            color: #CBD5E1;
        }}
        hr {{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 10px 0; }}
        {pygments_css}
    </style>
    <div>{html}</div>
    """
    return styled_html


class HeaderBar(QWidget):
    """Draggable header bar for the frameless chat window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self._drag_start_pos: Optional[QPoint] = None
        self._is_dragging = False
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            win = self.window()
            self._drag_start_pos = event.globalPosition().toPoint() - win.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_pos:
            win = self.window()
            win.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if hasattr(win, "toggle_maximize"):
                win.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            win = self.window()
            if hasattr(win, "_save_geometry"):
                win._save_geometry()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class MessageBubble(QFrame):
    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.raw_content = content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(6)

        if role == "user":
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4F46E5, stop:1 #7C3AED);
                    border-radius: 12px;
                    border-bottom-right-radius: 2px;
                }
            """)
            self.label = QLabel(content)
            self.label.setWordWrap(True)
            self.label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 500; background: transparent;")
            self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(self.label)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(30, 41, 59, 0.72);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    border-bottom-left-radius: 2px;
                }
            """)

            # Top bar with Assistant tag & Copy button
            top_bar = QHBoxLayout()
            top_bar.setContentsMargins(0, 0, 0, 0)
            top_bar.setSpacing(6)

            bot_tag = QLabel("🤖 Trợ lý")
            bot_tag.setStyleSheet("color: #A78BFA; font-size: 11px; font-weight: 600; background: transparent;")
            top_bar.addWidget(bot_tag)
            top_bar.addStretch()

            self.copy_btn = QPushButton("📋 Chép")
            self.copy_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(15, 23, 42, 0.6);
                    color: #94A3B8;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 4px;
                    padding: 1px 6px;
                    font-size: 10px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    color: #F8FAFC;
                    background: rgba(99, 102, 241, 0.35);
                    border-color: rgba(167, 139, 250, 0.4);
                }
            """)
            self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.copy_btn.setToolTip("Sao chép toàn bộ nội dung")
            self.copy_btn.clicked.connect(self._copy_content)
            top_bar.addWidget(self.copy_btn)
            layout.addLayout(top_bar)

            self.label = QLabel()
            self.label.setWordWrap(True)
            self.label.setStyleSheet("background: transparent;")
            self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
            self.label.setOpenExternalLinks(True)
            self.set_markdown(content)
            layout.addWidget(self.label)

    def _copy_content(self):
        clipboard = QApplication.clipboard()
        if clipboard and self.raw_content:
            clipboard.setText(self.raw_content)
            self.copy_btn.setText("✅ Đã chép")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 Chép"))

    def set_markdown(self, text: str):
        self.raw_content = text
        html = format_markdown_html(text)
        self.label.setText(html)


class ThinkingStepCard(QFrame):
    """Card representing an individual tool execution or reasoning step."""
    def __init__(self, tool_name: str, desc: str, details: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("ThinkingStepCard")
        self.tool_name = tool_name
        self.details = details or {}
        self._is_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        self.icon_label = QLabel("⚡")
        self.icon_label.setStyleSheet("font-size: 11.5px; background: transparent;")

        self.title_label = QLabel(desc or f"Thực thi {tool_name}")
        self.title_label.setStyleSheet("color: #E2E8F0; font-size: 11.5px; font-weight: 600; background: transparent;")

        self.duration_badge = QLabel("Đang chạy...")
        self.duration_badge.setStyleSheet("color: #FCD34D; font-size: 10.5px; background: rgba(245, 158, 11, 0.15); border-radius: 4px; padding: 1px 5px;")

        self.toggle_details_btn = QPushButton("▾")
        self.toggle_details_btn.setStyleSheet("background: transparent; color: #94A3B8; border: none; font-size: 11px; padding: 1px 4px;")
        self.toggle_details_btn.clicked.connect(self._toggle_details)

        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.duration_badge)
        header_layout.addWidget(self.toggle_details_btn)
        layout.addLayout(header_layout)

        # Details container (Parameters & Output)
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(0, 2, 0, 0)
        self.details_layout.setSpacing(4)

        # 1. Parameters block
        params = self.details.get("parameters", {})
        param_text = ""
        if isinstance(params, dict):
            if "CommandLine" in params:
                param_text = f"$ {params['CommandLine']}"
            elif "Query" in params or "query" in params:
                param_text = f"Query: {params.get('Query') or params.get('query')}"
            elif "DirectoryPath" in params or "SearchPath" in params or "TargetFile" in params:
                param_text = f"Path: {params.get('DirectoryPath') or params.get('SearchPath') or params.get('TargetFile')}"
            elif params:
                param_text = json.dumps(params, ensure_ascii=False, indent=2)

        if param_text:
            self.param_label = QLabel(param_text)
            self.param_label.setStyleSheet("""
                QLabel {
                    background: #0B0F19;
                    color: #38BDF8;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-family: 'JetBrains Mono', 'Fira Code', monospace;
                    font-size: 10.5px;
                }
            """)
            self.param_label.setWordWrap(True)
            self.param_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.details_layout.addWidget(self.param_label)

        # 2. Output preview block
        self.output_label = QLabel()
        self.output_label.setStyleSheet("""
            QLabel {
                background: #0B0F19;
                color: #CBD5E1;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 4px;
                padding: 4px 6px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 10px;
            }
        """)
        self.output_label.setWordWrap(True)
        self.output_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.output_label.setVisible(False)
        self.details_layout.addWidget(self.output_label)

        layout.addWidget(self.details_container)

    def _toggle_details(self):
        self._is_expanded = not self._is_expanded
        self.toggle_details_btn.setText("▸" if self._is_expanded else "▾")
        self.details_container.setVisible(not self._is_expanded)

    def update_finished(self, result_str: str, details: dict):
        status = details.get("status", "done")
        duration = float(details.get("duration", 0.0) or 0.0)

        if status == "error":
            self.icon_label.setText("❌")
            self.setStyleSheet("""
                QFrame#ThinkingStepCard {
                    background: rgba(239, 68, 68, 0.08);
                    border-left: 3px solid #EF4444;
                    border-radius: 6px;
                }
            """)
            self.duration_badge.setStyleSheet("color: #F87171; background: rgba(239, 68, 68, 0.15); border-radius: 4px; padding: 1px 5px;")
        else:
            self.icon_label.setText("✅")
            self.setStyleSheet("""
                QFrame#ThinkingStepCard {
                    background: rgba(16, 185, 129, 0.08);
                    border-left: 3px solid #10B981;
                    border-radius: 6px;
                }
            """)
            self.duration_badge.setStyleSheet("color: #34D399; background: rgba(16, 185, 129, 0.15); border-radius: 4px; padding: 1px 5px;")

        if duration > 0:
            self.duration_badge.setText(f"{duration:.2f}s")
        else:
            self.duration_badge.setText("Xong")

        if result_str:
            snippet = result_str.strip()
            if len(snippet) > 350:
                snippet = snippet[:350] + "\n... (kết quả dài, đã rút gọn)"
            self.output_label.setText(snippet)
            self.output_label.setVisible(True)


class ThinkingProcessWidget(QFrame):
    """Accordion container grouping reasoning tokens & tool execution cards."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ThinkingAccordion")
        self._is_collapsed = False
        self._start_time = time.time()
        self._total_steps = 0
        self._total_tokens = 0
        self._step_cards: List[ThinkingStepCard] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setObjectName("ThinkingHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(8)

        self.title_label = QLabel("🧠 Quá trình suy luận & Công cụ")
        self.title_label.setObjectName("ThinkingTitle")

        self.badge_label = QLabel("⚡ Đang xử lý...")
        self.badge_label.setObjectName("ThinkingBadge")

        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setObjectName("ThinkingToggleBtn")
        self.toggle_btn.setToolTip("Thu gọn / Mở rộng quá trình suy luận")
        self.toggle_btn.clicked.connect(self.toggle_collapsed)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.badge_label)
        header_layout.addWidget(self.toggle_btn)

        layout.addWidget(self.header)

        # Body container
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(8, 6, 8, 6)
        self.body_layout.setSpacing(6)
        layout.addWidget(self.body)

    def toggle_collapsed(self):
        self._is_collapsed = not self._is_collapsed
        self.toggle_btn.setText("▶" if self._is_collapsed else "▼")
        self.body.setVisible(not self._is_collapsed)

    def add_tool_started(self, tool_name: str, desc: str, details: dict):
        self._total_steps += 1
        card = ThinkingStepCard(tool_name, desc, details, self.body)
        self._step_cards.append(card)
        self.body_layout.addWidget(card)
        self.badge_label.setText(f"⚡ Bước {self._total_steps}: {tool_name}")
        self.badge_label.setStyleSheet("color: #FCD34D; background: rgba(245, 158, 11, 0.18); border-radius: 4px; padding: 2px 6px;")

    def update_tool_finished(self, tool_name: str, result_str: str, details: dict):
        if self._step_cards:
            for card in reversed(self._step_cards):
                if card.tool_name == tool_name:
                    card.update_finished(result_str, details)
                    break
            else:
                self._step_cards[-1].update_finished(result_str, details)

    def update_thinking_usage(self, data: dict):
        tokens = data.get("thinking_tokens", 0)
        if tokens:
            self._total_tokens = tokens

    def finalize(self):
        elapsed = round(time.time() - self._start_time, 1)
        token_info = f" • {self._total_tokens} tokens" if self._total_tokens else ""
        step_info = f"{self._total_steps} bước" if self._total_steps else "Hoàn thành"
def format_token_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


class ContextWindowMeter(QFrame):
    """
    Sleek Glassmorphic Context Window & Token Meter.
    Displays real-time tokens used, max context limit, breakdown (Input/Output/Thinking),
    and a color-coded percentage progress bar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContextWindowMeter")
        self._is_expanded = False
        self._context_limit = 1_048_576
        self._total_tokens = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._thinking_tokens = 0
        self._turn_count = 0
        self._model_name = config.model_name

        self.setStyleSheet("""
            QFrame#ContextWindowMeter {
                background: rgba(15, 23, 42, 0.75);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 0px;
                padding: 4px 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Top row: icon, mini progress bar, token ratio label, toggle details btn
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.setContentsMargins(0, 0, 0, 0)

        self.icon_lbl = QLabel("📊 Context")
        self.icon_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600; background: transparent;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(30, 41, 59, 0.85);
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #38BDF8);
                border-radius: 2px;
            }
        """)

        self.stats_lbl = QLabel("0 / 1.05M tokens (0.0%)")
        self.stats_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', 'Fira Code', monospace; background: transparent;")

        self.toggle_btn = QPushButton("▾")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                font-size: 10px;
                padding: 0 4px;
            }
            QPushButton:hover {
                color: #A78BFA;
            }
        """)
        self.toggle_btn.setToolTip("Xem chi tiết Input / Output / Thinking Tokens")
        self.toggle_btn.clicked.connect(self.toggle_details)

        top_row.addWidget(self.icon_lbl)
        top_row.addWidget(self.progress_bar, 1)
        top_row.addWidget(self.stats_lbl)
        top_row.addWidget(self.toggle_btn)
        layout.addLayout(top_row)

        # Details row (Breakdown pills)
        self.details_widget = QWidget()
        details_layout = QHBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 2, 0, 0)
        details_layout.setSpacing(6)

        self.pill_in = QLabel("📥 In: 0")
        self.pill_in.setStyleSheet("color: #38BDF8; background: rgba(56, 189, 248, 0.12); border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: 'JetBrains Mono', monospace;")

        self.pill_out = QLabel("📤 Out: 0")
        self.pill_out.setStyleSheet("color: #34D399; background: rgba(52, 211, 153, 0.12); border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: 'JetBrains Mono', monospace;")

        self.pill_think = QLabel("🧠 Think: 0")
        self.pill_think.setStyleSheet("color: #C084FC; background: rgba(192, 132, 252, 0.12); border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: 'JetBrains Mono', monospace;")

        self.pill_model = QLabel(f"🤖 {config.model_name}")
        self.pill_model.setStyleSheet("color: #94A3B8; background: rgba(148, 163, 184, 0.12); border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: 'JetBrains Mono', monospace;")

        details_layout.addWidget(self.pill_in)
        details_layout.addWidget(self.pill_out)
        details_layout.addWidget(self.pill_think)
        details_layout.addStretch()
        details_layout.addWidget(self.pill_model)

        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)

    def toggle_details(self):
        self._is_expanded = not self._is_expanded
        self.toggle_btn.setText("▴" if self._is_expanded else "▾")
        self.details_widget.setVisible(self._is_expanded)

    def update_usage(self, data: dict):
        if not isinstance(data, dict):
            return

        self._model_name = data.get("model_name") or self._model_name
        self._context_limit = data.get("context_limit") or self._context_limit
        self._input_tokens = data.get("input_tokens", 0)
        self._output_tokens = data.get("output_tokens", 0)
        self._thinking_tokens = data.get("thinking_tokens", 0)
        self._total_tokens = data.get("total_tokens", 0) or (self._input_tokens + self._output_tokens + self._thinking_tokens)
        self._turn_count = data.get("turn_count", 1)

        pct = (self._total_tokens / max(1, self._context_limit)) * 100
        val = min(1000, int(pct * 10))
        self.progress_bar.setValue(val)

        if pct < 50:
            chunk_color = "stop:0 #10B981, stop:1 #38BDF8"
            text_color = "#38BDF8"
        elif pct < 80:
            chunk_color = "stop:0 #F59E0B, stop:1 #FCD34D"
            text_color = "#FCD34D"
        else:
            chunk_color = "stop:0 #EF4444, stop:1 #F87171"
            text_color = "#F87171"

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(30, 41, 59, 0.85);
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {chunk_color});
                border-radius: 2px;
            }}
        """)

        used_str = format_token_count(self._total_tokens)
        limit_str = format_token_count(self._context_limit)
        self.stats_lbl.setText(f"{used_str} / {limit_str} ({pct:.1f}%)")
        self.stats_lbl.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', 'Fira Code', monospace; background: transparent;")

        self.pill_in.setText(f"📥 In: {format_token_count(self._input_tokens)}")
        self.pill_out.setText(f"📤 Out: {format_token_count(self._output_tokens)}")
        self.pill_think.setText(f"🧠 Think: {format_token_count(self._thinking_tokens)}")
        short_model = self._model_name.split("/")[-1]
        self.pill_model.setText(f"🤖 {short_model}")

        remaining = max(0, self._context_limit - self._total_tokens)
        self.setToolTip(
            f"📊 Context Window Status:\n"
            f"• Đã dùng: {self._total_tokens:,} / {self._context_limit:,} tokens ({pct:.2f}%)\n"
            f"• Còn trống: {remaining:,} tokens\n"
            f"• Input: {self._input_tokens:,} tokens\n"
            f"• Output: {self._output_tokens:,} tokens\n"
            f"• Thinking: {self._thinking_tokens:,} tokens\n"
            f"• Model: {self._model_name}"
        )

    def reset(self):
        self._total_tokens = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._thinking_tokens = 0
        self.progress_bar.setValue(0)
        limit_str = format_token_count(self._context_limit)
        self.stats_lbl.setText(f"0 / {limit_str} (0.0%)")
        self.stats_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', 'Fira Code', monospace; background: transparent;")
        self.pill_in.setText("📥 In: 0")
        self.pill_out.setText("📤 Out: 0")
        self.pill_think.setText("🧠 Think: 0")


class ChatPanel(QWidget):
    message_sent = pyqtSignal(str)
    request_minimize = pyqtSignal()
    request_settings = pyqtSignal()
    request_close = pyqtSignal()
    request_pin = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_assistant_bubble: Optional[MessageBubble] = None
        self._current_thinking_widget: Optional[ThinkingProcessWidget] = None
        self._current_assistant_text = ""
        self._is_pinned = config.always_on_top

        self._setup_ui()
        self._load_welcome_message()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar (Draggable)
        header = HeaderBar(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(8)

        # Avatar (transparent to mouse events so clicks drag header)
        avatar_lbl = QLabel()
        avatar_lbl.setPixmap(create_cute_mascot_pixmap(26, glow=False))
        avatar_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(avatar_lbl)

        # Titles (transparent to mouse events)
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)
        
        self.title_label = QLabel("Second Brain Companion")
        self.title_label.setObjectName("HeaderTitle")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.subtitle_label = QLabel("Obsidian Connected 🟢")
        self.subtitle_label.setObjectName("HeaderSubtitle")
        self.subtitle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        title_vbox.addWidget(self.title_label)
        title_vbox.addWidget(self.subtitle_label)
        header_layout.addLayout(title_vbox)

        header_layout.addStretch()

        # Header Buttons
        self.thinking_btn = QPushButton("🧠")
        self.thinking_btn.setProperty("class", "HeaderBtn")
        self._update_thinking_btn_style()
        self.thinking_btn.clicked.connect(self._toggle_thinking)

        self.pin_btn = QPushButton("📌" if self._is_pinned else "📍")
        self.pin_btn.setProperty("class", "HeaderBtn")
        self.pin_btn.setToolTip("Ghim luôn nổi trên màn hình")
        self.pin_btn.clicked.connect(self._toggle_pin)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setProperty("class", "HeaderBtn")
        self.settings_btn.setToolTip("Cài đặt")
        self.settings_btn.clicked.connect(self.request_settings.emit)

        self.min_btn = QPushButton("➖")
        self.min_btn.setProperty("class", "HeaderBtn")
        self.min_btn.setToolTip("Thu nhỏ thành Mascot tròn (hoặc phím tắt)")
        self.min_btn.clicked.connect(self.request_minimize.emit)

        self.max_btn = QPushButton("🗖")
        self.max_btn.setProperty("class", "HeaderBtn")
        self.max_btn.setToolTip("Phóng to / Khôi phục kích thước (hoặc Double-click Header)")
        self.max_btn.clicked.connect(self._toggle_maximize_window)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setProperty("class", "HeaderBtn")
        self.close_btn.setToolTip("Ẩn / Đóng")
        self.close_btn.clicked.connect(self.request_close.emit)

        for btn in (self.thinking_btn, self.pin_btn, self.settings_btn, self.min_btn, self.max_btn, self.close_btn):
            header_layout.addWidget(btn)

        main_layout.addWidget(header)

        # 2. Quick Action Pills
        pills_container = QWidget()
        pills_container.setStyleSheet("background: transparent; padding: 4px 10px;")
        pills_layout = QHBoxLayout(pills_container)
        pills_layout.setContentsMargins(4, 4, 4, 4)
        pills_layout.setSpacing(6)

        pill_daily = QPushButton("📝 Daily Log")
        pill_daily.setProperty("class", "ActionPill")
        pill_daily.clicked.connect(lambda: self._quick_prompt("Ghi nhật ký hôm nay: "))

        pill_idea = QPushButton("💡 Ý tưởng")
        pill_idea.setProperty("class", "ActionPill")
        pill_idea.clicked.connect(lambda: self._quick_prompt("Tạo ghi chú ý tưởng mới: "))

        pill_task = QPushButton("✅ Thêm Todo")
        pill_task.setProperty("class", "ActionPill")
        pill_task.clicked.connect(lambda: self._quick_prompt("Thêm việc cần làm: "))

        pill_search = QPushButton("🔍 Tìm kiếm")
        pill_search.setProperty("class", "ActionPill")
        pill_search.clicked.connect(lambda: self._quick_prompt("Tìm trong Vault kiến thức về: "))

        for p in (pill_daily, pill_idea, pill_task, pill_search):
            pills_layout.addWidget(p)
        pills_layout.addStretch()

        main_layout.addWidget(pills_container)

        # 3. Chat Messages Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ChatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_content = QWidget()
        self.chat_content.setObjectName("ChatContentWidget")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(12, 6, 12, 6)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_content)
        main_layout.addWidget(self.scroll_area, 1)

        # 4. Context Window & Token Usage Meter
        self.context_meter = ContextWindowMeter(self)
        main_layout.addWidget(self.context_meter)

        # 5. Input Area
        input_container = QWidget()
        input_container.setObjectName("InputContainer")
        input_vbox = QVBoxLayout(input_container)
        input_vbox.setContentsMargins(8, 6, 8, 6)
        input_vbox.setSpacing(4)

        self.prompt_input = QTextEdit()
        self.prompt_input.setObjectName("PromptInput")
        self.prompt_input.setPlaceholderText("Nhập tin nhắn... (Enter để gửi, Shift+Enter xuống dòng)")
        self.prompt_input.setFixedHeight(54)
        self.prompt_input.installEventFilter(self)

        input_bottom_layout = QHBoxLayout()
        input_bottom_layout.setSpacing(6)

        clear_btn = QPushButton("🗑️")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #F87171;
                background: rgba(239, 68, 68, 0.1);
            }
        """)
        clear_btn.setToolTip("Xóa khung chat")
        clear_btn.clicked.connect(self.clear_chat)
        input_bottom_layout.addWidget(clear_btn)

        input_bottom_layout.addStretch()

        self.send_btn = QPushButton("Gửi ✨")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._handle_send)
        input_bottom_layout.addWidget(self.send_btn)

        input_vbox.addWidget(self.prompt_input)
        input_vbox.addLayout(input_bottom_layout)

        main_layout.addWidget(input_container)

        self.refresh_vault_status()

    def _update_thinking_btn_style(self):
        is_on = config.show_thinking
        self.thinking_btn.setToolTip("Thinking & Tool: BẬT (Click để TẮT)" if is_on else "Thinking & Tool: TẮT (Click để BẬT)")
        self.thinking_btn.setStyleSheet("color: #A78BFA;" if is_on else "color: #64748B;")

    def _toggle_thinking(self):
        new_val = not config.show_thinking
        config.set("show_thinking", new_val)
        self._update_thinking_btn_style()

    def refresh_vault_status(self):
        reader = VaultReader(config.vault_path)
        if reader.is_valid():
            overview = reader.get_structure_overview()
            total = overview.get("total_notes", 0)
            self.subtitle_label.setText(f"Obsidian Connected • {total} notes 🟢")
            self.subtitle_label.setStyleSheet("color: #34D399; font-size: 11px;")
        else:
            self.subtitle_label.setText("Vault Chưa Kết Nối ⚠️")
            self.subtitle_label.setStyleSheet("color: #FBBF24; font-size: 11px;")

    def _load_welcome_message(self):
        welcome_text = (
            "Xin chào! Mình là **Second Brain Companion** 🤖✨\n\n"
            "Mình luôn sẵn sàng giúp bạn:\n"
            "- 📝 **Ghi nhanh Daily Note** & Nhật ký\n"
            "- 💡 **Lưu trữ Ý tưởng & Kiến thức** vào Obsidian\n"
            "- ✅ **Quản lý Todo** & Công việc\n"
            "- 🔍 **Truy vấn kiến thức** từ Second Brain của bạn\n\n"
            "*Hãy gõ nội dung hoặc dùng các phím tắt bên trên nhé!*"
        )
        self.append_assistant_message(welcome_text)

    def _quick_prompt(self, prefix: str):
        self.prompt_input.setText(prefix)
        self.prompt_input.setFocus()
        cursor = self.prompt_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.prompt_input.setTextCursor(cursor)

    def _toggle_pin(self):
        self._is_pinned = not self._is_pinned
        self.pin_btn.setText("📌" if self._is_pinned else "📍")
        self.pin_btn.setStyleSheet("color: #A78BFA;" if self._is_pinned else "color: #94A3B8;")
        self.request_pin.emit(self._is_pinned)

    def _toggle_maximize_window(self):
        win = self.window()
        if hasattr(win, "toggle_maximize"):
            win.toggle_maximize()

    def eventFilter(self, obj, event):
        if obj == self.prompt_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.request_minimize.emit()
                return True
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._handle_send()
                    return True
        return super().eventFilter(obj, event)

    def _handle_send(self):
        text = self.prompt_input.toPlainText().strip()
        if not text:
            return

        self.prompt_input.clear()
        self.append_user_message(text)
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳ Đang nghĩ...")

        # Create new assistant response container
        self._start_assistant_streaming()
        self.message_sent.emit(text)

    def append_user_message(self, text: str):
        bubble = MessageBubble("user", text)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def append_assistant_message(self, text: str):
        bubble = MessageBubble("assistant", text)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _start_assistant_streaming(self):
        self._current_assistant_text = ""
        self._current_thinking_widget = None
        self._current_assistant_bubble = MessageBubble("assistant", "...")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._current_assistant_bubble)
        self._scroll_to_bottom()

    def on_tool_started(self, tool_name: str, desc: str, details: Any = None):
        if config.show_thinking:
            if self._current_thinking_widget is None:
                self._current_thinking_widget = ThinkingProcessWidget()
                # Insert thinking accordion before assistant bubble
                if self._current_assistant_bubble:
                    idx = self.chat_layout.indexOf(self._current_assistant_bubble)
                    self.chat_layout.insertWidget(max(0, idx), self._current_thinking_widget)
                else:
                    self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._current_thinking_widget)

            self._current_thinking_widget.add_tool_started(tool_name, desc, details if isinstance(details, dict) else {})
        self._scroll_to_bottom()

    def on_tool_finished(self, tool_name: str, result_str: str, details: Any = None):
        if self._current_thinking_widget:
            self._current_thinking_widget.update_tool_finished(tool_name, result_str, details if isinstance(details, dict) else {})
        self.refresh_vault_status()
        self._scroll_to_bottom()

    def on_thinking_updated(self, data: Any):
        if self._current_thinking_widget and isinstance(data, dict):
            self._current_thinking_widget.update_thinking_usage(data)

    def on_token_usage_updated(self, data: Any):
        if isinstance(data, dict):
            self.context_meter.update_usage(data)

    def on_chunk_received(self, chunk: str):
        self._current_assistant_text += chunk
        if self._current_assistant_bubble:
            self._current_assistant_bubble.set_markdown(self._current_assistant_text)
            self._scroll_to_bottom()

    def on_response_finished(self, full_text: str):
        if self._current_thinking_widget:
            self._current_thinking_widget.finalize()
            self._current_thinking_widget = None

        if self._current_assistant_bubble and full_text:
            self._current_assistant_bubble.set_markdown(full_text)

        self.send_btn.setEnabled(True)
        self.send_btn.setText("Gửi ✨")
        self._scroll_to_bottom()

    def on_error(self, error_msg: str):
        if self._current_thinking_widget:
            self._current_thinking_widget.finalize()
            self._current_thinking_widget = None

        if self._current_assistant_bubble:
            self._current_assistant_bubble.set_markdown(error_msg)
        else:
            self.append_assistant_message(error_msg)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Gửi ✨")
        self._scroll_to_bottom()

    def clear_chat(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._current_thinking_widget = None
        self._current_assistant_bubble = None
        self.context_meter.reset()
        self._load_welcome_message()

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
