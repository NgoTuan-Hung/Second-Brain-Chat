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
