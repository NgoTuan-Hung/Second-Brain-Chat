"""
Obsidian Second Brain Tools for AI Agent.
Provides functions for creating notes, appending daily logs, adding tasks, and searching.
Compatible with Google GenAI function calling.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import config
from core.vault_reader import VaultReader

def get_vault_path() -> Path:
    return config.vault_path

def append_daily_log(content: str, category: str = "Log") -> str:
    """
    Append an entry or quick thought to today's Daily note or Log note in Obsidian.
    
    Args:
        content: The text/thought/summary to record.
        category: Category section, e.g. "Work", "Ideas", "Log", "Meeting", "Learning".
    """
    vault = get_vault_path()
    if not vault.exists():
        return f"Error: Vault path does not exist: {vault}"

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    time_str = today.strftime("%H:%M")

    # Priority: Daily folder, then Logs folder, then root
    daily_dir = vault / "Daily"
    if not daily_dir.exists():
        logs_dir = vault / "Logs"
        if logs_dir.exists():
            target_file = logs_dir / f"{today_str}.md"
        else:
            daily_dir.mkdir(parents=True, exist_ok=True)
            target_file = daily_dir / f"{today_str}.md"
    else:
        target_file = daily_dir / f"{today_str}.md"

    # Prepare markdown content
    entry_header = f"\n### [{time_str}] {category}\n"
    formatted_entry = f"{entry_header}- {content.strip()}\n"

    if not target_file.exists():
        initial_content = f"# Daily Note: {today_str}\n\nTags: #daily\n\n## Quick Logs\n{formatted_entry}"
        target_file.write_text(initial_content, encoding="utf-8")
        rel_path = str(target_file.relative_to(vault))
        return f"✅ Đã tạo Daily note mới và ghi log tại: `{rel_path}`"
    else:
        current_text = target_file.read_text(encoding="utf-8", errors="replace")
        target_file.write_text(current_text + formatted_entry, encoding="utf-8")
        rel_path = str(target_file.relative_to(vault))
        return f"✅ Đã thêm log vào `{rel_path}` lúc {time_str}"

def create_note(title: str, content: str, folder: str = "Knowledge", tags: Optional[List[str]] = None) -> str:
    """
    Create a new Markdown note in the Obsidian Second Brain.
    
    Args:
        title: The title / filename of the note.
        content: Markdown body of the note.
        folder: Subdirectory inside vault (e.g., 'Knowledge', 'Ideas', 'Tasks', 'Projects', 'People').
        tags: Optional list of tags to add to frontmatter (e.g. ['ai', 'research', 'ideas']).
    """
    vault = get_vault_path()
    if not vault.exists():
        return f"Error: Vault path does not exist: {vault}"

    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize title for filename
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
    if not safe_title:
        safe_title = f"Note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    file_path = target_dir / f"{safe_title}.md"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build YAML frontmatter
    tag_list = tags if tags else []
    if folder.lower() not in [t.lower() for t in tag_list]:
        tag_list.append(folder.lower())

    frontmatter = "---\n"
    frontmatter += f"title: \"{safe_title}\"\n"
    frontmatter += f"created: {now_str}\n"
    frontmatter += f"tags: [{', '.join(tag_list)}]\n"
    frontmatter += "---\n\n"

    body = f"# {safe_title}\n\n{content.strip()}\n"
    full_text = frontmatter + body

    file_path.write_text(full_text, encoding="utf-8")
    rel_path = str(file_path.relative_to(vault))
    return f"✅ Đã tạo ghi chú mới thành công: `[[{safe_title}]]` tại đường dẫn `{rel_path}`"

def add_task(task_text: str, due_date: str = "", priority: str = "normal", target_file: str = "") -> str:
    """
    Add a todo task item with checkbox to a task list or daily note.
    
    Args:
        task_text: The description of the task.
        due_date: Optional due date string (e.g. "2026-08-30" or "Hôm nay").
        priority: Priority level: 'high', 'normal', 'low'.
        target_file: Optional relative file path (defaults to Tasks/Tasks.md or today's Daily note).
    """
    vault = get_vault_path()
    if not vault.exists():
        return f"Error: Vault path does not exist: {vault}"

    if not target_file:
        tasks_dir = vault / "Tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        file_path = tasks_dir / "Tasks.md"
    else:
        file_path = vault / target_file
        if not file_path.suffix:
            file_path = file_path.with_suffix(".md")
        file_path.parent.mkdir(parents=True, exist_ok=True)

    p_badge = "🔥 [HIGH] " if priority == "high" else ("⚡ " if priority == "normal" else "☕ ")
    due_badge = f" 📅 {due_date}" if due_date else ""
    created_badge = f" ➕ {datetime.now().strftime('%Y-%m-%d')}"

    task_line = f"- [ ] {p_badge}{task_text.strip()}{due_badge}{created_badge}\n"

    if not file_path.exists():
        initial = f"# Tasks & Todo List\n\n## Backlog\n{task_line}"
        file_path.write_text(initial, encoding="utf-8")
    else:
        existing = file_path.read_text(encoding="utf-8", errors="replace")
        file_path.write_text(existing + task_line, encoding="utf-8")

    rel_path = str(file_path.relative_to(vault))
    return f"✅ Đã thêm việc cần làm vào `{rel_path}`: {task_text}"

def search_vault(query: str, max_results: int = 5) -> str:
    """
    Search notes in the Obsidian Vault by keywords.
    
    Args:
        query: Search term or keyword.
        max_results: Max number of matching notes to return.
    """
    reader = VaultReader(get_vault_path())
    results = reader.search_notes(query, max_results=max_results)
    if not results:
        return f"Không tìm thấy ghi chú nào khớp với từ khóa: '{query}'."

    res_str = f"🔍 Tìm thấy {len(results)} ghi chú khớp với '{query}':\n\n"
    for r in results:
        res_str += f"- **[[{r['title']}]]** (`{r['file']}`)\n  Trích đoạn: {r['snippet']}\n\n"
    return res_str

def read_note(filepath_or_title: str) -> str:
    """
    Read the full content of a specific note in the Obsidian Vault.
    
    Args:
        filepath_or_title: Note title or relative path (e.g. 'Knowledge/Transformer.md' or 'CRITICAL_FACTS').
    """
    reader = VaultReader(get_vault_path())
    content = reader.read_note(filepath_or_title)
    if content is None:
        return f"Không tìm thấy file ghi chú '{filepath_or_title}' trong Vault."
    return f"📄 Nội dung note `{filepath_or_title}`:\n\n```markdown\n{content}\n```"

def list_recent_notes(count: int = 8) -> str:
    """
    List recently modified notes in the Obsidian Vault.
    """
    vault = get_vault_path()
    if not vault.exists():
        return f"Vault không tồn tại tại {vault}"

    md_files = [f for f in vault.glob("**/*.md") if not f.name.startswith(".") and ".obsidian" not in f.parts and ".agents" not in f.parts]
    md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    recent = md_files[:count]
    if not recent:
        return "Chưa có ghi chú nào trong Vault."

    res = "📋 Ghi chú được chỉnh sửa gần đây:\n\n"
    for f in recent:
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rel_path = str(f.relative_to(vault))
        res += f"- **[[{f.stem}]]** (`{rel_path}`) — *{mtime}*\n"
    return res

# Export list of callable tools
ALL_TOOLS = [
    append_daily_log,
    create_note,
    add_task,
    search_vault,
    read_note,
    list_recent_notes
]
