"""
Settings Dialog for Second Brain AI Companion.
Allows configuring AI Engine (AGY vs Gemini API), Models (Gemini 3.7 / Claude), Vault Directory, and Hotkeys.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QCheckBox, QFrame, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
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

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cài Đặt Second Brain Companion")
        self.setFixedWidth(480)
        self.setStyleSheet("""
            QDialog {
                background: #181B26;
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
            QLabel {
                color: #E2E8F0;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QComboBox {
                background: #0F172A;
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 12.5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #8B5CF6;
            }
            QPushButton {
                background: #334155;
                color: #F8FAFC;
                border: none;
                border-radius: 8px;
                padding: 7px 14px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #475569;
            }
            QPushButton#SaveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                color: white;
            }
            QPushButton#SaveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
            }
            QRadioButton {
                color: #CBD5E1;
                font-size: 12px;
                font-weight: 600;
            }
            QCheckBox {
                color: #CBD5E1;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("✨ Cấu Hình AI Engine & Obsidian Second Brain")
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #A78BFA;")
        layout.addWidget(title_label)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: rgba(255,255,255,0.1); max-height: 1px;")
        layout.addWidget(line)

        # 1. Engine Choice
        layout.addWidget(QLabel("🚀 Chọn AI Engine:"))
        engine_layout = QHBoxLayout()
        self.radio_agy = QRadioButton("Antigravity (AGY CLI) — Nhiều quota, Gemini 3.7")
        self.radio_api = QRadioButton("Gemini API Key Trực Tiếp")
        
        self.engine_group = QButtonGroup(self)
        self.engine_group.addButton(self.radio_agy, 1)
        self.engine_group.addButton(self.radio_api, 2)

        if config.engine == "agy":
            self.radio_agy.setChecked(True)
        else:
            self.radio_api.setChecked(True)

        self.radio_agy.toggled.connect(self._on_engine_changed)
        engine_layout.addWidget(self.radio_agy)
        layout.addLayout(engine_layout)
        layout.addWidget(self.radio_api)

        # 2. Model Selection
        layout.addWidget(QLabel("🧠 Mô hình AI (Model):"))
        self.model_combo = QComboBox()
        self._populate_models()
        layout.addWidget(self.model_combo)

        # 3. Gemini API Key (Visible if API chosen)
        self.key_label = QLabel("🔑 Gemini API Key (Tùy chọn nếu dùng AGY):")
        layout.addWidget(self.key_label)
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("AIzaSy... (Không bắt buộc khi dùng AGY)")
        self.key_input.setText(config.gemini_api_key)
        layout.addWidget(self.key_input)

        # 4. Obsidian Vault Path
        layout.addWidget(QLabel("📁 Thư mục Obsidian Vault:"))
        vault_layout = QHBoxLayout()
        vault_layout.setSpacing(8)
        self.vault_input = QLineEdit()
        self.vault_input.setText(str(config.vault_path))
        browse_btn = QPushButton("Chọn...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_layout.addWidget(self.vault_input)
        vault_layout.addWidget(browse_btn)
        layout.addLayout(vault_layout)

        # 5. Global Hotkey
        layout.addWidget(QLabel("⌨️ Phím tắt toàn hệ thống (Global Hotkey):"))
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setText(config.hotkey)
        self.hotkey_input.setPlaceholderText("<ctrl>+<shift>+s")
        layout.addWidget(self.hotkey_input)

        # 6. Always on top & Thinking
        self.ontop_cb = QCheckBox("Luôn nổi trên các cửa sổ khác (Always on Top)")
        self.ontop_cb.setChecked(config.always_on_top)
        layout.addWidget(self.ontop_cb)

        self.thinking_cb = QCheckBox("Hiển thị chi tiết quá trình suy luận & gọi công cụ (Thinking & Tools)")
        self.thinking_cb.setChecked(config.show_thinking)
        layout.addWidget(self.thinking_cb)

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

    def _save(self):
        engine = "agy" if self.radio_agy.isChecked() else "gemini_api"
        model_name = self.model_combo.currentData() or "gemini-3.8-flash-medium"

        config.set("engine", engine)
        config.set("model_name", model_name)
        config.set("gemini_api_key", self.key_input.text().strip())
        config.set("vault_path", self.vault_input.text().strip())
        config.set("hotkey", self.hotkey_input.text().strip())
        config.set("always_on_top", self.ontop_cb.isChecked())
        config.set("show_thinking", self.thinking_cb.isChecked())

        self.settings_saved.emit()
        self.accept()

