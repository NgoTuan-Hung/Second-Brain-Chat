"""
Verification test for VaultReader and Core Tools.
"""

from pathlib import Path
from config import config
from core.vault_reader import VaultReader
from core.tools import (
    get_vault_path, list_recent_notes, search_vault,
    append_daily_log, create_note, add_task, read_note
)

def test_vault_reader():
    print("Testing VaultReader...")
    reader = VaultReader(config.vault_path)
    print(f"- Vault valid: {reader.is_valid()}")
    overview = reader.get_structure_overview()
    print(f"- Total notes: {overview.get('total_notes')}")
    print(f"- Folders: {overview.get('folders')}")
    
    ctx = reader.get_context_for_prompt()
    print(f"- Context length: {len(ctx)} chars")
    assert reader.is_valid(), "Vault should be valid"
    print(" VaultReader PASSED!\n")

def test_tools():
    print("Testing Tools...")
    # 1. List recent
    recent = list_recent_notes(count=3)
    print(f"Recent notes:\n{recent}\n")

    # 2. Search
    search_res = search_vault(query="AI", max_results=3)
    print(f"Search 'AI':\n{search_res}\n")

    # 3. Append Daily
    daily_res = append_daily_log("Thử nghiệm kết nối Second Brain Companion", category="Test")
    print(f"Daily log append: {daily_res}")

    # 4. Add task
    task_res = add_task("Kiểm tra tính năng floating chatbot", due_date="Hôm nay", priority="high")
    print(f"Add task: {task_res}")

    # 5. Create note
    note_res = create_note(
        title="Test Floating Companion Note",
        content="Đây là ghi chú tự động tạo từ Second Brain Floating Chatbot.",
        folder="Knowledge",
        tags=["ai", "test", "companion"]
    )
    print(f"Create note: {note_res}")

    # Verify created note
    test_note = config.vault_path / "Knowledge" / "Test Floating Companion Note.md"
    assert test_note.exists(), f"File {test_note} should exist"
    print(f"Verified test note exists at: {test_note}")
    # Clean up test note if created
    test_note.unlink()
    print("Cleaned up test note.")

    print(" Tools test PASSED!\n")

if __name__ == "__main__":
    test_vault_reader()
    test_tools()
