"""Skill registry and intent routing engine."""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.skills.base import BaseSkill, SkillResult
from app.skills.web_search import WebSearchSkill
from app.skills.calendar_reminders import CalendarRemindersSkill
from app.skills.run_code import RunCodeSkill
from app.skills.system_control import SystemControlSkill
from app.skills.mail_hub import MailHubSkill
from app.skills.system_file_hub import SystemFileHubSkill
from app.skills.whatsapp_skill import WhatsAppSkill

logger = logging.getLogger("lara.skills.registry")


class SkillRegistry:
    """Central registry and intent dispatcher for LARA's tool plugins."""

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        """Register default skills."""
        self.register(WebSearchSkill())
        self.register(CalendarRemindersSkill())
        self.register(RunCodeSkill())
        self.register(SystemControlSkill())
        self.register(MailHubSkill())
        self.register(SystemFileHubSkill())
        self.register(WhatsAppSkill())

    def register(self, skill: BaseSkill):
        """Register a new skill into the registry."""
        self._skills[skill.name] = skill
        logger.info("Registered skill: '%s'", skill.name)

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Retrieve skill instance by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all active skills and their metadata."""
        return [skill.to_schema() for skill in self._skills.values()]

    def classify_multi_intent(self, prompt: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Classify single or compound multi-task user prompts (e.g. 'open notepad and check my mail').
        Returns list of (skill_name, params) tuples.
        """
        text = prompt.strip()
        if not text:
            return []

        # 1. Check if this is a unified WhatsApp or Open-and-Type directive
        wa_kw = r"(?:whatsapp|whats\s+app|wtsup|whatsup|wtsp|watsap|watsp|watsapp)"
        is_unified_wa = (
            re.search(rf"open\s+{wa_kw}\s+(?:and\s+)?send\s+message", text, re.IGNORECASE) or
            re.search(rf"send\s+message\s+(?:in|on)\s+{wa_kw}", text, re.IGNORECASE) or
            re.search(rf"open\s+{wa_kw}\s+(?:to\s+)?send\s+message", text, re.IGNORECASE) or
            re.search(rf"^(?:open\s+{wa_kw}\s+(?:and\s+)?)(?:send\s+)?(?:message|msg)?\s*(?:to\s+)", text, re.IGNORECASE)
        )
        is_unified_type = bool(re.search(r"^(?:open|launch|start)\s+[a-zA-Z0-9\s\+\.\#\-_]{2,25}?\s+(?:and\s+)?(?:type|write|text|dictate|enter)\b", text, re.IGNORECASE))

        if not is_unified_wa and not is_unified_type:
            # 2. Check for compound chained instructions (e.g. "open notepad and check my mail")
            parts = re.split(r"\s+(?:and\s+then|then|after\s+that|next|also|\band\b)\s+", text, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]

            if len(parts) > 1:
                matched = []
                for part in parts:
                    res = self.classify_intent(part)
                    if res:
                        matched.append(res)
                if len(matched) >= 2:
                    return matched

        # 3. Fallback to single intent
        single = self.classify_intent(text)
        return [single] if single else []

    def classify_intent(self, prompt: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Classify user prompt into a tool intent and extracted parameters.
        Returns tuple of (skill_name, params) if matched, else None.
        """
        text = prompt.strip()
        
        # Strip leading conversational chaining connectors (e.g. "and...", "now...", "also...", "then...")
        connective_regex = r"^(?:and|then|also|now|after\s+that|next|please|can\s+you|could\s+you|i\s+need\s+you\s+to|i\s+want\s+you\s+to|go\s+ahead\s+and|hey\s+lara|hey\s+laara|laara|lara)[,.:;\s]+"
        cleaned_text = re.sub(connective_regex, "", text, flags=re.IGNORECASE).strip()
        if cleaned_text:
            text = cleaned_text

        lower = text.lower()

        # -------------------------------------------------------------
        # -1. Emergency Stop & Interruption Intent
        # -------------------------------------------------------------
        if lower in ("stop", "stop now", "emergency stop", "cancel", "pause", "halt", "abort", "hey lara stop", "lara stop"):
            return ("system_control", {"action": "emergency_stop", "target": text})

        # -------------------------------------------------------------
        # 0. WhatsApp Messaging, Search & Arbitrary Contact Intent
        # -------------------------------------------------------------
        wa_kw = r"(?:whatsapp|whats\s+app|wtsup|whatsup|wtsp|watsap|watsp|watsapp)"
        sentence_starters = (
            r"(?:saying|that|with\s+message|with\s+msg|message|msg|text|"
            r"please|plz|can\s+you|could\s+you|will|we|i|i\'m|im|are|is|let|lets|let\'s|"
            r"hello|hi|hey|good\s+morning|good\s+evening|the|my|call|check|send|come|meeting|meet|"
            r"where|what|when|why|how|thanks|thank\s+you|happy|congrats|busy|free|urgent|asap|reached|reaching)"
        )

        # Save Contact / Group
        save_contact_match = re.search(r"^(?:save|add)\s+(?:contact|number|phone|group)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+([+0-9\s\-()]{7,20}))?$", text, re.IGNORECASE)
        if save_contact_match:
            c_name = save_contact_match.group(1).strip()
            c_phone = (save_contact_match.group(2) or "").strip()
            return ("whatsapp_hub", {
                "action": "save_contact",
                "name": c_name,
                "phone": c_phone
            })

        # List Contacts: "list contacts", "my contacts", "show contacts", "whatsapp contacts"
        if any(w in lower for w in ["list contacts", "my contacts", "show contacts", "whatsapp contacts", "contacts list", "whatsapp groups"]):
            return ("whatsapp_hub", {"action": "list_contacts"})

        # Pattern 1: "open <wa> and send message to <target> <msg>" with lookahead boundary
        wa_open_send = re.search(
            rf"^(?:open\s+{wa_kw}\s+(?:and\s+)?)(?:send\s+)?(?:message|msg|text)?\s*(?:to\s+)?([a-zA-Z0-9\s_\-\+\.]{{1,35}}?)(?:\s*[:\-]\s*|\s+(?={sentence_starters}\b))(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_open_send and not any(wa_open_send.group(1).lower().startswith(p) for p in ["web", "app", "application", "search"]):
            return ("whatsapp_hub", {"action": "send", "recipient": wa_open_send.group(1).strip(), "message": wa_open_send.group(2).strip()})

        # Pattern 1b: Fallback single/multi word recipient
        wa_open_send_fb = re.search(
            rf"^(?:open\s+{wa_kw}\s+(?:and\s+)?)(?:send\s+)?(?:message|msg|text)?\s*(?:to\s+)?([a-zA-Z0-9_\-\+]+(?:\s+[a-zA-Z0-9_\-\+]+)?)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_open_send_fb and not any(wa_open_send_fb.group(1).lower().startswith(p) for p in ["web", "app", "application", "search"]):
            return ("whatsapp_hub", {"action": "send", "recipient": wa_open_send_fb.group(1).strip(), "message": wa_open_send_fb.group(2).strip()})

        # Pattern 2: "send message in <wa> [search] <target> send <msg>"
        wa_in_match = re.search(
            rf"send\s+(?:a\s+)?(?:message|msg|text)?\s+(?:in|on)\s+{wa_kw}[,\s]+(?:search\s+for\s+|search\s+|to\s+)?([a-zA-Z0-9\s_\-\+\.]{{1,35}}?)(?:[,\s]+(?:after\s+that\s+)?(?:it\s+wants\s+to\s+)?(?:and\s+)?send\s+(?:my\s+)?(?:message|msg)?\s*|\s+(?:saying|that|with\s+message|with\s+msg|message|msg|text|:|->|-)\s*|\s*[:\-]\s*|\s+(?={sentence_starters}\b))(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_in_match:
            return ("whatsapp_hub", {"action": "send", "recipient": wa_in_match.group(1).strip(), "message": wa_in_match.group(2).strip()})

        # Pattern 2b: "send message in <wa> to <target> <msg>" (fallback)
        wa_in_fallback = re.search(
            rf"send\s+(?:a\s+)?(?:message|msg|text)?\s+(?:in|on)\s+{wa_kw}[,\s]+(?:search\s+for\s+|search\s+|to\s+)([a-zA-Z0-9_\-\+]+(?:\s+[a-zA-Z0-9_\-\+]+)?)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_in_fallback:
            return ("whatsapp_hub", {"action": "send", "recipient": wa_in_fallback.group(1).strip(), "message": wa_in_fallback.group(2).strip()})

        # Pattern 3: Explicit Search in WhatsApp and Send
        wa_search_send = re.search(
            rf"(?:(?:open|go\s+to)\s+{wa_kw}\s+(?:and\s+)?(?:search\s+for\s+|search\s+)|(?:search\s+for\s+|search\s+))([a-zA-Z0-9\s_\-\+\.]{{1,35}}?)(?:\s+(?:in|on)\s+{wa_kw})?(?:[,\s]+(?:and\s+send\s+(?:message|msg)?|after\s+that\s+(?:it\s+wants\s+to\s+)?send\s+(?:my\s+)?(?:message|msg)?|send\s+(?:message|msg)?|send|saying|that|with\s+message)\s*|\s*[:\-]\s*)(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_search_send:
            return ("whatsapp_hub", {"action": "send", "recipient": wa_search_send.group(1).strip(), "message": wa_search_send.group(2).strip()})

        # Pattern 4: "send <wa> [message] to <target> <msg>"
        wa_send_to = re.search(
            rf"^(?:send\s+)?{wa_kw}\s+(?:message|msg|text)?\s*(?:to\s+)?([a-zA-Z0-9\s_\-\+\.]{{1,35}}?)(?:\s+(?:saying|that|with\s+message|with\s+msg|message|msg|text|:|->|-)\s*|\s*[:\-]\s*|\s+(?={sentence_starters}\b))(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_send_to and not any(wa_send_to.group(1).lower().startswith(p) for p in ["web", "app", "application", "search"]):
            return ("whatsapp_hub", {"action": "send", "recipient": wa_send_to.group(1).strip(), "message": wa_send_to.group(2).strip()})

        # Pattern 4b: Fallback
        wa_send_to_fallback = re.search(
            rf"^(?:send\s+)?{wa_kw}\s+(?:message|msg|text)?\s*(?:to\s+)?([a-zA-Z0-9_\-\+]+(?:\s+[a-zA-Z0-9_\-\+]+)?)\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_send_to_fallback and not any(wa_send_to_fallback.group(1).lower().startswith(p) for p in ["web", "app", "application", "search"]):
            return ("whatsapp_hub", {"action": "send", "recipient": wa_send_to_fallback.group(1).strip(), "message": wa_send_to_fallback.group(2).strip()})

        # Pattern 5: "send message to <target> on/in <wa> <msg>"
        wa_to_on = re.search(
            rf"^(?:send\s+)?(?:message|msg|text)\s+to\s+([a-zA-Z0-9\s_\-\+\.]{{1,35}}?)\s+(?:on|in)\s+{wa_kw}(?:\s+(?:saying|that|with\s+message|with\s+msg|message|msg|text|:|->|-)\s*|\s*[:\-]\s*|\s+(?={sentence_starters}\b)|\s+)(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_to_on:
            return ("whatsapp_hub", {"action": "send", "recipient": wa_to_on.group(1).strip(), "message": wa_to_on.group(2).strip()})

        # Generic "send message to <name> <msg>" (when not email / mail)
        wa_generic_match = re.search(
            r"^(?:send\s+)?(?:message|msg|text)\s+to\s+([a-zA-Z0-9\s_\-\+]+?)(?:\s+(?:saying|that|with\s+message|message|msg|:)\s*|\s+)(.+)$",
            text,
            re.IGNORECASE
        )
        if wa_generic_match and not any(w in lower for w in ["email", "mail", "gmail", "outlook", "@"]):
            return ("whatsapp_hub", {"action": "send", "recipient": wa_generic_match.group(1).strip(), "message": wa_generic_match.group(2).strip()})

        # Short form: "whatsapp Alex hello"
        if any(lower.startswith(p) for p in ["whatsapp ", "whats app ", "wtsup ", "whatsup ", "wtsp ", "watsap ", "watsp "]):
            parts = text.split(maxsplit=2)
            if len(parts) >= 3 and parts[1].lower() not in ["web", "app", "application", "desktop"]:
                return ("whatsapp_hub", {"action": "send", "recipient": parts[1].strip(), "message": parts[2].strip()})

        # -------------------------------------------------------------
        # 1. Mail & Email Hub Intent
        # -------------------------------------------------------------
        if any(w in lower for w in ["analyze mail", "analyze my mail", "analyze emails", "analyze my emails", "email analysis", "summarize my emails", "summarize emails"]):
            return ("mail_hub", {"action": "analyze"})

        if any(lower.startswith(w) or lower == w for w in [
            "check mail", "check my mail", "check emails", "check my emails",
            "unread emails", "unread mail", "show my mail", "show emails",
            "show unread mail", "show inbox", "inbox summary", "read emails", "my emails", "mail",
            "connect real mail", "connect my mail", "connect gmail", "how to connect my real mail"
        ]) or any(w in lower for w in ["check my mail", "check unread emails", "check my inbox", "what are my emails", "show unread emails", "connect my real mail", "connect my real gmail"]):
            return ("mail_hub", {"action": "check"})

        mail_search_match = re.search(r"^(?:search\s+mail|search\s+email|find\s+email|search\s+inbox)\s+(?:for\s+|from\s+|about\s+)?(.+)$", lower)
        if mail_search_match:
            return ("mail_hub", {"action": "search", "query": mail_search_match.group(1).strip()})

        mail_draft_match = re.search(r"^(?:compose|draft|send|write)\s+(?:email|mail)\s+(?:to\s+)?([^\s@]+@[^\s@]+)?(?:\s+subject\s+(.+?))?(?:\s+body\s+(.+))?$", text, re.IGNORECASE)
        if mail_draft_match and any(w in lower for w in ["email", "mail", "gmail"]):
            to_addr = mail_draft_match.group(1) or "team@example.com"
            subject = mail_draft_match.group(2) or "Direct message from Bunty"
            body = mail_draft_match.group(3) or "Hello from LARA OS."
            return ("mail_hub", {"action": "draft", "to": to_addr, "subject": subject, "body": body})

        if any(w == lower or lower.startswith(w) for w in ["open gmail", "open mail app", "open outlook", "open webmail", "launch gmail"]):
            client = "outlook" if "outlook" in lower else "gmail"
            return ("mail_hub", {"action": "open_client", "client": client})

        # -------------------------------------------------------------
        # 2. System File & Folder Hub Intent
        # -------------------------------------------------------------
        # Listing / Browsing folders: "list files in downloads", "show files in D:\", "browse desktop", "list folder X"
        folder_list_match = re.search(
            r"^(?:list\s+files\s+in|show\s+files\s+in|browse\s+folder|browse|list\s+folder|explore\s+folder|files\s+in)\s+(.+)$",
            lower
        )
        if folder_list_match:
            folder_target = folder_list_match.group(1).strip()
            return ("system_file_hub", {"action": "list", "target": folder_target})

        # Searching files: "find pdf files", "search files about invoice", "find file X", "find python files"
        file_search_match = re.search(
            r"^(?:find|search|lookup)\s+(?:all\s+)?(?:files?\s+about\s+|files?\s+matching\s+|files?\s+named\s+|files?\s+for\s+|files?\s+|documents?\s+about\s+|documents?\s+)?(.+?)(?:\s+files|\s+documents)?$",
            lower
        )
        if file_search_match and any(w in lower for w in ["file", "files", "document", "documents", "pdf", "docx", "py", "txt"]):
            q = file_search_match.group(1).strip()
            # Clean "for", "about", "named"
            q = re.sub(r"^(?:for|about|named|matching)\s+", "", q).strip()
            if q and q not in ["in", "on", "the"]:
                return ("system_file_hub", {"action": "search", "query": q})

        # Reading file content: "read file README.md", "view file notes.txt", "show content of X"
        file_read_match = re.search(
            r"^(?:read\s+file|view\s+file|inspect\s+file|show\s+content\s+of|cat\s+file|read)\s+(?:file\s+)?([a-zA-Z0-9_.\-\\/:\s]+(?:\.[a-zA-Z0-9]{1,6})?)$",
            lower
        )
        if file_read_match:
            target_f = file_read_match.group(1).strip()
            if "." in target_f or "\\" in target_f or "/" in target_f:
                return ("system_file_hub", {"action": "read", "target": target_f})

        # Creating files / folders: "create file note.txt with content Hello", "make folder D:\Projects\App"
        file_create_match = re.search(r"^(?:create\s+file|make\s+file|write\s+file)\s+([^\s]+)(?:\s+with\s+content\s+(.+))?$", text, re.IGNORECASE)
        if file_create_match:
            return ("system_file_hub", {"action": "create_file", "target": file_create_match.group(1).strip(), "content": file_create_match.group(2) or ""})

        # Save summary / document to desktop/downloads
        save_desktop_match = re.search(
            r"^(?:save\s+(?:the\s+|that\s+)?(?:summary|document|file|notes)?\s*(?:on|to|in)\s+(?:my\s+)?(desktop|downloads|documents))(?:\s+(?:as|named)\s+([^\s]+))?$",
            lower
        )
        if save_desktop_match:
            import os
            folder_alias = save_desktop_match.group(1).strip()
            fname = save_desktop_match.group(2) or "Summary.txt"
            target_path = os.path.join(os.path.expanduser("~"), folder_alias.title(), fname)
            return ("system_file_hub", {"action": "create_file", "target": target_path, "content": "Summary document generated by LARA OS."})

        folder_create_match = re.search(r"^(?:create\s+folder|make\s+folder|mkdir)\s+(.+)$", text, re.IGNORECASE)
        if folder_create_match:
            return ("system_file_hub", {"action": "create_folder", "target": folder_create_match.group(1).strip()})

        # -------------------------------------------------------------
        # 3. System Apps, Web Search & Telemetry Intent
        # -------------------------------------------------------------
        if any(w in lower for w in [
            "analyze apps", "list apps", "installed apps", "show apps", "all apps",
            "apps in my system", "what apps", "system apps", "installed programs", "scan apps"
        ]):
            return ("system_control", {"action": "analyze_apps"})

        if any(lower.startswith(p) for p in ["search web for", "search for", "google", "look up", "search on web", "search internet for"]):
            return ("system_control", {"action": "web_search", "target": text})

        if any(w in lower for w in [
            "system stats", "system status", "hardware specs", "cpu usage", "ram usage",
            "memory usage", "battery status", "system metrics", "hardware telemetry", "system info"
        ]):
            return ("system_control", {"action": "stats"})

        # Conversational stop words that must NEVER be misrouted as app launches
        conversational_words = {
            "in", "that", "this", "more", "attractive", "design", "colors", "please", "fixes",
            "fix", "change", "website", "around", "globe", "lines", "neural", "network", "networks",
            "how", "why", "what", "where", "can", "could", "should", "tell", "explain", "help"
        }

        # -------------------------------------------------------------
        # Wispr Flow Auto-Typist & In-App Dictation
        # -------------------------------------------------------------
        # 1. "open <app> and type/write/dictate/enter <text>"
        open_and_type_match = re.search(
            r"^(?:open|launch|start)\s+([a-zA-Z0-9\s\+\.\#\-_]{2,25}?)\s+(?:and\s+)?(?:type|write|text|dictate|enter)\s+(?:text\s+|message\s+|saying\s+|that\s+)?(.+)$",
            text,
            re.IGNORECASE
        )
        if open_and_type_match:
            target_app = open_and_type_match.group(1).strip()
            text_content = open_and_type_match.group(2).strip()
            return ("system_control", {
                "action": "type_text",
                "app": target_app,
                "text": text_content,
                "target": text_content
            })

        # 2. "type <text> in/into/on <app>"
        type_in_app_match = re.search(
            r"^type\s+(.+?)\s+(?:in|into|on)\s+([a-zA-Z0-9\s\+\.\#\-_]{2,25})$",
            text,
            re.IGNORECASE
        )
        if type_in_app_match:
            text_content = type_in_app_match.group(1).strip()
            target_app = type_in_app_match.group(2).strip()
            return ("system_control", {
                "action": "type_text",
                "app": target_app,
                "text": text_content,
                "target": text_content
            })

        # 3. Standalone Dictation / In-App Voice Typist: "type <text>", "dictate <text>", "write text <text>"
        type_standalone_match = re.search(
            r"^(?:type|dictate|write\s+text|copy\s+to\s+clipboard)\s*[:\s]\s*(.+)$",
            text,
            re.IGNORECASE
        )
        if type_standalone_match and not any(lower.startswith(p) for p in ["write code", "write a python", "write python", "write script"]):
            text_content = type_standalone_match.group(1).strip()
            return ("system_control", {
                "action": "type_text",
                "text": text_content,
                "target": text_content
            })

        # Shell Command Execution (CMD & PowerShell)
        if any(lower.startswith(p) for p in ["run cmd ", "cmd /c ", "run terminal "]):
            return ("system_control", {"action": "run_cmd", "target": text})

        if any(lower.startswith(p) for p in ["run powershell ", "powershell -c ", "run ps "]):
            return ("system_control", {"action": "run_powershell", "target": text})

        # -------------------------------------------------------------
        # Native OS Control: Volume, Media, Window, Screen
        # -------------------------------------------------------------
        # Volume
        if any(w in lower for w in ["volume up", "increase volume", "raise volume", "louder", "boost volume"]):
            return ("system_control", {"action": "volume_up", "target": text})

        if any(w in lower for w in ["volume down", "decrease volume", "lower volume", "quieter", "reduce volume"]):
            return ("system_control", {"action": "volume_down", "target": text})

        if any(w in lower for w in ["mute audio", "mute sound", "mute volume", "unmute audio", "unmute sound", "unmute volume", "mute", "unmute"]):
            return ("system_control", {"action": "volume_mute", "target": text})

        # Media Playback
        if any(w in lower for w in ["play music", "pause music", "pause video", "play video", "resume music", "play song", "pause song", "play/pause", "media pause", "media play"]):
            return ("system_control", {"action": "media_play_pause", "target": text})

        if any(w in lower for w in ["next song", "next track", "skip song", "skip track"]):
            return ("system_control", {"action": "media_next", "target": text})

        if any(w in lower for w in ["previous song", "previous track", "prev track", "prev song"]):
            return ("system_control", {"action": "media_prev", "target": text})

        # Window & Screen Management
        if any(w in lower for w in ["close window", "close active window", "close app", "close current window"]):
            return ("system_control", {"action": "close_window", "target": text})

        if any(w in lower for w in ["maximize window", "maximize screen", "fullscreen window", "maximize this"]):
            return ("system_control", {"action": "maximize_window", "target": text})

        if any(w in lower for w in ["switch window", "next window", "switch app"]):
            return ("system_control", {"action": "switch_window", "target": text})

        if any(w in lower for w in ["take screenshot", "capture screen", "screenshot", "screen shot"]):
            return ("system_control", {"action": "screenshot", "target": text})

        # Desktop & Screen Control
        if any(w in lower for w in ["show desktop", "minimize all", "minimize windows"]):
            return ("system_control", {"action": "show_desktop"})

        if any(w in lower for w in ["lock pc", "lock screen", "lock computer"]):
            return ("system_control", {"action": "lock_pc"})

        # Native Folder Opening in Windows Explorer: "open folder downloads", "open desktop", "open downloads folder"
        folder_open_match = re.search(
            r"^(?:open|show|explore)\s+(?:folder|directory|drive)?\s*[:\s]?\s*(desktop|downloads|documents|pictures|music|videos|lara|workspace|c drive|d drive|d:\\|c:\\|[a-zA-Z]:\\[a-zA-Z0-9_.\-\\/]+)$",
            lower
        )
        if folder_open_match:
            return ("system_file_hub", {"action": "open", "target": folder_open_match.group(1).strip()})

        # Universal App & Media Launcher (Strict: Max 3 words, no conversational sentences)
        app_launch_match = re.search(
            r"^(?:open|launch|start)\s+(?:app|application|program)?\s*[:\s]?\s*([a-zA-Z0-9\s\+\.\#\-_]{2,30})$",
            lower
        )
        if app_launch_match:
            app_target = app_launch_match.group(1).strip()
            target_words = set(app_target.split())
            # If target has more than 3 words or contains conversational terms, let Gemini answer
            if len(target_words) <= 3 and not (target_words & conversational_words):
                if not any(app_target.startswith(p) for p in ["code", "python", "remind", "search", "mail", "the"]):
                    return ("system_control", {"action": "launch", "target": app_target})

        # -------------------------------------------------------------
        # 4. Run Code Intent
        # -------------------------------------------------------------
        code_prefix_match = re.search(r"^(?:run\s+code|execute\s+python|run\s+python|calculate|eval|python):\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if code_prefix_match:
            code_content = code_prefix_match.group(1).strip()
            return ("run_code", {"code": code_content})

        if text.startswith("```python") or (text.startswith("```") and "print(" in text):
            return ("run_code", {"code": text})

        # -------------------------------------------------------------
        # 5. Calendar / Reminders Intent
        # -------------------------------------------------------------
        if any(w in lower for w in ["my reminders", "list reminders", "show reminders", "what are my reminders", "list calendar"]):
            return ("calendar_reminders", {"action": "list"})

        rem_add_match = re.search(r"(?:remind\s+me\s+to\s+|set\s+a\s+reminder\s+(?:to|for)\s+)(.+?)(?:\s+(?:at|on|tomorrow|in)\s+(.+))?$", text, re.IGNORECASE)
        if rem_add_match:
            title = rem_add_match.group(1).strip()
            due_time = rem_add_match.group(2).strip() if rem_add_match.group(2) else "Unspecified"
            return ("calendar_reminders", {"action": "create", "title": title, "time": due_time})

        rem_del_match = re.search(r"(?:delete\s+reminder\s+|remove\s+reminder\s+|clear\s+reminder\s+)(.+)", text, re.IGNORECASE)
        if rem_del_match:
            return ("calendar_reminders", {"action": "delete", "title": rem_del_match.group(1).strip()})

        # -------------------------------------------------------------
        # 6. Real-time Date / Time & Web Search Intent
        # -------------------------------------------------------------
        if any(w in lower for w in ["what is the date", "what date is it", "today's date", "current date", "what time is it", "current time"]):
            return ("web_search", {"query": "today's date and current time"})

        search_match = re.search(r"^(?:search\s+the\s+web\s+for|search\s+for|look\s+up|google)\s+(.+)", text, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            return ("web_search", {"query": query})

        return None

    async def route_and_execute(self, prompt: str, user_id: str = "default_user") -> Optional[Tuple[str, SkillResult]]:
        """
        Classify prompt and execute matched skill if found.
        Supports single-turn compound directives (e.g. "open notepad and check my mail").
        """
        intent = self.classify_intent(prompt)
        if intent:
            skill_name, params = intent
            skill = self.get_skill(skill_name)
            if skill:
                logger.info("Routing prompt to skill '%s' with params: %s", skill_name, params)
                result = await skill.execute(params, user_id=user_id)
                return (skill_name, result)

        # Compound multi-task pipeline (e.g. "open c drive and search for invoice files")
        clauses = re.split(r"\s+(?:and\s+then|then|after\s+that|and\s+also|and)\s+", prompt.strip(), flags=re.IGNORECASE)
        if len(clauses) > 1:
            combined_outputs = []
            combined_skills = []
            mutated_any = False
            total_time = 0.0

            for clause in clauses:
                sub_intent = self.classify_intent(clause)
                if sub_intent:
                    s_name, s_params = sub_intent
                    s_inst = self.get_skill(s_name)
                    if s_inst:
                        res = await s_inst.execute(s_params, user_id=user_id)
                        combined_outputs.append(res.output)
                        combined_skills.append(s_name)
                        if res.mutated_state:
                            mutated_any = True
                        total_time += res.execution_time_ms

            if combined_outputs:
                merged_result = SkillResult(
                    success=True,
                    output="\n\n---\n\n".join(combined_outputs),
                    execution_time_ms=round(total_time, 2),
                    mutated_state=mutated_any
                )
                return (", ".join(set(combined_skills)), merged_result)

        return None


# Singleton
skill_registry = SkillRegistry()
