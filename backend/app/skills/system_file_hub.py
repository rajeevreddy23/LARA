"""
System File & Folder Hub Skill for LARA OS.
Provides comprehensive file browsing, deep folder navigation, file content inspection,
system-wide search, and native file/folder launching on Windows.
"""

import os
import sys
import glob
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.skills.base import BaseSkill, SkillResult

logger = logging.getLogger("lara.skills.system_file_hub")


class SystemFileHubSkill(BaseSkill):
    """Deep file and folder management across Windows system drives and directories."""

    @property
    def name(self) -> str:
        return "system_file_hub"

    @property
    def description(self) -> str:
        return (
            "Browse any folder, search files across system drives (C:, D:, Downloads, Desktop, Documents), "
            "inspect file contents, create files/folders, and open folders in File Explorer."
        )

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "list files in downloads",
            "show files in D drive",
            "open folder desktop",
            "find pdf files",
            "search files about invoice",
            "read file README.md",
            "browse documents folder",
            "create file notes.txt with content Meeting at 5",
            "make folder D:\\Projects\\NewApp"
        ]

    @property
    def is_state_mutating(self) -> bool:
        return True

    def _resolve_folder_alias(self, alias: str) -> str:
        """Resolve common natural language folder names to absolute paths."""
        cleaned = alias.strip().strip('"\'').lower()
        user_home = os.path.expanduser("~")

        alias_map = {
            "downloads": os.path.join(user_home, "Downloads"),
            "download": os.path.join(user_home, "Downloads"),
            "desktop": os.path.join(user_home, "Desktop"),
            "documents": os.path.join(user_home, "Documents"),
            "docs": os.path.join(user_home, "Documents"),
            "document": os.path.join(user_home, "Documents"),
            "pictures": os.path.join(user_home, "Pictures"),
            "photos": os.path.join(user_home, "Pictures"),
            "music": os.path.join(user_home, "Music"),
            "videos": os.path.join(user_home, "Videos"),
            "home": user_home,
            "user": user_home,
            "root": "C:\\",
            "c": "C:\\",
            "c:": "C:\\",
            "c drive": "C:\\",
            "c:\\": "C:\\",
            "d": "D:\\",
            "d:": "D:\\",
            "d drive": "D:\\",
            "d:\\": "D:\\",
            "lara": "D:\\LARA",
            "workspace": "D:\\LARA",
            "project": "D:\\LARA",
            "projects": "D:\\LARA"
        }

        if cleaned in alias_map:
            return alias_map[cleaned]

        # Check if direct path exists
        if os.path.exists(alias):
            return os.path.abspath(alias)

        # Check if subfolder of user home or D:\ exists
        candidates = [
            os.path.join(user_home, alias),
            os.path.join("D:\\", alias),
            os.path.join("D:\\LARA", alias),
            os.path.join("C:\\", alias),
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)

        return alias

    def _find_files_matching(self, query: str, search_roots: List[str], max_results: int = 15) -> List[Dict[str, Any]]:
        """Search for files matching name or extension across candidate search roots."""
        matches = []
        clean_q = query.strip().lower()
        is_ext = clean_q.startswith(".") or clean_q in ["pdf", "docx", "py", "txt", "png", "jpg", "xlsx", "json", "md"]
        ext_pattern = clean_q if clean_q.startswith(".") else f".{clean_q}"

        for root in search_roots:
            if not os.path.exists(root):
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    # Skip massive system or cache directories for performance
                    dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in [
                        "node_modules", "AppData", "Windows", "$Recycle.Bin", "__pycache__", "venv", ".git"
                    ]]
                    
                    for f in filenames:
                        full_path = os.path.join(dirpath, f)
                        f_lower = f.lower()

                        matched = False
                        if is_ext:
                            if f_lower.endswith(ext_pattern):
                                matched = True
                        elif clean_q in f_lower:
                            matched = True

                        if matched:
                            try:
                                sz = os.path.getsize(full_path)
                                mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M")
                                matches.append({
                                    "name": f,
                                    "path": full_path,
                                    "size_kb": round(sz / 1024, 1),
                                    "modified": mtime,
                                    "is_dir": False
                                })
                            except Exception:
                                pass

                            if len(matches) >= max_results:
                                return matches
            except Exception as e:
                logger.debug("Search walk notice on %s: %s", root, e)

        return matches

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        """Execute system file and folder action."""
        start_time = time.perf_counter()
        action = params.get("action", "list").lower()
        target = params.get("target", "D:\\LARA")
        resolved_path = self._resolve_folder_alias(target)

        # -------------------------------------------------------------
        # Action: List Folder Contents
        # -------------------------------------------------------------
        if action in ["list", "browse", "show_folder", "ls"]:
            if not os.path.exists(resolved_path):
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"❌ Directory not found: `{resolved_path}`",
                    execution_time_ms=round(latency, 2)
                )

            if not os.path.isdir(resolved_path):
                resolved_path = os.path.dirname(resolved_path)

            try:
                entries = []
                for item in os.listdir(resolved_path):
                    if item.startswith(".") and item not in [".env", ".gitignore"]:
                        continue
                    full = os.path.join(resolved_path, item)
                    is_d = os.path.isdir(full)
                    size_str = "<DIR>" if is_d else f"{round(os.path.getsize(full) / 1024, 1)} KB"
                    mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
                    entries.append((is_d, item, size_str, mtime, full))

                # Sort: directories first, then files
                entries.sort(key=lambda x: (not x[0], x[1].lower()))

                lines = [
                    f"📁 **Folder Directory**: `{resolved_path}` ({len(entries)} items)\n",
                    "| Type | Name | Size | Modified |",
                    "| :--- | :--- | :--- | :--- |"
                ]

                for is_d, item, size_str, mtime, full in entries[:25]:
                    icon = "📁" if is_d else "📄"
                    lines.append(f"| {icon} | **{item}** | `{size_str}` | {mtime} |")

                if len(entries) > 25:
                    lines.append(f"\n*...and {len(entries) - 25} more items.*")

                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output="\n".join(lines),
                    execution_time_ms=round(latency, 2),
                    mutated_state=False
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Failed to list directory `{resolved_path}`: {e}",
                    execution_time_ms=round(latency, 2)
                )

        # -------------------------------------------------------------
        # Action: Search Files Across System
        # -------------------------------------------------------------
        elif action in ["search", "find", "search_files"]:
            query = params.get("query", target)
            user_home = os.path.expanduser("~")
            search_roots = [
                "D:\\LARA",
                os.path.join(user_home, "Desktop"),
                os.path.join(user_home, "Downloads"),
                os.path.join(user_home, "Documents"),
                "D:\\",
                "C:\\Users"
            ]

            results = self._find_files_matching(query, search_roots, max_results=12)

            if not results:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🔍 No files found matching query **'{query}'** across system search paths.",
                    execution_time_ms=round(latency, 2)
                )

            lines = [f"🔍 Found **{len(results)}** file(s) matching **'{query}'**:\n"]
            for idx, res in enumerate(results, 1):
                lines.append(f"{idx}. 📄 **{res['name']}** ({res['size_kb']} KB) — `{res['path']}` [{res['modified']}]")

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output="\n".join(lines),
                execution_time_ms=round(latency, 2)
            )

        # -------------------------------------------------------------
        # Action: Read File Content / Snippet
        # -------------------------------------------------------------
        elif action in ["read", "view", "inspect", "cat"]:
            # If not direct path, try resolving or searching
            file_path = resolved_path
            if not os.path.exists(file_path):
                # Search candidate
                candidates = self._find_files_matching(target, ["D:\\LARA", os.path.expanduser("~/Downloads"), os.path.expanduser("~/Documents"), os.path.expanduser("~/Desktop")], max_results=1)
                if candidates:
                    file_path = candidates[0]["path"]

            if not os.path.exists(file_path) or os.path.isdir(file_path):
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"❌ File not found: `{target}`",
                    execution_time_ms=round(latency, 2)
                )

            try:
                sz = os.path.getsize(file_path)
                if sz > 2 * 1024 * 1024:
                    return SkillResult(
                        success=False,
                        output=f"File `{file_path}` is too large to display directly ({round(sz / (1024*1024), 2)} MB)."
                    )

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(3000)

                output = (
                    f"📄 **File Content: `{os.path.basename(file_path)}`** (`{file_path}`):\n\n"
                    f"```\n{content}\n```"
                )
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=output,
                    execution_time_ms=round(latency, 2)
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Error reading file `{file_path}`: {e}",
                    execution_time_ms=round(latency, 2)
                )

        # -------------------------------------------------------------
        # Action: Open Folder or File in Native Windows Application
        # -------------------------------------------------------------
        elif action in ["open", "launch", "explorer"]:
            if not os.path.exists(resolved_path):
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"❌ Cannot open: Path `{resolved_path}` does not exist on your system.",
                    execution_time_ms=round(latency, 2)
                )

            try:
                if os.path.isdir(resolved_path):
                    subprocess.Popen(f'explorer "{resolved_path}"', shell=True)
                    label = f"folder **{os.path.basename(resolved_path) or resolved_path}** in Windows File Explorer"
                else:
                    if hasattr(os, "startfile"):
                        os.startfile(resolved_path)
                    else:
                        subprocess.Popen(f'start "" "{resolved_path}"', shell=True)
                    label = f"file **{os.path.basename(resolved_path)}** with its default application"

                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🚀 Opened {label} (`{resolved_path}`).",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Failed to open `{resolved_path}`: {e}",
                    execution_time_ms=round(latency, 2)
                )

        # -------------------------------------------------------------
        # Action: Create File or Folder
        # -------------------------------------------------------------
        elif action in ["create_file", "write_file", "touch"]:
            content = params.get("content", "")
            try:
                os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
                with open(resolved_path, "w", encoding="utf-8") as f:
                    f.write(content)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"✅ Created file `{resolved_path}` with {len(content)} bytes.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Failed to create file `{resolved_path}`: {e}",
                    execution_time_ms=round(latency, 2)
                )

        elif action in ["create_folder", "mkdir", "make_folder"]:
            try:
                os.makedirs(resolved_path, exist_ok=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"✅ Created folder directory `{resolved_path}`.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Failed to create folder `{resolved_path}`: {e}",
                    execution_time_ms=round(latency, 2)
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return SkillResult(
            success=False,
            output=f"Unknown file action: '{action}'. Try 'list files in downloads', 'find pdf files', or 'open folder desktop'.",
            execution_time_ms=round(latency, 2)
        )
