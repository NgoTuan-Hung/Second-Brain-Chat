"""
Vault Reader & Context Extractor for Obsidian Second Brain.
Scans and queries the Obsidian vault filesystem for real-time context.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class VaultReader:
    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path).expanduser().resolve()

    def is_valid(self) -> bool:
        return self.vault_path.exists() and self.vault_path.is_dir()

    def get_structure_overview(self) -> Dict[str, Any]:
        """Returns folder structure and counts of markdown files."""
        if not self.is_valid():
            return {"error": f"Vault path '{self.vault_path}' does not exist."}

        folders = {}
        total_notes = 0

        for item in self.vault_path.iterdir():
            if item.name.startswith("."):
                continue
            if item.is_dir():
                md_files = list(item.glob("**/*.md"))
                folders[item.name] = len(md_files)
                total_notes += len(md_files)
            elif item.suffix == ".md":
                total_notes += 1

        root_notes = [f.name for f in self.vault_path.glob("*.md") if not f.name.startswith(".")]

        return {
            "vault_path": str(self.vault_path),
            "total_notes": total_notes,
            "folders": folders,
            "root_notes": root_notes,
        }

    def get_context_for_prompt(self, max_length: int = 4000) -> str:
        """Reads key index/guideline files to provide rich context to the LLM."""
        if not self.is_valid():
            return f"Note: Vault not found at {self.vault_path}."

        context_parts = []
        context_parts.append(f"# Obsidian Vault Context (Path: {self.vault_path})")

        # 1. Structure overview
        overview = self.get_structure_overview()
        folders_str = ", ".join([f"{k} ({v} notes)" for k, v in overview.get("folders", {}).items()])
        context_parts.append(f"- Folders: {folders_str}")
        context_parts.append(f"- Root notes: {', '.join(overview.get('root_notes', []))}")

        # 2. Key guidance files
        key_files = ["_CLAUDE.md", "CRITICAL_FACTS.md", "index.md", "About Me.md"]
        for kf in key_files:
            file_path = self.vault_path / kf
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace").strip()
                    if content:
                        # Truncate if too large
                        snippet = content[:800] + ("\n...(truncated)" if len(content) > 800 else "")
                        context_parts.append(f"\n--- Content of [{kf}] ---\n{snippet}")
                except Exception as e:
                    print(f"Error reading {kf}: {e}")

        # 3. Recent Daily Note
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_candidates = [
            self.vault_path / "Daily" / f"{today_str}.md",
            self.vault_path / "Logs" / f"{today_str}.md",
            self.vault_path / f"{today_str}.md",
        ]
        for dp in daily_candidates:
            if dp.exists():
                try:
                    daily_content = dp.read_text(encoding="utf-8", errors="replace").strip()
                    snippet = daily_content[:600] + ("\n...(truncated)" if len(daily_content) > 600 else "")
                    context_parts.append(f"\n--- Today's Daily Note ({dp.name}) ---\n{snippet}")
                    break
                except Exception:
                    pass

        full_context = "\n".join(context_parts)
        if len(full_context) > max_length:
            full_context = full_context[:max_length] + "\n...(vault context truncated)"
        return full_context

    def search_notes(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search markdown files in the vault by text query."""
        if not self.is_valid():
            return []

        query_lower = query.lower()
        results = []

        for md_file in self.vault_path.glob("**/*.md"):
            if md_file.name.startswith(".") or ".obsidian" in md_file.parts or ".agents" in md_file.parts:
                continue

            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                rel_path = str(md_file.relative_to(self.vault_path))

                # Match in filename or content
                if query_lower in md_file.stem.lower() or query_lower in content.lower():
                    # Find snippet around query
                    snippet = ""
                    idx = content.lower().find(query_lower)
                    if idx != -1:
                        start = max(0, idx - 100)
                        end = min(len(content), idx + 200)
                        snippet = content[start:end].replace("\n", " ").strip()
                    else:
                        snippet = content[:200].replace("\n", " ").strip()

                    results.append({
                        "file": rel_path,
                        "title": md_file.stem,
                        "snippet": f"...{snippet}..." if snippet else "",
                        "size": md_file.stat().st_size,
                    })

                    if len(results) >= max_results:
                        break
            except Exception:
                continue

        return results

    def read_note(self, rel_path: str) -> Optional[str]:
        """Read content of a specific note given relative path or filename."""
        if not self.is_valid():
            return None

        target = self.vault_path / rel_path
        if not target.exists() and not rel_path.endswith(".md"):
            target = self.vault_path / f"{rel_path}.md"

        if not target.exists():
            # Search for filename match anywhere
            found = list(self.vault_path.glob(f"**/{rel_path}*"))
            if found and found[0].is_file():
                target = found[0]

        if target.exists() and target.is_file():
            try:
                return target.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                return f"Error reading note: {e}"

        return None

    def get_uncompleted_tasks(self, days_back: int = 3, max_tasks: int = 8) -> List[Dict[str, Any]]:
        """Scans recent daily notes and key files for uncompleted '- [ ]' tasks."""
        if not self.is_valid():
            return []

        import re
        from datetime import datetime, timedelta

        task_regex = re.compile(r"^\s*-\s*\[\s*\]\s+(.+)$")
        tasks = []
        visited_files = set()

        # 1. Search daily notes for the last `days_back` days
        today = datetime.now().date()
        for i in range(days_back + 1):
            day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            candidates = [
                self.vault_path / "Daily" / f"{day_str}.md",
                self.vault_path / "Logs" / f"{day_str}.md",
                self.vault_path / f"{day_str}.md",
            ]
            for c in candidates:
                if c.exists() and c.is_file() and c not in visited_files:
                    visited_files.add(c)
                    try:
                        content = c.read_text(encoding="utf-8", errors="replace")
                        for line in content.splitlines():
                            match = task_regex.match(line)
                            if match:
                                task_text = match.group(1).strip()
                                tasks.append({
                                    "task": task_text,
                                    "source": str(c.relative_to(self.vault_path)),
                                    "date": day_str,
                                    "is_today": (i == 0)
                                })
                                if len(tasks) >= max_tasks:
                                    return tasks
                    except Exception:
                        pass

        # 2. If still have room, check root todo files (e.g. Todo.md, Tasks.md)
        todo_names = ["Todo.md", "Tasks.md", "todo.md", "tasks.md"]
        for tn in todo_names:
            tf = self.vault_path / tn
            if tf.exists() and tf.is_file() and tf not in visited_files:
                visited_files.add(tf)
                try:
                    content = tf.read_text(encoding="utf-8", errors="replace")
                    for line in content.splitlines():
                        match = task_regex.match(line)
                        if match:
                            tasks.append({
                                "task": match.group(1).strip(),
                                "source": str(tf.relative_to(self.vault_path)),
                                "date": "Todo list",
                                "is_today": False
                            })
                            if len(tasks) >= max_tasks:
                                return tasks
                except Exception:
                    pass

        return tasks

    def get_spaced_repetition_candidates(
        self,
        min_age_days: int = 0,
        excluded_files: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Picks a genuine knowledge note from the Vault to resurface to the user.
        Excludes:
          - Non-knowledge folders (Daily, Logs, Tasks, Templates, Archive, Assets, Skills, System, etc.)
          - System/meta files (_CLAUDE.md, CRITICAL_FACTS.md, index.md, About Me.md, Welcome.md, log.md, etc.)
          - Files starting with '_' or '.'
          - Files with exclude tags (#exclude, #no-review, #private, #system, #meta, #task, #todo, #credential)
          - Notes with YAML flags (sr: false, exclude: true, review: false)
          - Very short/empty notes (< 80 chars)
          - Recently shown files passed in excluded_files
        Prioritizes notes in dedicated knowledge folders while falling back to the wider pool
        if knowledge folder has few candidates.
        """
        if not self.is_valid():
            return None

        import re
        import random
        import time

        now = time.time()
        candidates = []

        # Directories that should NEVER be resurfaced as knowledge
        excluded_dirs = {
            ".obsidian", ".agents", ".git", ".trash", ".vscode", ".idea",
            "daily", "logs", "journal", "calendar",
            "tasks", "todo", "todos", "templates", "template",
            "archive", "archived", "drafts", "inbox", "assets",
            "attachments", "resources", "scripts", "skills", "system",
            "prompts", "configs"
        }

        # Specific system/meta files to ignore (case-insensitive)
        excluded_filenames = {
            "_claude.md", "claude.md", "critical_facts.md", "readme.md",
            "index.md", "about me.md", "welcome.md", "log.md",
            "todo.md", "tasks.md", "summary.md", "license.md"
        }

        excluded_tags = {
            "#exclude", "#no-review", "#private", "#system",
            "#meta", "#task", "#todo", "#draft", "#archive",
            "#credential", "#credentials", "#password", "#secret"
        }

        excluded_rel_paths = set(excluded_files) if excluded_files else set()

        for md_file in self.vault_path.glob("**/*.md"):
            # 1. Ignore if any parent directory is in excluded_dirs or hidden
            parts_lower = [p.lower() for p in md_file.parts]
            if any(p in excluded_dirs or p.startswith(".") for p in parts_lower):
                continue

            # 2. Ignore hidden files or files starting with '_' (convention for system/meta notes)
            if md_file.name.startswith(".") or md_file.name.startswith("_"):
                continue

            # 3. Ignore explicit system/meta filenames
            if md_file.name.lower() in excluded_filenames:
                continue

            try:
                stat = md_file.stat()
                # Ignore tiny files < 80 bytes
                if stat.st_size < 80:
                    continue

                raw_content = md_file.read_text(encoding="utf-8", errors="replace")
                
                # Check YAML frontmatter exclusions
                cleaned_content = raw_content
                if raw_content.startswith("---"):
                    parts = raw_content.split("---", 2)
                    if len(parts) >= 3:
                        fm = parts[1].lower()
                        if any(k in fm for k in [
                            "sr: false", "sr-due: false", "exclude: true",
                            "review: false", "type: meta", "type: system",
                            "status: archive", "status: draft"
                        ]):
                            continue
                        cleaned_content = parts[2].strip()

                # Clean content length check (ignore empty or stub notes)
                text_lines = [l.strip() for l in cleaned_content.splitlines() if l.strip() and not l.startswith("#")]
                text_body = " ".join(text_lines)
                if len(text_body) < 80:
                    continue

                # Check tags
                tags = [t.lower() for t in re.findall(r"#[\w-]+", raw_content)]
                if set(tags) & excluded_tags:
                    continue

                # Check if it's in a designated Knowledge folder
                rel_parts_lower = [p.lower() for p in md_file.relative_to(self.vault_path).parts]
                is_knowledge_folder = any(k in p for p in rel_parts_lower[:-1] for k in ["knowledge", "learn", "study", "notes", "permanent", "zettelkasten"])

                age_days = (now - stat.st_mtime) / (24 * 3600)
                candidates.append((md_file, age_days, is_knowledge_folder, cleaned_content, raw_content))
            except Exception:
                continue

        if not candidates:
            return None

        # Filter out recently shown files if provided (anti-repetition)
        if excluded_rel_paths:
            fresh_candidates = [
                c for c in candidates 
                if str(c[0].relative_to(self.vault_path)) not in excluded_rel_paths
            ]
            # If fresh candidates exist, use them; if exhausted, reset to all candidates
            if fresh_candidates:
                candidates = fresh_candidates

        # Prioritize knowledge folders if they have enough variety (>= 4 files),
        # otherwise mix with all valid candidates in vault so pool isn't locked to 1-2 notes.
        knowledge_candidates = [c for c in candidates if c[2]]
        if len(knowledge_candidates) >= 4:
            pool = knowledge_candidates
        else:
            pool = candidates

        # Filter by min_age_days if requested (> 0)
        if min_age_days > 0:
            older_candidates = [c for c in pool if c[1] >= min_age_days]
            pool_to_pick = older_candidates if older_candidates else pool
        else:
            pool_to_pick = pool

        chosen = random.choice(pool_to_pick)
        chosen_file, age_days, _, cleaned_content, raw_content = chosen

        try:
            # Find clean preview lines, preserving structure and bullet points
            lines = [l.strip() for l in cleaned_content.splitlines() if l.strip() and not l.startswith("#")]
            preview_lines = []
            char_count = 0
            for line in lines:
                if len(preview_lines) >= 6 or char_count >= 500:
                    break
                preview_lines.append(line)
                char_count += len(line)

            snippet = "\n".join(preview_lines)
            if len(snippet) > 500:
                truncated = snippet[:500]
                if " " in truncated:
                    snippet = truncated.rsplit(" ", 1)[0] + "..."
                else:
                    snippet = truncated + "..."

            # Extract tags
            tags = re.findall(r"#([\w-]+)", raw_content)
            tags = list(dict.fromkeys(tags))[:4]

            return {
                "file": str(chosen_file.relative_to(self.vault_path)),
                "title": chosen_file.stem,
                "snippet": snippet or "(Ghi chú không có nội dung mô tả)",
                "tags": tags,
                "days_ago": max(0, int(age_days)),
            }
        except Exception as e:
            print(f"[VaultReader] Error reading spaced repetition candidate: {e}")
            return None

    def get_daily_summary_stats(self) -> Dict[str, Any]:
        """Returns statistics of today's Daily note."""
        if not self.is_valid():
            return {"exists": False, "tasks_total": 0, "tasks_done": 0, "tasks_pending": 0}

        import re
        from datetime import datetime

        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_candidates = [
            self.vault_path / "Daily" / f"{today_str}.md",
            self.vault_path / "Logs" / f"{today_str}.md",
            self.vault_path / f"{today_str}.md",
        ]

        for dp in daily_candidates:
            if dp.exists() and dp.is_file():
                try:
                    content = dp.read_text(encoding="utf-8", errors="replace")
                    pending = len(re.findall(r"^\s*-\s*\[\s*\]", content, re.MULTILINE))
                    done = len(re.findall(r"^\s*-\s*\[x\]", content, re.IGNORECASE | re.MULTILINE))
                    has_evening = bool(re.search(r"(tổng kết|evening|eod|cuối ngày)", content, re.IGNORECASE))
                    return {
                        "exists": True,
                        "file": str(dp.relative_to(self.vault_path)),
                        "tasks_total": pending + done,
                        "tasks_pending": pending,
                        "tasks_done": done,
                        "has_evening_log": has_evening,
                    }
                except Exception:
                    pass

        return {"exists": False, "tasks_total": 0, "tasks_done": 0, "tasks_pending": 0, "has_evening_log": False}

