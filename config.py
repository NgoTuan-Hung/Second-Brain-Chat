"""
Configuration Manager for Second Brain AI Companion.
Handles persistent settings, environment variables, engine choices, and default parameters.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"

DEFAULT_VAULT_PATH = os.getenv(
    "VAULT_PATH",
    "/home/hungdreamer/Desktop/all-in-one/App/Obsidian Data/Vault/Second Brain"
)

DEFAULT_SETTINGS = {
    "engine": "agy",  # "agy" (Antigravity CLI) or "gemini_api"
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "model_name": os.getenv("MODEL_NAME", "gemini-3.8-flash-medium"),
    "vault_path": DEFAULT_VAULT_PATH,
    "hotkey": "<ctrl>+<shift>+s",
    "always_on_top": True,
    "theme": "dark",
    "window_width": 430,
    "window_height": 640,
    "bubble_size": 64,
    "last_x": 120,
    "last_y": 120,
    "sound_enabled": False,
    "show_thinking": True,
    "proactive_enabled": True,
    "morning_briefing": True,
    "spaced_repetition": True,
    "spaced_min_age_days": 0,
    "evening_reflection": True,
    "proactive_interval_min": 30,
    "morning_time": "08:00",
    "evening_time": "18:00",
    "bubble_dismiss_sec": 15,
}

class Config:
    def __init__(self):
        self._settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._settings.update(data)
            except Exception as e:
                print(f"[Config] Error loading settings.json: {e}")
        
        env_key = os.getenv("GEMINI_API_KEY")
        if env_key and not self._settings.get("gemini_api_key"):
            self._settings["gemini_api_key"] = env_key

        env_vault = os.getenv("VAULT_PATH")
        if env_vault:
            self._settings["vault_path"] = env_vault

        env_engine = os.getenv("AI_ENGINE")
        if env_engine:
            self._settings["engine"] = env_engine

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error saving settings.json: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()

    @property
    def engine(self) -> str:
        return self._settings.get("engine", "agy")

    @property
    def gemini_api_key(self) -> str:
        return self._settings.get("gemini_api_key", "")

    @property
    def model_name(self) -> str:
        return self._settings.get("model_name", "gemini-3.8-flash-medium")

    @property
    def vault_path(self) -> Path:
        return Path(self._settings.get("vault_path", DEFAULT_VAULT_PATH))

    @property
    def hotkey(self) -> str:
        return self._settings.get("hotkey", "<ctrl>+<shift>+s")

    @property
    def always_on_top(self) -> bool:
        return self._settings.get("always_on_top", True)

    @property
    def show_thinking(self) -> bool:
        return self._settings.get("show_thinking", True)

    @property
    def proactive_enabled(self) -> bool:
        return self._settings.get("proactive_enabled", True)

    @property
    def morning_briefing(self) -> bool:
        return self._settings.get("morning_briefing", True)

    @property
    def spaced_repetition(self) -> bool:
        return self._settings.get("spaced_repetition", True)

    @property
    def spaced_min_age_days(self) -> int:
        return int(self._settings.get("spaced_min_age_days", 0))

    @property
    def evening_reflection(self) -> bool:
        return self._settings.get("evening_reflection", True)

    @property
    def proactive_interval_min(self) -> int:
        return int(self._settings.get("proactive_interval_min", 30))

    @property
    def morning_time(self) -> str:
        return self._settings.get("morning_time", "08:00")

    @property
    def evening_time(self) -> str:
        return self._settings.get("evening_time", "18:00")

    @property
    def bubble_dismiss_sec(self) -> int:
        return int(self._settings.get("bubble_dismiss_sec", 15))

config = Config()


