"""
Settings Dialog for Second Brain AI Companion.
Allows configuring AI Engine, Models, Obsidian Vault, Hotkeys, and Proactive Cadence Settings.
Features Resizable Window, Smooth Scroll Areas, and Clean Modern Layout.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QCheckBox, QFrame,
    QRadioButton, QButtonGroup, QTabWidget, QWidget, QGridLayout,
    QSpinBox, QScrollArea, QSizeGrip
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from config import config

MODELS_AGY = [
    ("gemini-3.8-flash-medium", "Gemini 3.8 Flash (Medium) ⭐ Mới & Khuyên Dùng"),
    ("gemini-3.8-flash-high", "Gemini 3.8 Flash (High - Suy luận cao nhất)"),
    ("gemini-3.8-flash-low", "Gemini 3.8 Flash (Low - Siêu nhanh)"),
    ("gemini-3.7-flash-medium", "Gemini 3.7 Flash (Medium)"),
    ("gemini-3.7-flash-high", "Gemini 3.7 Flash (High)"),
    ("gemini-3.7-flash-low", "Gemini 3.7 Flash (Low)"),
    ("gemini-3.1-pro-high", "Gemini 3.1 Pro (High)"),
    ("claude-sonnet-4-6", "Claude Sonnet 4.6 (Thinking)"),
    ("claude-opus-4-6-thinking", "Claude Opus 4.6 (Thinking)"),
    ("gpt-oss-120b-medium", "GPT-OSS 120B (Medium)")
]

MODELS_API = [
    ("gemini-2.5-flash", "Gemini 2.5 Flash"),
    ("gemini-1.5-flash", "Gemini 1.5 Flash"),
    ("gemini-1.5-pro", "Gemini 1.5 Pro")
]

MORNING_TIME_OPTIONS = [
    "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00"
]

EVENING_TIME_OPTIONS = [
    "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"
]

DISMISS_OPTIONS = [
    (8, "8 giây (Nhanh)"),
    (12, "12 giây"),
    (15, "15 giây (Mặc định)"),
    (25, "25 giây"),
    (40, "40 giây"),
    (0, "Không tự đóng (Đợi click)"),
]

SPACED_MIN_AGE_OPTIONS = [
    (0, "Mọi ghi chú (Kể cả vừa viết hôm nay)"),
    (1, "Từ 1 ngày trước trở lên"),
    (2, "Từ 2 ngày trước trở lên"),
    (3, "Từ 3 ngày trước trở lên"),
    (7, "Từ 1 tuần trước trở lên"),
    (14, "Từ 2 tuần trước trở lên"),
    (30, "Từ 1 tháng trước trở lên"),
]

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cài Đặt Second Brain Companion")
        
        # Cho phép co giãn kích thước tự do và nhớ kích thước trước đó nếu có
        init_w = int(config.get("settings_win_w", 620))
        init_h = int(config.get("settings_win_h", 680))
        self.resize(init_w, init_h)
        self.setMinimumSize(520, 480)
        self.setSizeGripEnabled(True)

        # Cờ cửa sổ chuẩn Dialog, hỗ trợ Maximize / Resize và luôn nổi trên cùng (WindowStaysOnTopHint)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(True)

        # Căn giữa cửa sổ trên màn hình hiển thị
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            cx = geo.x() + (geo.width() - init_w) // 2
            cy = geo.y() + (geo.height() - init_h) // 2
            self.move(max(20, cx), max(20, cy))

        self.setStyleSheet("""
            QDialog {
                background: #141724;
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QLabel {
                color: #E2E8F0;
                font-size: 12.5px;
                font-weight: 500;
            }
            QLabel.section-desc {
                color: #94A3B8;
                font-size: 11.5px;
                font-weight: normal;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #0D111D;
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #8B5CF6;
                background: #111627;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #1E2436;
                border: none;
                width: 18px;
                border-radius: 3px;
                margin: 1px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #6366F1;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #181D2E;
                color: #F8FAFC;
                selection-background-color: #6366F1;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background: #2D3748;
                color: #F8FAFC;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12.5px;
            }
            QPushButton:hover {
                background: #4A5568;
            }
            QPushButton.preset-pill {
                background: rgba(99, 102, 241, 0.15);
                color: #A5B4FC;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11.5px;
                font-weight: 600;
            }
            QPushButton.preset-pill:hover {
                background: #6366F1;
                color: white;
            }
            QPushButton#SaveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                color: white;
                padding: 8px 20px;
            }
            QPushButton#SaveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
            }
            QRadioButton {
                color: #CBD5E1;
                font-size: 12.5px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox {
                color: #CBD5E1;
                font-size: 12.5px;
                spacing: 8px;
            }
            QCheckBox:disabled {
                color: #64748B;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: #181C2B;
                border-radius: 10px;
                top: -1px;
            }
            QTabBar::tab {
                background: #1B2032;
                color: #94A3B8;
                padding: 9px 22px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 12.5px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #181C2B;
                color: #A78BFA;
                border-top: 2px solid #8B5CF6;
                border-left: 1px solid rgba(255, 255, 255, 0.12);
                border-right: 1px solid rgba(255, 255, 255, 0.12);
            }
            QTabBar::tab:hover:!selected {
                background: #242B42;
                color: #E2E8F0;
            }
            QFrame#CardFrame {
                background: rgba(13, 17, 29, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 12px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(139, 92, 246, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header Title
        title_label = QLabel("⚙️ Cài Đặt Second Brain Companion")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #A78BFA; padding-bottom: 2px;")
        layout.addWidget(title_label)

        # Tabs
        self.tabs = QTabWidget()
        
        # Setup Tab 1 in ScrollArea
        self.tab_system = QWidget()
        self._setup_system_tab()
        self.scroll_system = self._create_scroll_area(self.tab_system)

        # Setup Tab 2 in ScrollArea
        self.tab_proactive = QWidget()
        self._setup_proactive_tab()
        self.scroll_proactive = self._create_scroll_area(self.tab_proactive)

        self.tabs.addTab(self.scroll_system, "🧠 AI & Hệ Thống")
        self.tabs.addTab(self.scroll_proactive, "✨ Trợ Lý Chủ Động")
        layout.addWidget(self.tabs, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Lưu Cài Đặt")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _create_scroll_area(self, content_widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_widget.setStyleSheet("background: transparent;")
        scroll.setWidget(content_widget)
        return scroll

    def _setup_system_tab(self):
        layout = QVBoxLayout(self.tab_system)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)

        # Card 1: AI Engine & Model
        engine_card = QFrame()
        engine_card.setObjectName("CardFrame")
        ec_layout = QVBoxLayout(engine_card)
        ec_layout.setSpacing(10)

        ec_header = QLabel("🚀 AI Engine & Model:")
        ec_header.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        ec_layout.addWidget(ec_header)

        self.radio_agy = QRadioButton("Antigravity (AGY CLI) — Nhiều quota, Gemini 3.8 / Claude")
        self.radio_api = QRadioButton("Gemini API Key Trực Tiếp")
        
        self.engine_group = QButtonGroup(self)
        self.engine_group.addButton(self.radio_agy, 1)
        self.engine_group.addButton(self.radio_api, 2)

        if config.engine == "agy":
            self.radio_agy.setChecked(True)
        else:
            self.radio_api.setChecked(True)

        self.radio_agy.toggled.connect(self._on_engine_changed)
        ec_layout.addWidget(self.radio_agy)
        ec_layout.addWidget(self.radio_api)

        ec_layout.addWidget(QLabel("Mô hình AI (Model):"))
        self.model_combo = QComboBox()
        self._populate_models()
        ec_layout.addWidget(self.model_combo)

        self.key_label = QLabel("🔑 Gemini API Key (Tùy chọn nếu dùng AGY):")
        ec_layout.addWidget(self.key_label)
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("AIzaSy... (Không bắt buộc khi dùng AGY)")
        self.key_input.setText(config.gemini_api_key)
        ec_layout.addWidget(self.key_input)

        layout.addWidget(engine_card)

        # Card 2: Obsidian Vault & Phím tắt
        vault_card = QFrame()
        vault_card.setObjectName("CardFrame")
        vc_layout = QVBoxLayout(vault_card)
        vc_layout.setSpacing(10)

        vc_header = QLabel("📁 Obsidian Second Brain & Phím Tắt:")
        vc_header.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        vc_layout.addWidget(vc_header)

        vc_layout.addWidget(QLabel("Thư mục Obsidian Vault:"))
        vault_layout = QHBoxLayout()
        vault_layout.setSpacing(8)
        self.vault_input = QLineEdit()
        self.vault_input.setText(str(config.vault_path))
        browse_btn = QPushButton("Chọn...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_layout.addWidget(self.vault_input)
        vault_layout.addWidget(browse_btn)
        vc_layout.addLayout(vault_layout)

        vc_layout.addWidget(QLabel("Phím tắt toàn hệ thống (Global Hotkey):"))
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setText(config.hotkey)
        self.hotkey_input.setPlaceholderText("<ctrl>+<shift>+s")
        vc_layout.addWidget(self.hotkey_input)

        layout.addWidget(vault_card)

        # Card 3: Hiển thị & Hành vi
        display_card = QFrame()
        display_card.setObjectName("CardFrame")
        dc_layout = QVBoxLayout(display_card)
        dc_layout.setSpacing(8)

        dc_header = QLabel("📌 Tùy Chọn Cửa Sổ:")
        dc_header.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        dc_layout.addWidget(dc_header)

        self.ontop_cb = QCheckBox("Luôn nổi trên các cửa sổ khác (Always on Top)")
        self.ontop_cb.setChecked(config.always_on_top)
        dc_layout.addWidget(self.ontop_cb)

        self.thinking_cb = QCheckBox("Hiển thị chi tiết quá trình suy luận & gọi công cụ (Thinking & Tools)")
        self.thinking_cb.setChecked(config.show_thinking)
        dc_layout.addWidget(self.thinking_cb)

        layout.addWidget(display_card)
        layout.addStretch()

    def _setup_proactive_tab(self):
        layout = QVBoxLayout(self.tab_proactive)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)

        # Master Switch
        master_box = QHBoxLayout()
        self.proactive_cb = QCheckBox("Bật trợ lý chủ động nói chuyện (Proactive Companion)")
        self.proactive_cb.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #38BDF8;")
        self.proactive_cb.setChecked(config.proactive_enabled)
        master_box.addWidget(self.proactive_cb)
        layout.addLayout(master_box)

        desc_label = QLabel("Agent sẽ tự động quan sát thời gian và ghi chú trong Second Brain để đưa ra gợi ý ôn tập, điểm tin công việc và nhật ký một cách tự nhiên.")
        desc_label.setProperty("class", "section-desc")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #94A3B8; font-size: 11.5px;")
        layout.addWidget(desc_label)

        # Sub-settings container widget
        self.sub_settings_container = QWidget()
        sub_layout = QVBoxLayout(self.sub_settings_container)
        sub_layout.setContentsMargins(0, 4, 0, 0)
        sub_layout.setSpacing(12)

        # Card 1: Các loại gợi ý
        type_card = QFrame()
        type_card.setObjectName("CardFrame")
        type_layout = QVBoxLayout(type_card)
        type_layout.setSpacing(10)

        type_header = QLabel("📌 Các hoạt động chủ động:")
        type_header.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        type_layout.addWidget(type_header)

        self.morning_cb = QCheckBox("☀️ Chào buổi sáng & Điểm tin việc tồn (Morning Briefing)")
        self.morning_cb.setChecked(config.morning_briefing)
        type_layout.addWidget(self.morning_cb)

        self.spaced_cb = QCheckBox("💡 Ôn tập kiến thức ngẫu nhiên từ Vault (Spaced Repetition)")
        self.spaced_cb.setChecked(config.spaced_repetition)
        type_layout.addWidget(self.spaced_cb)

        self.evening_cb = QCheckBox("🌙 Tổng kết cuối ngày & Nhắc viết nhật ký (Evening Reflection)")
        self.evening_cb.setChecked(config.evening_reflection)
        type_layout.addWidget(self.evening_cb)

        sub_layout.addWidget(type_card)

        # Card 2: Cài đặt thời gian & tần suất
        time_card = QFrame()
        time_card.setObjectName("CardFrame")
        grid = QGridLayout(time_card)
        grid.setSpacing(12)
        grid.setContentsMargins(12, 12, 12, 12)

        # Interval SpinBox + Preset Pills
        grid.addWidget(QLabel("⏱️ Chu kỳ ôn tập kiến thức:"), 0, 0)
        interval_box = QHBoxLayout()
        interval_box.setSpacing(6)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)  # 1 phút tới 24 tiếng (1440 phút)
        self.interval_spin.setSuffix(" phút")
        cur_interval = max(1, config.proactive_interval_min)
        self.interval_spin.setValue(cur_interval)
        self.interval_spin.setFixedWidth(110)
        interval_box.addWidget(self.interval_spin)

        # Quick preset buttons
        presets = [("1m", 1), ("5m", 5), ("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120)]
        for label, val in presets:
            pill_btn = QPushButton(label)
            pill_btn.setProperty("class", "preset-pill")
            pill_btn.setFixedHeight(28)
            pill_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pill_btn.setToolTip(f"Đặt nhanh {label} ({val} phút)")
            pill_btn.clicked.connect(lambda checked=False, m=val: self.interval_spin.setValue(m))
            interval_box.addWidget(pill_btn)

        interval_box.addStretch()
        grid.addLayout(interval_box, 0, 1)

        # Spaced repetition minimum note age
        grid.addWidget(QLabel("📅 Độ tuổi ghi chú tối thiểu:"), 1, 0)
        self.spaced_age_combo = QComboBox()
        cur_age = config.spaced_min_age_days
        selected_age_idx = 0
        for i, (val, text) in enumerate(SPACED_MIN_AGE_OPTIONS):
            self.spaced_age_combo.addItem(text, val)
            if val == cur_age:
                selected_age_idx = i
        self.spaced_age_combo.setCurrentIndex(selected_age_idx)
        grid.addWidget(self.spaced_age_combo, 1, 1)

        # Morning time
        grid.addWidget(QLabel("☀️ Giờ bắt đầu nhắc sáng:"), 2, 0)
        self.morning_time_combo = QComboBox()
        cur_morning = config.morning_time
        for t in MORNING_TIME_OPTIONS:
            self.morning_time_combo.addItem(t, t)
        m_idx = self.morning_time_combo.findText(cur_morning)
        self.morning_time_combo.setCurrentIndex(m_idx if m_idx >= 0 else 4) # Default 08:00
        grid.addWidget(self.morning_time_combo, 2, 1)

        # Evening time
        grid.addWidget(QLabel("🌙 Giờ bắt đầu nhắc tối:"), 3, 0)
        self.evening_time_combo = QComboBox()
        cur_evening = config.evening_time
        for t in EVENING_TIME_OPTIONS:
            self.evening_time_combo.addItem(t, t)
        e_idx = self.evening_time_combo.findText(cur_evening)
        self.evening_time_combo.setCurrentIndex(e_idx if e_idx >= 0 else 2) # Default 18:00
        grid.addWidget(self.evening_time_combo, 3, 1)

        # Bubble dismiss duration
        grid.addWidget(QLabel("⏳ Thời gian tự ẩn bong bóng:"), 4, 0)
        self.dismiss_combo = QComboBox()
        cur_dismiss = config.bubble_dismiss_sec
        selected_dismiss_idx = 2
        for i, (val, text) in enumerate(DISMISS_OPTIONS):
            self.dismiss_combo.addItem(text, val)
            if val == cur_dismiss:
                selected_dismiss_idx = i
        self.dismiss_combo.setCurrentIndex(selected_dismiss_idx)
        grid.addWidget(self.dismiss_combo, 4, 1)

        sub_layout.addWidget(time_card)
        sub_layout.addStretch()

        layout.addWidget(self.sub_settings_container)

        # Toggle sub-settings enabled status based on master switch
        self.proactive_cb.toggled.connect(self.sub_settings_container.setEnabled)
        self.sub_settings_container.setEnabled(config.proactive_enabled)

    def _on_engine_changed(self):
        self._populate_models()

    def _populate_models(self):
        self.model_combo.clear()
        current_model = config.model_name
        is_agy = self.radio_agy.isChecked()
        model_list = MODELS_AGY if is_agy else MODELS_API

        selected_idx = 0
        for i, (m_id, m_label) in enumerate(model_list):
            self.model_combo.addItem(m_label, m_id)
            if m_id == current_model or m_id in current_model:
                selected_idx = i

        self.model_combo.setCurrentIndex(selected_idx)

    def _browse_vault(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn Thư mục Obsidian Vault", str(config.vault_path))
        if dir_path:
            self.vault_input.setText(dir_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ghi nhớ kích thước cửa sổ người dùng kéo giãn
        config.set("settings_win_w", self.width())
        config.set("settings_win_h", self.height())

    def _save(self):
        engine = "agy" if self.radio_agy.isChecked() else "gemini_api"
        model_name = self.model_combo.currentData() or "gemini-3.8-flash-medium"

        # System Settings
        config.set("engine", engine)
        config.set("model_name", model_name)
        config.set("gemini_api_key", self.key_input.text().strip())
        config.set("vault_path", self.vault_input.text().strip())
        config.set("hotkey", self.hotkey_input.text().strip())
        config.set("always_on_top", self.ontop_cb.isChecked())
        config.set("show_thinking", self.thinking_cb.isChecked())

        # Proactive Settings
        config.set("proactive_enabled", self.proactive_cb.isChecked())
        config.set("morning_briefing", self.morning_cb.isChecked())
        config.set("spaced_repetition", self.spaced_cb.isChecked())
        config.set("evening_reflection", self.evening_cb.isChecked())
        
        # Proactive Interval (Free choice from 1 min to 1440 min)
        config.set("proactive_interval_min", int(self.interval_spin.value()))

        # Spaced min age days
        spaced_age_val = self.spaced_age_combo.currentData()
        if spaced_age_val is not None:
            config.set("spaced_min_age_days", int(spaced_age_val))

        config.set("morning_time", self.morning_time_combo.currentText())
        config.set("evening_time", self.evening_time_combo.currentText())

        dismiss_val = self.dismiss_combo.currentData()
        if dismiss_val is not None:
            config.set("bubble_dismiss_sec", int(dismiss_val))

        # Lưu lại kích thước hiện tại
        config.set("settings_win_w", self.width())
        config.set("settings_win_h", self.height())

        self.settings_saved.emit()
        self.accept()
