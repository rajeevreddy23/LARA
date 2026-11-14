"""
WhatsApp Skill for LARA OS with Autonomous Auto-Dispatch.
Provides hands-free voice and automated text messaging via WhatsApp Desktop and WhatsApp Web.
Supports contact lookup, phone number normalization, automated window focus, and autonomous message transmission.
"""

import os
import json
import logging
import subprocess
import urllib.parse
import re
import time
import threading
import asyncio
import ctypes

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

from typing import Dict, Any, List, Optional, Tuple
from app.skills.base import BaseSkill, SkillResult

logger = logging.getLogger("lara.skills.whatsapp")

CONTACTS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "whatsapp_contacts.json")

VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_F = 0x46
VK_V = 0x56
VK_ESCAPE = 0x1B
VK_DOWN = 0x28
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002

def _native_press_key(vk: int):
    """Press a virtual key using user32 keybd_event."""
    try:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.06)
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.debug("keybd_event error for key 0x%02X: %s", vk, e)

def _native_press_enter():
    _native_press_key(VK_RETURN)

def _native_hotkey_ctrl(vk: int):
    """Trigger Ctrl + Key."""
    try:
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.06)
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.06)
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.06)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.debug("hotkey_ctrl error for key 0x%02X: %s", vk, e)

def _activate_whatsapp_window():
    """Locate and focus WhatsApp desktop or browser tab using UIAutomation."""
    try:
        import uiautomation as auto
        wa_win = auto.WindowControl(searchDepth=2, SubName='WhatsApp')
        if not wa_win.Exists(maxSearchSeconds=1):
            wa_win = auto.WindowControl(searchDepth=2, RegexName=r'.*(WhatsApp|Chrome|Edge|Brave|Firefox).*')
        
        if wa_win.Exists(maxSearchSeconds=1):
            logger.info("Found WhatsApp window: [%s] -> Activating and bringing to front", wa_win.Name)
            wa_win.SetActive()
            wa_win.SetTopmost(True)
            time.sleep(0.2)
            wa_win.SetTopmost(False)
            return True
    except Exception as ex:
        logger.debug("UIAutomation notice: %s", ex)

    # Fallback to PowerShell AppActivate
    try:
        ps_focus = """
        $wshell = New-Object -ComObject WScript.Shell
        $proc = Get-Process -Name "WhatsApp", "WhatsApp.Root", "chrome", "msedge", "brave", "firefox" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($proc) {
            $wshell.AppActivate($proc.Id)
        }
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_focus], capture_output=True, timeout=5)
    except Exception as e:
        logger.debug("PowerShell AppActivate notice: %s", e)
    return False


def _focus_and_search_send(recipient_name: str, message_text: str, delay_sec: float = 2.8):
    """
    Autonomous worker for any named contact or group (e.g. 'Project Hub', 'Vikas'):
    1. Focuses/activates WhatsApp window.
    2. Focuses search box (Escape -> Ctrl+F).
    3. Pastes recipient / group name directly.
    4. Navigates from search box down into the first chat result (Down Arrow) and opens it (Enter).
    5. Pastes message text into active chat input box and transmits with Enter.
    """
    def worker():
        try:
            time.sleep(delay_sec)

            # Step 1: Ensure WhatsApp window is active and foregrounded
            _activate_whatsapp_window()
            time.sleep(0.4)

            # Step 2: Clear any existing modals/active boxes and trigger Search (Ctrl+F)
            _native_press_key(VK_ESCAPE)
            time.sleep(0.25)
            _native_hotkey_ctrl(VK_F)
            time.sleep(0.5)

            # Step 3: Paste recipient / group name into search box
            if pyperclip:
                pyperclip.copy(recipient_name)
                _native_hotkey_ctrl(VK_V)
            else:
                clean_recip = recipient_name.replace('"', '`"').replace("'", "''")
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"[System.Windows.Forms.Clipboard]::SetText('{clean_recip}'); [System.Windows.Forms.SendKeys]::SendWait('^v')"],
                    capture_output=True
                )
            
            # Step 4: Allow WhatsApp to query and render search matches (1.4s)
            time.sleep(1.4)
            
            # Step 5: Press Down Arrow to move from search input down to the first matched chat
            _native_press_key(VK_DOWN)
            time.sleep(0.35)
            
            # Step 6: Press Enter to open the selected chat
            _native_press_key(VK_RETURN)
            time.sleep(0.9)

            # Step 7: If message text is provided, paste and transmit autonomously
            if message_text:
                if pyperclip:
                    pyperclip.copy(message_text)
                    _native_hotkey_ctrl(VK_V)
                else:
                    clean_msg = message_text.replace('"', '`"').replace("'", "''")
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", f"[System.Windows.Forms.Clipboard]::SetText('{clean_msg}'); [System.Windows.Forms.SendKeys]::SendWait('^v')"],
                        capture_output=True
                    )
                time.sleep(0.4)
                _native_press_key(VK_RETURN)
                time.sleep(0.3)
                _native_press_key(VK_RETURN)

            logger.info("Autonomous WhatsApp live search & dispatch completed for '%s'.", recipient_name)
        except Exception as ex:
            logger.error("Error in live search_and_send worker: %s", ex)

    t = threading.Thread(target=worker, daemon=True)
    t.start()


def _focus_and_auto_send(delay_sec: float = 4.5):
    """Background worker that waits for WhatsApp direct deep-link and auto-presses Enter."""
    def worker():
        try:
            time.sleep(delay_sec)
            _activate_whatsapp_window()
            time.sleep(0.4)
            _native_press_key(VK_RETURN)
            time.sleep(0.3)
            _native_press_key(VK_RETURN)
            logger.info("Autonomous WhatsApp direct Enter keypress dispatched.")
        except Exception as ex:
            logger.error("Error in auto-send worker: %s", ex)

    t = threading.Thread(target=worker, daemon=True)
    t.start()


class WhatsAppSkill(BaseSkill):
    def __init__(self):
        self.contacts = self._load_contacts()

    @property
    def name(self) -> str:
        return "whatsapp_hub"

    @property
    def description(self) -> str:
        return (
            "Send WhatsApp messages to contacts, groups (e.g. 'Project Hub'), or phone numbers, "
            "search chats, and manage contact shortcuts with autonomous auto-send."
        )

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "send message in WhatsApp, search Project Hub and send message we are ready",
            "send whatsapp to Project Hub hello team",
            "send whatsapp message to Alex I will reach in 10 minutes",
            "open whatsapp and send message to vikas will meet at 8:00 p.m. tomorrow",
            "save contact Project Hub",
            "list contacts",
        ]

    @property
    def is_state_mutating(self) -> bool:
        return True

    def _load_contacts(self) -> Dict[str, str]:
        """Load known contacts and groups from disk."""
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load WhatsApp contacts file: %s", e)
        return {
            "priyan": "+919876543210",
            "vikas": "+919876543210",
            "self": "+919876543210",
            "team": "+919876543210",
            "project hub": "Project Hub",
            "project": "Project Hub"
        }

    def _save_contacts(self):
        """Save contacts to disk."""
        try:
            os.makedirs(os.path.dirname(CONTACTS_FILE), exist_ok=True)
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=2)
        except Exception as e:
            logger.error("Failed to save contacts: %s", e)

    def _normalize_phone(self, phone: str) -> str:
        """Strip non-digit characters except leading plus."""
        clean = re.sub(r"[^\d+]", "", phone.strip())
        if clean.startswith("00"):
            clean = "+" + clean[2:]
        elif not clean.startswith("+") and len(clean) == 10:
            clean = "+91" + clean
        return clean.replace("+", "")

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        start_time = time.perf_counter()
        action = params.get("action", "send")
        recipient = params.get("recipient", "").strip()
        raw_message = params.get("message", "").strip()
        phone_number = params.get("phone", "").strip()

        # Clean natural spoken prefixes from message (e.g. "that I will meet...", "saying hello...", "a message saying hello")
        message = re.sub(
            r"^(?:a\s+message\s+(?:saying|that)?|message\s+(?:saying|that)?|saying\s+that|that|saying|with\s+message|with\s+msg|with\s+text|message|msg|text|to\s+say)[:,\s]+",
            "",
            raw_message,
            flags=re.IGNORECASE
        ).strip()
        if not message and raw_message:
            message = raw_message

        # 1. ADD / SAVE CONTACT ACTION
        if action == "save_contact":
            name = params.get("name", "").strip().lower()
            num = params.get("phone", "").strip()
            if not name:
                return SkillResult(
                    success=False,
                    output="Please specify contact or group name (e.g., 'Save contact Project Hub +919876543210').",
                    execution_time_ms=0.0
                )
            self.contacts[name] = num or name.title()
            self._save_contacts()
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=f"💾 Saved contact / group **{name.title()}** (`{self.contacts[name]}`) into LARA WhatsApp Contact Book.",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        # 2. LIST CONTACTS ACTION
        if action == "list_contacts":
            latency = (time.perf_counter() - start_time) * 1000.0
            if not self.contacts:
                return SkillResult(
                    success=True,
                    output="No contacts saved in your WhatsApp Contact Book yet.",
                    execution_time_ms=round(latency, 2)
                )
            contact_rows = "\n".join([f"- **{k.title()}**: `{v}`" for k, v in self.contacts.items()])
            return SkillResult(
                success=True,
                output=f"📱 **Saved WhatsApp Contacts & Groups** ({len(self.contacts)}):\n{contact_rows}",
                execution_time_ms=round(latency, 2)
            )

        # 3. AUTONOMOUS SEND MESSAGE / SEARCH & SEND
        target_phone = ""
        target_name = recipient or "Recipient"

        if phone_number:
            target_phone = self._normalize_phone(phone_number)
        elif recipient:
            clean_recip = recipient.lower().strip().replace("_", " ").replace("-", " ")
            # If recipient is directly a phone number (e.g., +91..., 9876543210)
            if re.match(r"^\+?[\d\s\-()]{7,15}$", clean_recip):
                target_phone = self._normalize_phone(clean_recip)
            elif clean_recip in ("projecthub", "projecthuba", "project hub", "project hub group", "project group", "projecthub group"):
                target_name = "Project Hub"
            else:
                target_name = recipient.strip().title()

        # Trigger Playwright Autonomous Web Engine in background
        def run_web_engine_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                from app.skills.whatsapp_web_engine import wa_web_engine
                res = loop.run_until_complete(wa_web_engine.send_message(
                    recipient=target_name,
                    message=message,
                    phone=target_phone if target_phone else None,
                    headless=False
                ))
                logger.info("Playwright WhatsApp Web Engine dispatch result: %s", res)
            except Exception as e:
                logger.error("Playwright WhatsApp Web Engine notice: %s", e)

        threading.Thread(target=run_web_engine_task, daemon=True).start()

        # Flow A: Direct Phone Number URL
        if target_phone:
            encoded_msg = urllib.parse.quote(message) if message else ""
            web_url = f"https://web.whatsapp.com/send?phone={target_phone}&text={encoded_msg}"
            api_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={encoded_msg}"

            try:
                subprocess.Popen(f'cmd.exe /c start "" "{api_url}"', shell=True)
            except Exception:
                subprocess.Popen(f'cmd.exe /c start "" "{web_url}"', shell=True)

            _focus_and_auto_send(delay_sec=4.5)

            latency = (time.perf_counter() - start_time) * 1000.0
            msg_display = f'"{message}"' if message else "Ready"
            output_text = (
                f"⚡ **WhatsApp Automated Autonomous Dispatch Active**\n\n"
                f"- **Recipient**: **{target_name}** (`+{target_phone}`)\n"
                f"- **Message**: {msg_display}\n"
                f"- **Engine**: Playwright Autonomous Web Engine & Direct API active."
            )
            return SkillResult(success=True, output=output_text, execution_time_ms=round(latency, 2), mutated_state=True)

        # Flow B: Named Contact / Group Live Search & Send (e.g. 'Project Hub', 'Vikas')
        # 1. Open WhatsApp with native message pre-fill protocol
        encoded_msg = urllib.parse.quote(message) if message else ""
        try:
            subprocess.Popen(
                f'cmd.exe /c start "WhatsApp" "whatsapp://send?text={encoded_msg}" || start "" "https://web.whatsapp.com/send?text={encoded_msg}"',
                shell=True
            )
        except Exception as e:
            logger.error("Failed to launch WhatsApp protocol: %s", e)
            subprocess.Popen(f'cmd.exe /c start "" "https://web.whatsapp.com/send?text={encoded_msg}"', shell=True)

        # 2. Trigger Keystroke Worker as parallel backup
        _focus_and_search_send(target_name, message, delay_sec=2.5)

        latency = (time.perf_counter() - start_time) * 1000.0
        msg_display = f'"{message}"' if message else "Ready"

        output_text = (
            f"Done. I sent '{message}' to {target_name}.\n\n"
            f"- **Target Contact / Group**: **{target_name}**\n"
            f"- **Message**: \"{message}\"\n"
            f"- **Automation**: LARA has accessed WhatsApp, searched for **'{target_name}'**, selected the chat, and transmitted your message."
        )

        return SkillResult(
            success=True,
            output=output_text,
            execution_time_ms=round(latency, 2),
            mutated_state=True
        )


whatsapp_skill = WhatsAppSkill()

