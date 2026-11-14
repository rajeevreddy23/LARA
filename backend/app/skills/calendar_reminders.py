"""Calendar & Reminders skill backed by LARA memory store."""

import time
import os
import json
from typing import Dict, Any, List
from datetime import datetime
from app.skills.base import BaseSkill, SkillResult
from app.config import settings

REMINDERS_FILE = os.path.join(settings.LOCAL_DATA_DIR, "reminders.json")


def _load_reminders() -> List[Dict[str, Any]]:
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_reminders(reminders: List[Dict[str, Any]]):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


class CalendarRemindersSkill(BaseSkill):
    """Manages scheduled reminders and calendar entries."""

    @property
    def name(self) -> str:
        return "calendar_reminders"

    @property
    def description(self) -> str:
        return "Create, list, and manage calendar events, reminders, and scheduled tasks."

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "remind me to check the deploy logs tomorrow at 9 AM",
            "what are my pending reminders?",
            "schedule a meeting with the team",
            "list my calendar events",
            "delete reminder"
        ]

    @property
    def is_state_mutating(self) -> bool:
        return True

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        start_time = time.perf_counter()
        action = params.get("action", "list").lower()
        reminders = _load_reminders()

        if action in ("create", "add", "set"):
            title = params.get("title") or params.get("text") or "Untitled Reminder"
            due = params.get("time") or params.get("due") or "Soon"
            priority = params.get("priority", "normal")

            item_id = f"rem_{int(datetime.utcnow().timestamp())}_{len(reminders) + 1}"
            new_item = {
                "id": item_id,
                "user_id": user_id,
                "title": title,
                "due": due,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            reminders.append(new_item)
            _save_reminders(reminders)

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=f"Reminder scheduled: **'{title}'** (Due: {due}, Priority: {priority.upper()}).",
                execution_time_ms=round(latency, 2),
                mutated_state=True
            )

        elif action in ("list", "get", "show"):
            user_rems = [r for r in reminders if r.get("user_id") == user_id and r.get("status") == "pending"]
            if not user_rems:
                output = "You have no pending reminders or calendar events scheduled."
            else:
                lines = [f"• **{r['title']}** — Due: `{r['due']}` (Priority: {r['priority']})" for r in user_rems]
                output = f"### Scheduled Reminders ({len(user_rems)}):\n" + "\n".join(lines)

            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=output,
                execution_time_ms=round(latency, 2),
                mutated_state=False
            )

        elif action in ("delete", "remove", "complete"):
            title_to_remove = (params.get("title") or "").lower()
            if not title_to_remove.strip():
                return SkillResult(success=False, output="Specify the reminder to remove.", error="missing_target")
            initial_count = len(reminders)
            reminders = [
                r for r in reminders
                if not (r.get("user_id") == user_id and (title_to_remove in r.get("title", "").lower() or title_to_remove == r.get("id")))
            ]
            _save_reminders(reminders)

            latency = (time.perf_counter() - start_time) * 1000.0
            if len(reminders) < initial_count:
                return SkillResult(
                    success=True,
                    output=f"Cleared reminder matching '{title_to_remove}'.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=True
                )
            else:
                return SkillResult(
                    success=True,
                    output=f"No reminder found matching '{title_to_remove}'.",
                    execution_time_ms=round(latency, 2),
                    mutated_state=False
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return SkillResult(
            success=False,
            output=f"Unknown calendar action '{action}'.",
            error="invalid_action",
            execution_time_ms=round(latency, 2)
        )
