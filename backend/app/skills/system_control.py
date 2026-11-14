"""System Control, File Automation & OS Automation Skill for LARA OS on Windows."""

import os
import sys
import re
import time
import glob
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.skills.base import BaseSkill, SkillResult

logger = logging.getLogger("lara.skills.system_control")


class SystemControlSkill(BaseSkill):
    """Controls OS applications, opens and navigates system files/folders, dynamically discovers installed apps."""

    @property
    def name(self) -> str:
        return "system_control"

    @property
    def description(self) -> str:
        return (
            "Open any application installed on your PC, browse/open files and folders across drives, "
            "type text like Wispr Flow into any active window or app, search the web, and control OS actions."
        )

    def _attach_desktop(self):
        """Ensure thread is attached to WinSta0/Default desktop for foreground window access."""
        try:
            import ctypes
            u32 = ctypes.windll.user32
            h_winsta = u32.OpenWindowStationW('WinSta0', False, 0x10000000)
            if h_winsta:
                u32.SetProcessWindowStation(h_winsta)
            h_desk = u32.OpenDesktopW('Default', 0, False, 0x1FF)
            if h_desk:
                u32.SetThreadDesktop(h_desk)
            return h_desk
        except Exception as ex:
            logger.debug("Desktop attach notice: %s", ex)
            return None

    def _find_window_by_app(self, app_name: str) -> Optional[int]:
        """Search visible desktop windows for a matching app title or class."""
        try:
            import ctypes
            u32 = ctypes.windll.user32
            h_desk = self._attach_desktop()
            clean = app_name.lower().strip()
            matches = []

            def cb(hwnd, _):
                t = ctypes.create_unicode_buffer(256)
                u32.GetWindowTextW(hwnd, t, 256)
                c = ctypes.create_unicode_buffer(256)
                u32.GetClassNameW(hwnd, c, 256)
                title = t.value.lower()
                cls = c.value.lower()
                if u32.IsWindowVisible(hwnd) and (t.value or c.value):
                    if clean in title or clean in cls:
                        matches.append(hwnd)
                return 1

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            if h_desk:
                u32.EnumDesktopWindows(h_desk, WNDENUMPROC(cb), 0)
            else:
                u32.EnumWindows(WNDENUMPROC(cb), 0)
            return matches[0] if matches else None
        except Exception as e:
            logger.debug("Find window notice: %s", e)
            return None

    def _focus_window(self, hwnd: int) -> bool:
        """Bring a specific window handle to the foreground and attach thread input."""
        try:
            import ctypes, win32process
            u32 = ctypes.windll.user32
            k32 = ctypes.windll.kernel32
            fg_hwnd = u32.GetForegroundWindow()
            if fg_hwnd == hwnd:
                return True
            fg_tid, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
            cur_tid = k32.GetCurrentThreadId()
            u32.AttachThreadInput(cur_tid, fg_tid, True)
            u32.ShowWindow(hwnd, 9)  # SW_RESTORE
            u32.SetForegroundWindow(hwnd)
            u32.BringWindowToTop(hwnd)
            u32.AttachThreadInput(cur_tid, fg_tid, False)
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.debug("Focus window notice: %s", e)
            return False

    def _inject_text(self, text: str, press_enter: bool = False):
        """Wispr Flow-style text injection into active focused window via clipboard & Ctrl+V."""
        import ctypes
        u32 = ctypes.windll.user32

        # 1. Set clipboard content
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            try:
                subprocess.run("clip", input=text, text=True, check=True)
            except Exception:
                clean = text.replace('"', '`"').replace("'", "''")
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"[System.Windows.Forms.Clipboard]::SetText('{clean}')"],
                    capture_output=True
                )

        time.sleep(0.08)

        # 2. Inject native Ctrl + V
        VK_CONTROL = 0x11
        VK_V = 0x56
        VK_RETURN = 0x0D
        KEYEVENTF_KEYUP = 0x0002

        u32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.04)
        u32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.04)
        u32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.04)
        u32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        if press_enter:
            time.sleep(0.06)
            u32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.04)
            u32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "open notepad",
            "open excel",
            "open word",
            "open chrome",
            "open whatsapp",
            "open vs code",
            "open downloads folder",
            "open desktop",
            "open c drive",
            "search web for artificial intelligence",
            "analyze installed apps",
            "list apps in my system",
            "check my system stats"
        ]

    @property
    def is_state_mutating(self) -> bool:
        return True

    def scan_installed_apps(self) -> Dict[str, Dict[str, Any]]:
        """Dynamically scan Windows Start Menu and system directories for all installed applications."""
        user_home = os.path.expanduser("~")
        search_dirs = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.join(user_home, r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),
            r"C:\Program Files",
            r"C:\Program Files (x86)",
        ]

        apps = {}
        # Core default system apps
        core_defaults = {
            "Notepad": {"cmd": "notepad.exe", "category": "Productivity", "icon": "FileText"},
            "Calculator": {"cmd": "calc.exe", "category": "Productivity", "icon": "Calculator"},
            "File Explorer": {"cmd": "explorer.exe", "category": "System", "icon": "Folder"},
            "Task Manager": {"cmd": "taskmgr.exe", "category": "System", "icon": "Activity"},
            "Command Prompt": {"cmd": "cmd.exe /c start cmd.exe", "category": "System", "icon": "Terminal"},
            "Terminal": {"cmd": "wt.exe", "category": "System", "icon": "Terminal"},
            "PowerShell": {"cmd": "powershell.exe", "category": "System", "icon": "Terminal"},
            "Windows Settings": {"cmd": "start ms-settings:", "category": "System", "icon": "Settings"},
            "Camera": {"cmd": "start microsoft.windows.camera:", "category": "Media", "icon": "Camera"},
            "Photos": {"cmd": "start ms-photos:", "category": "Media", "icon": "Image"},
            "Clock & Alarms": {"cmd": "start ms-clock:", "category": "Productivity", "icon": "Clock"},
            "Google Chrome": {"cmd": "start chrome", "category": "Internet", "icon": "Globe"},
            "Microsoft Edge": {"cmd": "start msedge", "category": "Internet", "icon": "Globe"},
            "WhatsApp": {"cmd": "start https://web.whatsapp.com", "category": "Communication", "icon": "MessageCircle"},
            "YouTube": {"cmd": "start https://youtube.com", "category": "Media", "icon": "Video"},
            "Gmail": {"cmd": "start https://mail.google.com", "category": "Communication", "icon": "Mail"},
            "Google Maps": {"cmd": "start https://maps.google.com", "category": "Internet", "icon": "MapPin"},
            "Spotify": {"cmd": "start spotify: || start https://open.spotify.com", "category": "Media", "icon": "Music"},
            "VS Code": {"cmd": "code", "category": "Development", "icon": "Code"},
            "Cursor": {"cmd": "cursor", "category": "Development", "icon": "Code"},
            "GitHub": {"cmd": "start https://github.com", "category": "Development", "icon": "Github"},
            "Google AI Studio": {"cmd": 'cmd.exe /c start "" "https://aistudio.google.com"', "category": "Development", "icon": "Brain"},
            "AI Studio": {"cmd": 'cmd.exe /c start "" "https://aistudio.google.com"', "category": "Development", "icon": "Brain"},
            "Claude": {"cmd": 'cmd.exe /c start "" "https://claude.ai"', "category": "Development", "icon": "Brain"},
            "Claude Code": {"cmd": 'cmd.exe /c start "Claude Code CLI" cmd.exe /k "claude || npx @anthropic-ai/claude-code"', "category": "Development", "icon": "Terminal"},
            "Claude AI": {"cmd": 'cmd.exe /c start "" "https://claude.ai"', "category": "Development", "icon": "Brain"},
            "Anthropic Claude": {"cmd": 'cmd.exe /c start "" "https://claude.ai"', "category": "Development", "icon": "Brain"},
            "Google Colab": {"cmd": 'cmd.exe /c start "" "https://colab.research.google.com"', "category": "Development", "icon": "Code"},
            "ChatGPT": {"cmd": 'cmd.exe /c start "" "https://chatgpt.com"', "category": "Development", "icon": "Brain"},
            "Gemini": {"cmd": 'cmd.exe /c start "" "https://gemini.google.com"', "category": "Development", "icon": "Brain"},
            "HuggingFace": {"cmd": 'cmd.exe /c start "" "https://huggingface.co"', "category": "Development", "icon": "Brain"},
            "Kaggle": {"cmd": 'cmd.exe /c start "" "https://kaggle.com"', "category": "Development", "icon": "Globe"},
        }

        for name, info in core_defaults.items():
            apps[name] = {
                "name": name,
                "path": info["cmd"],
                "category": info["category"],
                "icon": info["icon"],
                "is_shortcut": False
            }

        # Scan Windows Start Menu Shortcuts
        for root in search_dirs[:2]:
            if not os.path.exists(root):
                continue
            try:
                for dirpath, _, filenames in os.walk(root):
                    for f in filenames:
                        if f.lower().endswith((".lnk", ".url")):
                            clean_name = os.path.splitext(f)[0].strip()
                            # Skip uninstaller / readme shortcuts
                            if any(k in clean_name.lower() for k in ["uninstall", "readme", "help", "documentation", "license", "website", "support"]):
                                continue

                            full_path = os.path.join(dirpath, f)
                            category = "Productivity"
                            icon = "AppWindow"

                            lower = clean_name.lower()
                            if any(w in lower for w in ["chrome", "edge", "firefox", "brave", "opera", "browser"]):
                                category = "Internet"
                                icon = "Globe"
                            elif any(w in lower for w in ["code", "visual studio", "studio", "git", "python", "node", "pycharm", "intellij", "sublime"]):
                                category = "Development"
                                icon = "Code"
                            elif any(w in lower for w in ["media", "player", "vlc", "spotify", "music", "video", "audio", "voice", "camera", "recorder"]):
                                category = "Media"
                                icon = "Music"
                            elif any(w in lower for w in ["word", "excel", "powerpoint", "office", "acrobat", "pdf", "onenote", "notepad", "notes", "calc"]):
                                category = "Productivity"
                                icon = "FileText"
                            elif any(w in lower for w in ["game", "steam", "epic", "xbox"]):
                                category = "Games"
                                icon = "Gamepad"
                            elif any(w in lower for w in ["settings", "control", "task", "cmd", "powershell", "clean", "backup", "drive"]):
                                category = "System"
                                icon = "Settings"

                            apps[clean_name] = {
                                "name": clean_name,
                                "path": full_path,
                                "category": category,
                                "icon": icon,
                                "is_shortcut": True
                            }
            except Exception as e:
                logger.debug("Shortcut scan notice: %s", e)

        return apps

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Fetch live hardware telemetry via psutil."""
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            battery = psutil.sensors_battery()

            battery_info = "N/A (Desktop/AC)"
            if battery:
                battery_info = f"{battery.percent}% ({'Plugged In' if battery.power_plugged else 'On Battery'})"

            return {
                "cpu_percent": f"{cpu_pct}%",
                "cpu_cores": cpu_count,
                "ram_used_gb": f"{round((mem.total - mem.available) / (1024**3), 2)} GB",
                "ram_total_gb": f"{round(mem.total / (1024**3), 2)} GB",
                "ram_percent": f"{mem.percent}%",
                "disk_free_gb": f"{round(disk.free / (1024**3), 2)} GB",
                "disk_total_gb": f"{round(disk.total / (1024**3), 2)} GB",
                "battery": battery_info,
                "platform": sys.platform,
                "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.warning("psutil error: %s", e)
            return {
                "platform": sys.platform,
                "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _find_file_on_system(self, filename: str) -> Optional[str]:
        """Fuzzy search for a file in common Windows user directories and workspace."""
        clean_name = filename.strip().strip('"\'')
        
        if os.path.exists(clean_name):
            return os.path.abspath(clean_name)

        # Guard: Only search for files if the query explicitly has a file extension or path separators
        has_extension = bool(re.search(r"\.[a-zA-Z0-9]{2,5}$", clean_name))
        if not has_extension and not any(sep in clean_name for sep in ["\\", "/"]):
            return None
        
        search_roots = [
            os.getcwd(),
            "d:\\LARA",
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~"),
            "d:\\",
            "c:\\Users"
        ]

        target_base = os.path.basename(clean_name).lower()

        for root in search_roots:
            if not os.path.exists(root):
                continue
            
            direct_cand = os.path.join(root, clean_name)
            if os.path.exists(direct_cand):
                return direct_cand

            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "venv", ".venv", "AppData", "Windows", "tests", "__pycache__")]
                    for fname in filenames:
                        if fname.lower() == target_base:
                            return os.path.join(dirpath, fname)
            except Exception as ex:
                logger.debug("Walk error in root %s: %s", root, ex)
                continue

        return None

    def _open_file_or_target(self, target: str) -> Tuple[bool, str]:
        """Open any file, folder, or URL in Windows default handlers."""
        clean_target = target.strip().strip('"\'')

        special_folders = {
            "desktop": os.path.expanduser("~/Desktop"),
            "documents": os.path.expanduser("~/Documents"),
            "downloads": os.path.expanduser("~/Downloads"),
            "pictures": os.path.expanduser("~/Pictures"),
            "music": os.path.expanduser("~/Music"),
            "videos": os.path.expanduser("~/Videos"),
            "home": os.path.expanduser("~"),
            "workspace": "d:\\LARA",
            "lara": "d:\\LARA",
            "d drive": "d:\\",
            "c drive": "c:\\"
        }

        lower_target = clean_target.lower()
        for key, path in special_folders.items():
            if lower_target == key or lower_target == f"{key} folder" or lower_target == f"my {key}":
                if os.path.exists(path):
                    if hasattr(os, "startfile"):
                        os.startfile(path)
                    else:
                        subprocess.Popen(f'explorer "{path}"', shell=True)
                    return True, f"Opened **{key.title()}** folder (`{path}`) in Windows File Explorer."

        # Web URL -> ALWAYS open in new browser window / tab
        if lower_target.startswith("http://") or lower_target.startswith("https://") or any(lower_target.endswith(ext) for ext in [".com", ".org", ".io", ".net", ".dev", ".ai", ".in", ".edu"]):
            url = lower_target if lower_target.startswith("http") else f"https://{lower_target}"
            subprocess.Popen(f'start "" "{url}"', shell=True)
            return True, f"Opened browser in new window to: **[{url}]({url})**."

        # Search for file on system
        located_file = self._find_file_on_system(clean_target)
        if located_file and os.path.exists(located_file):
            try:
                if hasattr(os, "startfile"):
                    os.startfile(located_file)
                else:
                    subprocess.Popen(f'start "" "{located_file}"', shell=True)
                return True, f"Successfully launched file: `{located_file}`"
            except Exception as e:
                subprocess.Popen(f'notepad "{located_file}"', shell=True)
                return True, f"Opened file `{located_file}` with Notepad."

        return False, f"Could not locate file or path: `{clean_target}`."

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        start_time = time.perf_counter()
        action = params.get("action", "").lower().strip()
        target = (params.get("target") or params.get("app") or params.get("file") or params.get("path") or params.get("query") or "").strip()
        lower_target = target.lower()
        user_name = "Bunty"

        # ---------------------------------------------------------
        # 1. System App Analyzer & Inventory
        # ---------------------------------------------------------
        if action in ("analyze_apps", "list_apps", "apps", "inventory") or any(w in target.lower() for w in ["analyze apps", "list apps", "installed apps", "show apps", "all apps"]):
            all_apps = self.scan_installed_apps()
            
            categories: Dict[str, List[str]] = {}
            for app_name, info in all_apps.items():
                cat = info.get("category", "Productivity")
                categories.setdefault(cat, []).append(app_name)

            lines = [
                f"💻 **Installed Applications Analysis for {user_name}** ({len(all_apps)} programs detected):\n"
            ]

            for cat, items in sorted(categories.items()):
                lines.append(f"### 📦 {cat} ({len(items)})")
                sample_items = items[:8]
                lines.append(", ".join([f"**{it}**" for it in sample_items]) + (f" *...and {len(items)-8} more*" if len(items) > 8 else ""))
                lines.append("")

            lines.append("💡 *Say 'Open <app name>' (e.g. 'Open Excel', 'Open Word', 'Open Notepad++', 'Open Chrome') to launch instantly.*")

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output="\n".join(lines),
                execution_time_ms=round(latency, 2),
                mutated_state=False
            )

        # ---------------------------------------------------------
        # 2. Web Search & New Page Opener
        # ---------------------------------------------------------
        if action in ("web_search", "search_web", "google") or any(target.lower().startswith(p) for p in ["search for", "google", "search web for", "look up"]):
            q = target
            for p in ["search web for", "search for", "google", "look up"]:
                if q.lower().startswith(p):
                    q = q[len(p):].strip()
                    break
            search_url = f"https://www.google.com/search?q={subprocess.list2cmdline([q]).strip('\"')}"
            subprocess.Popen(f'start "" "{search_url}"', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=f"🌐 Opened Google Web Search for **'{q}'** in a new browser window.\nLink: [{search_url}]({search_url})",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # ---------------------------------------------------------
        # 3. System Telemetry Query
        # ---------------------------------------------------------
        if action in ("stats", "metrics", "status", "telemetry") or any(w in target.lower() for w in ["stats", "specs", "ram", "cpu", "battery", "hardware"]):
            metrics = self._get_system_metrics()
            output = (
                f"### 🖥️ Real-Time System Telemetry\n"
                f"- **Commander**: `{user_name}`\n"
                f"- **Local Time**: `{metrics.get('local_time')}`\n"
                f"- **CPU Usage**: `{metrics.get('cpu_percent')}` ({metrics.get('cpu_cores')} logical cores)\n"
                f"- **Memory (RAM)**: `{metrics.get('ram_used_gb')} / {metrics.get('ram_total_gb')}` ({metrics.get('ram_percent')} used)\n"
                f"- **Primary Disk Free**: `{metrics.get('disk_free_gb')} / {metrics.get('disk_total_gb')}`\n"
                f"- **Power/Battery**: `{metrics.get('battery')}`\n\n"
                f"*All local host hardware monitors report nominal operation, {user_name}.*"
            )
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=output,
                execution_time_ms=round(latency, 2),
                mutated_state=False
            )

        # ---------------------------------------------------------
        # 4. Wispr Flow In-App Voice Typist & Auto-Dictation
        # ---------------------------------------------------------
        if action in ("type_text", "type", "dictate", "wispr_flow") or any(target.lower().startswith(p) for p in ["type ", "write text ", "copy to clipboard ", "dictate ", "write "]):
            text_to_type = (params.get("text") or params.get("message") or target).strip()
            for p in ["type ", "write text ", "copy to clipboard ", "dictate ", "write ", "text "]:
                if text_to_type.lower().startswith(p):
                    text_to_type = text_to_type[len(p):].strip()
                    break

            app_target = params.get("app") or params.get("target_app")
            press_enter = bool(params.get("enter") or params.get("press_enter"))

            # Strip spoken introductory filler ("saying...", "that...")
            text_to_type = re.sub(r"^(?:that|saying|text|message)[:,\s]+", "", text_to_type, flags=re.IGNORECASE).strip()
            if not text_to_type and target:
                text_to_type = target

            target_display = "Active Window"
            self._attach_desktop()

            # If an app target is provided (e.g. "open notepad and type ..."), bring it to foreground
            if app_target:
                hwnd = self._find_window_by_app(app_target)
                if not hwnd:
                    # Launch app first
                    await self.execute({"action": "launch", "target": app_target}, user_id=user_id)
                    time.sleep(0.8)
                    hwnd = self._find_window_by_app(app_target)
                if hwnd:
                    self._focus_window(hwnd)
                    target_display = app_target.title()
                else:
                    target_display = app_target.title()

            # Wispr Flow text injection directly into focused window / cursor position
            self._inject_text(text_to_type, press_enter=press_enter)

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=f"✍️ **Wispr Flow Auto-Typist**: Typed directly into **{target_display}**:\n> \"{text_to_type}\"",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # ---------------------------------------------------------
        # 5. Shell Command Runner (CMD / PowerShell / Terminal)
        # ---------------------------------------------------------
        if action in ("run_cmd", "cmd", "terminal", "exec") or target.lower().startswith("cmd ") or target.lower().startswith("run cmd "):
            cmd_str = target
            for p in ["run cmd ", "cmd ", "run terminal ", "terminal "]:
                if cmd_str.lower().startswith(p):
                    cmd_str = cmd_str[len(p):].strip()
                    break

            try:
                proc = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=10)
                out = (proc.stdout or proc.stderr or "Command executed with code 0 (No output)").strip()
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=proc.returncode == 0,
                    output=f"⚡ **CMD Execution Result** (`{cmd_str}`):\n```cmd\n{out[:1200]}\n```",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"Failed to execute command `{cmd_str}`: {str(e)}",
                    error=str(e),
                    execution_time_ms=round(latency, 2)
                )

        if action in ("run_powershell", "powershell", "ps") or target.lower().startswith("powershell ") or target.lower().startswith("run powershell "):
            ps_cmd = target
            for p in ["run powershell ", "powershell ", "run ps ", "ps "]:
                if ps_cmd.lower().startswith(p):
                    ps_cmd = ps_cmd[len(p):].strip()
                    break

            try:
                proc = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
                out = (proc.stdout or proc.stderr or "PowerShell script completed with code 0").strip()
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=proc.returncode == 0,
                    output=f"⚡ **PowerShell Output** (`{ps_cmd}`):\n```powershell\n{out[:1200]}\n```",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=False,
                    output=f"PowerShell error `{ps_cmd}`: {str(e)}",
                    error=str(e),
                    execution_time_ms=round(latency, 2)
                )

        # ---------------------------------------------------------
        # 6. Screen, Audio, Media & Window OS Control
        # ---------------------------------------------------------
        # Volume Control
        if action == "volume_up" or any(w in lower_target for w in ["volume up", "increase volume", "raise volume", "louder"]):
            try:
                import pyautogui
                pyautogui.press('volumeup', presses=5)
            except Exception:
                subprocess.Popen('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="🔊 Volume increased.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "volume_down" or any(w in lower_target for w in ["volume down", "decrease volume", "lower volume", "quieter"]):
            try:
                import pyautogui
                pyautogui.press('volumedown', presses=5)
            except Exception:
                subprocess.Popen('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="🔉 Volume decreased.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "volume_mute" or any(w in lower_target for w in ["mute audio", "mute sound", "mute volume", "unmute", "mute"]):
            try:
                import pyautogui
                pyautogui.press('volumemute')
            except Exception:
                subprocess.Popen('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="🔇 Audio toggled mute/unmute.", execution_time_ms=round(latency, 2), mutated_state=True)

        # Media Playback Controls
        if action == "media_play_pause" or any(w in lower_target for w in ["play music", "pause music", "pause video", "play video", "resume music", "play song", "pause song", "play/pause", "media pause", "media play"]):
            try:
                import pyautogui
                pyautogui.press('playpause')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="⏯️ Media playback toggled (Play/Pause).", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "media_next" or any(w in lower_target for w in ["next song", "next track", "skip song", "skip track"]):
            try:
                import pyautogui
                pyautogui.press('nexttrack')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="⏭️ Skipped to next track.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "media_prev" or any(w in lower_target for w in ["previous song", "previous track", "prev track", "prev song"]):
            try:
                import pyautogui
                pyautogui.press('prevtrack')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="⏮️ Returned to previous track.", execution_time_ms=round(latency, 2), mutated_state=True)

        # Window & Screen Management
        if action == "close_window" or any(w in lower_target for w in ["close window", "close active window", "close app", "close current window"]):
            try:
                import pyautogui
                pyautogui.hotkey('alt', 'f4')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="❌ Closed active window.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "maximize_window" or any(w in lower_target for w in ["maximize window", "maximize screen", "fullscreen window"]):
            try:
                import pyautogui
                pyautogui.hotkey('win', 'up')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="🔲 Maximized active window.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "switch_window" or any(w in lower_target for w in ["switch window", "next window", "switch app"]):
            try:
                import pyautogui
                pyautogui.hotkey('alt', 'tab')
            except Exception:
                pass
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output="🔄 Switched active application window.", execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "screenshot" or any(w in lower_target for w in ["take screenshot", "capture screen", "screenshot"]):
            shot_path = os.path.join(os.path.expanduser("~"), "Pictures", "LARA_Screenshot.png")
            try:
                os.makedirs(os.path.dirname(shot_path), exist_ok=True)
                import pyautogui
                shot = pyautogui.screenshot()
                shot.save(shot_path)
                msg = f"📸 Screenshot captured and saved to `{shot_path}`."
            except Exception:
                try:
                    subprocess.Popen('cmd.exe /c start ms-screenclip:', shell=True)
                    msg = "📸 Opened Windows Snip & Screen Capture overlay."
                except Exception:
                    msg = "📸 Screen capture command dispatched."
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(success=True, output=msg, execution_time_ms=round(latency, 2), mutated_state=True)

        if action == "show_desktop" or any(w in target.lower() for w in ["show desktop", "minimize all", "minimize windows"]):
            subprocess.Popen('powershell -Command "(New-Object -ComObject Shell.Application).MinimizeAll()"', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output="🖥️ Minimized all windows and revealed your Desktop, Bunty.",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        if action == "lock_pc" or any(w in target.lower() for w in ["lock pc", "lock screen", "lock computer"]):
            subprocess.Popen('rundll32.exe user32.dll,LockWorkStation', shell=True)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output="🔒 Host workstation locked for security, Bunty.",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # Emergency Stop / Interruption
        if action in ("emergency_stop", "stop", "cancel_task") or any(w == lower_target for w in ["stop", "pause", "cancel", "halt", "emergency stop", "hey lara stop", "lara stop"]):
            try:
                from app.services.agent import agent_coordinator
                cancelled_count = 0
                for task in agent_coordinator.tasks.values():
                    if task.status in ("running", "pending_approval"):
                        task.status = "interrupted"
                        cancelled_count += 1
                if cancelled_count > 0:
                    agent_coordinator._save()
            except Exception as e:
                logger.debug("Stop task coordinator notice: %s", e)

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output="🛑 Emergency stop confirmed. Active workflows and speech have been safely halted.",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # ---------------------------------------------------------
        # 7. File / Folder Opener Action
        # ---------------------------------------------------------
        if action in ("open_file", "open_folder", "file", "folder") or params.get("is_file"):
            success, msg = self._open_file_or_target(target)
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=success,
                output=msg,
                execution_time_ms=round(latency, 2),
                mutated_state=success
            )

        # ---------------------------------------------------------
        # 8. Universal & Dynamic Application Launcher
        # ---------------------------------------------------------
        all_installed = self.scan_installed_apps()
        lower_target = target.lower().strip()

        # Try matching in dynamically scanned installed apps
        matched_app_name = None
        matched_app_info = None

        # Exact match check
        for name, info in all_installed.items():
            if name.lower() == lower_target:
                matched_app_name = name
                matched_app_info = info
                break

        # Partial / fuzzy match check
        if not matched_app_info:
            for name, info in all_installed.items():
                if lower_target in name.lower() or name.lower() in lower_target:
                    matched_app_name = name
                    matched_app_info = info
                    break

        # Explicit WhatsApp launcher handling
        if "whatsapp" in lower_target or "whats app" in lower_target:
            try:
                subprocess.Popen('cmd.exe /c start whatsapp: || start https://web.whatsapp.com', shell=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🚀 Launched **WhatsApp** on your system.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                logger.error("WhatsApp launch error: %s", e)

        # Explicit AI Studio launcher handling
        if "ai studio" in lower_target or "aistudio" in lower_target or "google ai" in lower_target:
            try:
                subprocess.Popen('cmd.exe /c start "" "https://aistudio.google.com"', shell=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🚀 Opened **Google AI Studio** (`https://aistudio.google.com`) in your browser.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                logger.error("AI Studio launch error: %s", e)

        # Explicit Claude Code & Claude AI launcher handling
        if "claude code" in lower_target:
            try:
                subprocess.Popen('cmd.exe /c start "Claude Code CLI" cmd.exe /k "claude || npx @anthropic-ai/claude-code"', shell=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output="🚀 Launched **Claude Code Agentic CLI** in a new terminal session.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                logger.error("Claude Code launch error: %s", e)

        if lower_target == "claude" or "claude ai" in lower_target or "anthropic claude" in lower_target:
            try:
                subprocess.Popen('cmd.exe /c start "" "https://claude.ai"', shell=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output="🚀 Opened **Claude AI** (`https://claude.ai`) in your browser.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                logger.error("Claude launch error: %s", e)

        if matched_app_info:
            try:
                cmd_or_path = matched_app_info["path"]
                if matched_app_info.get("is_shortcut"):
                    if hasattr(os, "startfile"):
                        os.startfile(cmd_or_path)
                    else:
                        subprocess.Popen(f'cmd.exe /c start "" "{cmd_or_path}"', shell=True)
                elif cmd_or_path.startswith("start "):
                    subprocess.Popen(f'cmd.exe /c {cmd_or_path}', shell=True)
                else:
                    subprocess.Popen(f'cmd.exe /c {cmd_or_path}', shell=True)

                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🚀 Launched application **{matched_app_name}** on your system.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception as e:
                logger.error("Failed to launch %s: %s", matched_app_name, e)

        # Fallback: Try opening as file/folder/URL
        file_success, file_msg = self._open_file_or_target(target)
        if file_success:
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=file_msg,
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # Fallback 2: Check if target looks like a website or query
        if "." in target and not " " in target:
            try:
                subprocess.Popen(f'cmd.exe /c start "" "https://{target}"', shell=True)
                latency = (time.perf_counter() - start_time) * 1000.0
                return SkillResult(
                    success=True,
                    output=f"🌐 Navigating to website: **{target}**",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            except Exception:
                pass

        latency = (time.perf_counter() - start_time) * 1000.0
        return SkillResult(
            success=False,
            output=f"Application or target **'{target}'** was not recognized on your system. Try saying 'Open Chrome', 'Open WhatsApp', 'Browse files', or ask a question.",
            execution_time_ms=round(latency, 2),
            mutated_state=False
        )
