"""LARA Skills and Tool Plugins Package."""

from app.skills.base import BaseSkill, SkillResult
from app.skills.registry import skill_registry, SkillRegistry
from app.skills.web_search import WebSearchSkill
from app.skills.calendar_reminders import CalendarRemindersSkill
from app.skills.run_code import RunCodeSkill
from app.skills.system_control import SystemControlSkill
from app.skills.mail_hub import MailHubSkill
from app.skills.system_file_hub import SystemFileHubSkill

__all__ = [
    "BaseSkill",
    "SkillResult",
    "skill_registry",
    "SkillRegistry",
    "WebSearchSkill",
    "CalendarRemindersSkill",
    "RunCodeSkill",
    "SystemControlSkill",
    "MailHubSkill",
    "SystemFileHubSkill",
]
