"""Autonomous Executive Briefing Generator for LARA OS."""

import logging
from typing import Dict, Any, List
from datetime import datetime
from app.memory.structured import structured_memory
from app.memory.vector import vector_memory
from app.skills.calendar_reminders import _load_reminders
from app.skills.registry import skill_registry

logger = logging.getLogger("lara.proactivity.briefing")


class BriefingGenerator:
    """Compiles structured memory, calendar reminders, and system telemetry into an executive daily briefing."""

    def generate_briefing(self, user_id: str = "default_user", user_name: str = "Commander") -> Dict[str, Any]:
        """Generate a complete executive briefing document."""
        facts = structured_memory.get_user_facts(user_id)
        projects = structured_memory.get_projects(user_id)
        reminders = [r for r in _load_reminders() if r.get("user_id") == user_id and r.get("status") == "pending"]
        skills = skill_registry.list_skills()
        total_memories = vector_memory.count_memories(user_id)

        # 1. Projects Breakdown
        project_sections = []
        for p in projects:
            actions = "\n".join([f"    - [ ] {a}" for a in p.pending_actions]) if p.pending_actions else "    - (No pending action items)"
            project_sections.append(f"  • **{p.name}** [{p.status.upper()}]\n    *{p.summary}*\n{actions}")
        projects_text = "\n".join(project_sections) if project_sections else "  • No active projects registered."

        # 2. Reminders Breakdown
        if reminders:
            reminders_text = "\n".join([f"  • **{r['title']}** (Due: `{r['due']}`, Priority: {r['priority'].upper()})" for r in reminders])
        else:
            reminders_text = "  • All scheduled items cleared. No pending reminders."

        # 3. System Telemetry
        telemetry_text = (
            f"  • Memory Storage: `{structured_memory.backend_type.upper()}`\n"
            f"  • Vector Semantic Index: `{total_memories} records`\n"
            f"  • Active Tool Plugins: `{len(skills)} tools` ({', '.join([s['name'] for s in skills])})"
        )

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        briefing_markdown = (
            f"## 📋 Executive System Briefing for {user_name}\n"
            f"*Timestamp: {now_str}*\n\n"
            f"### 🎯 Tracked Projects & Action Items\n"
            f"{projects_text}\n\n"
            f"### ⏰ Scheduled Calendar & Reminders\n"
            f"{reminders_text}\n\n"
            f"### ⚙️ Intelligence & Tool Matrix\n"
            f"{telemetry_text}\n\n"
            f"---\n"
            f"*Status: All subsystems operational. Ready for subsequent directives, {user_name}.*"
        )

        return {
            "title": f"Daily Briefing — {now_str}",
            "briefing": briefing_markdown,
            "project_count": len(projects),
            "pending_reminder_count": len(reminders),
            "timestamp": now_str,
        }


# Singleton
briefing_generator = BriefingGenerator()
