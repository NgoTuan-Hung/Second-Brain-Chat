"""
Proactive Companion Service for Second Brain AI.
Runs background cadences for Morning Briefing, Spaced Repetition, and Evening Reflection.
"""

import time
from datetime import datetime
from collections import deque
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from config import config
from core.vault_reader import VaultReader

class ProactiveService(QObject):
    """
    Monitors time and vault state to proactively trigger suggestions and check-ins.
    """
    nudge_ready = pyqtSignal(dict)  # Emits payload dict to be shown in SpeechBubble

    def __init__(self, vault_reader: Optional[VaultReader] = None, parent=None):
        super().__init__(parent)
        self.vault_reader = vault_reader or VaultReader(config.vault_path)
        
        # State tracking
        self.last_morning_date: Optional[str] = None
        self.last_evening_date: Optional[str] = None
        self.last_spaced_time: float = 0.0
        self.is_chat_active: bool = False
        self.recent_spaced_files: deque = deque(maxlen=30)

        # Periodic check timer (checks every 20 seconds to support 1-minute cadence)
        self.check_timer = QTimer(self)
        self.check_timer.setInterval(20 * 1000)
        self.check_timer.timeout.connect(self.check_triggers)

    def set_vault_path(self, path):
        self.vault_reader = VaultReader(path)

    def on_settings_updated(self):
        """Called when settings are saved in SettingsDialog."""
        self.set_vault_path(config.vault_path)
        if config.proactive_enabled:
            QTimer.singleShot(1500, self.check_triggers)

    def start(self):
        """Starts the proactive scheduler timer."""
        self.check_timer.start()
        # Optional initial check after 10 seconds of app start
        QTimer.singleShot(10000, self.check_triggers)

    def stop(self):
        """Stops the scheduler timer."""
        self.check_timer.stop()

    def set_chat_active(self, active: bool):
        """Tracks whether user is actively using the large chat window."""
        self.is_chat_active = active

    def _parse_time(self, time_str: str, def_h: int, def_m: int):
        try:
            parts = str(time_str).strip().split(":")
            return int(parts[0]), int(parts[1])
        except Exception:
            return def_h, def_m

    def check_triggers(self):
        """Evaluates conditions for Morning Briefing, Evening Reflection, or Spaced Repetition."""
        if not config.proactive_enabled:
            return

        if self.is_chat_active:
            return

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hour = now.hour
        current_min = now.minute
        cur_minute_of_day = current_hour * 60 + current_min

        # 1. Morning Briefing (From morning_time up to 4 hours later)
        m_h, m_m = self._parse_time(config.morning_time, 8, 0)
        m_minute_of_day = m_h * 60 + m_m
        if config.morning_briefing and (m_minute_of_day <= cur_minute_of_day <= m_minute_of_day + 240):
            if self.last_morning_date != today_str:
                nudge = self._create_morning_nudge()
                if nudge:
                    self.last_morning_date = today_str
                    self.nudge_ready.emit(nudge)
                    return

        # 2. Evening Reflection (From evening_time until midnight)
        e_h, e_m = self._parse_time(config.evening_time, 18, 0)
        e_minute_of_day = e_h * 60 + e_m
        if config.evening_reflection and (e_minute_of_day <= cur_minute_of_day <= 23 * 60 + 59):
            if self.last_evening_date != today_str:
                nudge = self._create_evening_nudge()
                if nudge:
                    self.last_evening_date = today_str
                    self.nudge_ready.emit(nudge)
                    return

        # 3. Spaced Repetition (Midday / Daytime interval: default every X minutes)
        cooldown_sec = max(1, config.proactive_interval_min) * 60
        # Active daytime window: between 08:00 and 22:30
        if config.spaced_repetition and (8 <= current_hour <= 22):
            if (time.time() - self.last_spaced_time) >= cooldown_sec:
                nudge = self._create_spaced_repetition_nudge()
                if nudge:
                    self.last_spaced_time = time.time()
                    self.nudge_ready.emit(nudge)
                    return

    def trigger_instant_nudge(self, force_type: Optional[str] = None):
        """
        Manually trigger a proactive nudge (useful for testing or user-initiated inspiration).
        """
        now = datetime.now()
        current_hour = now.hour

        if force_type == "morning":
            nudge = self._create_morning_nudge()
        elif force_type == "evening":
            nudge = self._create_evening_nudge()
        elif force_type == "spaced":
            nudge = self._create_spaced_repetition_nudge()
        else:
            # Smart pick based on current hour
            if 6 <= current_hour <= 11:
                nudge = self._create_morning_nudge()
            elif 17 <= current_hour <= 23:
                nudge = self._create_evening_nudge()
            else:
                nudge = self._create_spaced_repetition_nudge()

        if not nudge:
            # Fallback to spaced repetition or general note
            nudge = self._create_spaced_repetition_nudge()

        if nudge:
            self.nudge_ready.emit(nudge)

    def _create_morning_nudge(self) -> Optional[Dict[str, Any]]:
        """Generates a Morning Briefing payload."""
        tasks = self.vault_reader.get_uncompleted_tasks(days_back=2, max_tasks=3)
        stats = self.vault_reader.get_daily_summary_stats()

        if tasks:
            task_lines = "\n".join([f"• {t['task'][:50]}" for t in tasks[:2]])
            more_text = f" (và {len(tasks)-2} việc khác)" if len(tasks) > 2 else ""
            msg = f"Bạn còn việc tồn đọng cần xử lý:\n{task_lines}{more_text}"
            actions = [
                {"id": "plan_tasks", "label": "📋 Xem việc tồn", "primary": True},
                {"id": "open_daily", "label": "📝 Mở Daily Note"},
                {"id": "dismiss", "label": "Để sau"},
            ]
            prompt = "Hãy tổng hợp các việc cần làm hôm nay và các task tồn đọng trong Second Brain, sau đó gợi ý thứ tự ưu tiên thực hiện cho tôi."
        else:
            msg = "Chào ngày mới! Second Brain hôm nay đang sẵn sàng. Mục tiêu quan trọng nhất của bạn là gì?"
            actions = [
                {"id": "plan_day", "label": "🎯 Lên kế hoạch ngày", "primary": True},
                {"id": "quick_log", "label": "📝 Ghi mục tiêu"},
                {"id": "dismiss", "label": "Bỏ qua"},
            ]
            prompt = "Chào buổi sáng! Hãy giúp tôi lên kế hoạch làm việc hiệu quả cho hôm nay và chuẩn bị ghi chú Daily Note."

        return {
            "type": "morning",
            "category": "MORNING",
            "emoji": "☀️",
            "title": "Khởi Động Ngày Mới",
            "message": msg,
            "actions": actions,
            "prompt_to_send": prompt,
            "tasks": tasks,
        }

    def _create_evening_nudge(self) -> Optional[Dict[str, Any]]:
        """Generates an Evening Reflection payload."""
        stats = self.vault_reader.get_daily_summary_stats()
        
        if stats.get("exists") and stats.get("tasks_total", 0) > 0:
            done = stats.get("tasks_done", 0)
            total = stats.get("tasks_total", 0)
            msg = f"Hôm nay bạn đã hoàn thành {done}/{total} mục tiêu trong Daily Note. Bạn có muốn ghi lại kết quả cuối ngày không?"
        else:
            msg = "Hôm nay công việc của bạn diễn ra thế nào? Click để ghi nhanh 1 dòng nhật ký vào Second Brain nhé!"

        return {
            "type": "evening",
            "category": "EVENING",
            "emoji": "🌙",
            "title": "Tổng Kết Cuối Ngày",
            "message": msg,
            "actions": [
                {"id": "quick_log", "label": "📝 Ghi nhật ký", "primary": True},
                {"id": "review_eod", "label": "📊 Đánh giá ngày"},
                {"id": "dismiss", "label": "Nghỉ ngơi"},
            ],
            "prompt_to_send": "Ghi nhật ký cuối ngày: Hôm nay tôi đã hoàn thành các công việc sau... ",
        }

    def _create_spaced_repetition_nudge(self) -> Optional[Dict[str, Any]]:
        """Generates a Spaced Repetition knowledge resurfacing payload."""
        candidate = self.vault_reader.get_spaced_repetition_candidates(
            min_age_days=config.spaced_min_age_days,
            excluded_files=set(self.recent_spaced_files)
        )
        if not candidate:
            return None

        # Track to prevent immediate repetition
        if "file" in candidate:
            self.recent_spaced_files.append(candidate["file"])

        title = candidate["title"]
        days = candidate["days_ago"]
        snippet = candidate["snippet"]
        tags_str = (" " + " ".join([f"#{t}" for t in candidate.get("tags", [])])) if candidate.get("tags") else ""

        if days == 0:
            time_desc = "Hôm nay bạn vừa ghi chép"
        elif days == 1:
            time_desc = "Hôm qua bạn đã ghi chép"
        else:
            time_desc = f"{days} ngày trước bạn đã ghi chép"

        msg = f"{time_desc}{tags_str}:\n\"{snippet}\""

        return {
            "type": "spaced_repetition",
            "category": "SPACED REPETITION",
            "emoji": "💡",
            "title": f"Ôn lại: {title}",
            "message": msg,
            "actions": [
                {"id": "quiz_note", "label": "🧠 Ôn tập nhanh", "primary": True},
                {"id": "summarize_note", "label": "📖 Xem tóm tắt"},
                {"id": "dismiss", "label": "Để sau"},
            ],
            "prompt_to_send": f"Hãy đọc ghi chú '{title}' trong Second Brain, tóm tắt 3 ý quan trọng nhất và đặt cho tôi 1 câu hỏi nhanh để kiểm tra mức độ hiểu sâu kiến thức này.",
            "note": candidate,
        }
