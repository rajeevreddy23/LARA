"""Background Proactivity Scheduler and WebSocket Event Broadcaster."""

import asyncio
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
from fastapi import WebSocket
from app.memory.structured import structured_memory
from app.skills.calendar_reminders import _load_reminders
from app.proactivity.briefing import briefing_generator

logger = logging.getLogger("lara.proactivity.scheduler")


class ProactivityScheduler:
    """Monitors reminders, project tasks, and pushes proactive notifications to connected clients."""

    def __init__(self, check_interval_seconds: int = 45):
        self.check_interval = check_interval_seconds
        self.active_websockets: Set[WebSocket] = set()
        self._task: asyncio.Task | None = None
        self._running = False
        self.last_checked: datetime | None = None
        self.dispatched_history: List[Dict[str, Any]] = []

    def register_websocket(self, websocket: WebSocket):
        """Register a connected WebSocket client."""
        self.active_websockets.add(websocket)
        logger.info("Registered WebSocket client in ProactivityScheduler. (Total active: %d)", len(self.active_websockets))

    def unregister_websocket(self, websocket: WebSocket):
        """Unregister a disconnected WebSocket client."""
        self.active_websockets.discard(websocket)
        logger.info("Unregistered WebSocket client in ProactivityScheduler. (Remaining: %d)", len(self.active_websockets))

    async def broadcast_event(self, event_payload: Dict[str, Any]):
        """Broadcast JSON payload to all connected clients."""
        if not self.active_websockets:
            logger.debug("No active WebSocket clients to broadcast event to.")
            return

        dead_sockets = set()
        for ws in list(self.active_websockets):
            try:
                await ws.send_json(event_payload)
            except Exception as e:
                logger.warning("Error broadcasting to WebSocket (%s), removing.", e)
                dead_sockets.add(ws)

        for dead in dead_sockets:
            self.active_websockets.discard(dead)

    def check_followups(self, user_id: str = "default_user", user_name: str = "Commander") -> List[Dict[str, Any]]:
        """Evaluate tracked projects and reminders to produce proactive follow-ups."""
        followups: List[Dict[str, Any]] = []
        projects = structured_memory.get_projects(user_id)
        reminders = [r for r in _load_reminders() if r.get("user_id") == user_id and r.get("status") == "pending"]

        # 1. Project action item follow-ups
        for p in projects:
            if p.status == "active" and p.pending_actions:
                first_action = p.pending_actions[0]
                followups.append({
                    "id": f"followup_proj_{p.id}_{int(datetime.utcnow().timestamp())}",
                    "type": "project_followup",
                    "title": f"Follow-up: {p.name}",
                    "message": f"Commander, following up on {p.name}: Have you completed \"{first_action}\"?",
                    "project_id": p.id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

        # 2. Reminder alerts
        for r in reminders:
            followups.append({
                "id": f"alert_rem_{r['id']}",
                "type": "reminder_alert",
                "title": f"Scheduled Reminder: {r['title']}",
                "message": f"Reminder active: \"{r['title']}\" (Due: {r['due']})",
                "priority": r.get("priority", "normal"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        return followups

    async def execute_proactive_check(self, user_id: str = "default_user"):
        """Run a proactive evaluation and broadcast if any alerts exist."""
        self.last_checked = datetime.utcnow()
        followups = self.check_followups(user_id)
        if followups:
            # Pick latest item to broadcast
            latest = followups[0]
            event = {
                "event": "proactive_notification",
                "notification": latest
            }
            self.dispatched_history.append(latest)
            logger.info("Broadcasting proactive event: %s", latest["title"])
            await self.broadcast_event(event)

    async def _scheduler_loop(self):
        """Periodic background check worker loop."""
        logger.info("Proactivity scheduler background loop started.")
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.execute_proactive_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in proactivity scheduler loop: %s", e)
                await asyncio.sleep(5)

    def start(self):
        """Start the background daemon task."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._scheduler_loop())
            logger.info("ProactivityScheduler daemon initialized.")

    def stop(self):
        """Stop the background daemon task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("ProactivityScheduler daemon stopped.")


# Singleton
proactivity_scheduler = ProactivityScheduler()
