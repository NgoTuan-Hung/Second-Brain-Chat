"""
Unit & Integration test for Proactive Service, Cadence Scheduling, and Settings UI.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from config import config
from core.vault_reader import VaultReader
from core.proactive_service import ProactiveService
from ui.settings_dialog import SettingsDialog

def test_proactive_pipeline():
    print("==================================================")
    print("🧪 TESTING PROACTIVE SERVICE & SETTINGS PIPELINE")
    print("==================================================")

    # 1. Config properties
    print(f"1. Proactive Enabled: {config.proactive_enabled}")
    print(f"   Morning Briefing: {config.morning_briefing} (Time: {config.morning_time})")
    print(f"   Evening Reflection: {config.evening_reflection} (Time: {config.evening_time})")
    print(f"   Spaced Repetition: {config.spaced_repetition} (Interval: {config.proactive_interval_min} min)")
    print(f"   Bubble Dismiss: {config.bubble_dismiss_sec}s")

    assert hasattr(config, "morning_time"), "Missing morning_time in config"
    assert hasattr(config, "evening_time"), "Missing evening_time in config"
    assert hasattr(config, "bubble_dismiss_sec"), "Missing bubble_dismiss_sec in config"
    assert hasattr(config, "spaced_min_age_days"), "Missing spaced_min_age_days in config"

    # 2. Vault Reader
    reader = VaultReader(config.vault_path)
    print(f"\n2. Vault Path: {reader.vault_path}")
    print(f"   Vault is valid: {reader.is_valid()}")

    # 3. Proactive Service
    service = ProactiveService(reader)
    h, m = service._parse_time(config.morning_time, 8, 0)
    print(f"\n3. Proactive Service Parsed Morning Time: {h:02d}:{m:02d}")
    assert isinstance(h, int) and isinstance(m, int)

    morning_nudge = service._create_morning_nudge()
    if morning_nudge:
        print(f"   - Generated Morning Nudge Title: {morning_nudge.get('title')}")

    service.on_settings_updated()
    print("   - Called on_settings_updated() successfully.")

    # Test Spaced Repetition candidate filtering
    print("\n   - Testing Spaced Repetition file filters:")
    for _ in range(15):
        cand = reader.get_spaced_repetition_candidates(min_age_days=0)
        if cand:
            rel_file = cand["file"]
            assert not rel_file.startswith("_"), f"Should not pick files starting with _: {rel_file}"
            assert not rel_file.startswith("."), f"Should not pick hidden files: {rel_file}"
            assert "Tasks/" not in rel_file, f"Should not pick task files: {rel_file}"
            assert "Daily/" not in rel_file and "Logs/" not in rel_file, f"Should not pick daily/logs: {rel_file}"
            assert rel_file not in ["CRITICAL_FACTS.md", "index.md", "About Me.md", "Welcome.md", "log.md"], f"Picked excluded meta file: {rel_file}"
    print("   ✓ Spaced Repetition candidate exclusion verified: No system, meta, or task files selected.")

    # 4. Settings Dialog GUI Initialization Test (Headless offscreen)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = SettingsDialog()
    assert dialog.tabs.count() == 2, "SettingsDialog should have 2 tabs"
    assert dialog.interval_spin.minimum() == 1, "Interval spin minimum should be 1 min"
    assert dialog.interval_spin.maximum() >= 720, "Interval spin maximum should be at least 720 min"

    # Test setting interval to 1 minute
    dialog.interval_spin.setValue(1)
    assert dialog.interval_spin.value() == 1, "Interval spin value should be 1"

    assert dialog.morning_time_combo.count() > 0, "Morning time combo should have items"
    assert dialog.evening_time_combo.count() > 0, "Evening time combo should have items"
    assert dialog.dismiss_combo.count() > 0, "Dismiss combo should have items"
    assert dialog.spaced_age_combo.count() > 0, "Spaced age combo should have items"

    # Test toggling master proactive checkbox
    dialog.proactive_cb.setChecked(False)
    assert not dialog.sub_settings_container.isEnabled(), "Sub-settings container should be disabled when master toggle is off"
    dialog.proactive_cb.setChecked(True)
    assert dialog.sub_settings_container.isEnabled(), "Sub-settings container should be enabled when master toggle is on"

    print("\n4. SettingsDialog UI verification passed:")
    print("   - 2 Tabs initialized (AI & Hệ Thống / Trợ Lý Chủ Động)")
    print("   - Master toggle disables/enables child controls correctly")
    print("   - All dropdown options loaded properly")

    dialog.close()
    print("\n✅ ALL PROACTIVE PIPELINE & SETTINGS TESTS PASSED!\n")

if __name__ == "__main__":
    test_proactive_pipeline()
