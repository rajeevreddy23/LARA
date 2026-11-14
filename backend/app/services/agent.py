"""Durable sequential task execution with approval pauses and bounded read retries."""
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from copy import deepcopy
from app.config import settings
from app.guardrails.risk_guardian import risk_guardian, PendingAction
from app.guardrails.audit_logger import audit_logger
from app.schemas.agent import AgentTask, TaskStep
from app.schemas.chat import ChatResponse, PendingActionItem, ToolExecutionItem
from app.skills.registry import skill_registry
from app.skills.base import SkillResult
from app.services.storage import locked, write_json

logger = logging.getLogger("lara.agent")


class AgentCoordinator:
    def __init__(self, file_path=None):
        self.file_path = file_path or os.path.join(settings.LOCAL_DATA_DIR, "agent_tasks.json")
        self.tasks = {}
        self._locks = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, encoding="utf-8") as stream:
                self.tasks = {key: AgentTask.model_validate(value) for key, value in json.load(stream).items()}
        for task in self.tasks.values():
            if task.status == "running":
                # The host may have performed a side effect before the last checkpoint.
                task.status = "interrupted"
            if task.status == "pending_approval":
                for step in task.steps:
                    data = step.pending_action
                    if step.status == "pending_approval" and data:
                        action = PendingAction(**{k: v for k, v in data.items() if k != "created_at"})
                        action.created_at = data["created_at"]
                        risk_guardian._pending_actions[action.ticket_id] = action
        if self.tasks:
            self._save()

    @locked
    def _save(self):
        write_json(self.file_path, {key: task.model_dump() for key, task in self.tasks.items()})

    def list_tasks(self, user_id, session_id=None):
        return [task.model_dump() for task in list(self.tasks.values())[::-1]
                if task.user_id == user_id and (session_id is None or task.session_id == session_id)][:50]

    def find_ticket(self, ticket_id, user_id):
        return next((task for task in self.tasks.values() if task.user_id == user_id and
                     task.status == "pending_approval" and any(step.ticket_id == ticket_id and
                     step.status == "pending_approval" for step in task.steps)), None)

    async def _checkpoint(self, task, emit):
        await asyncio.to_thread(self._save)
        if emit:
            await emit({"event": "task", "task": task.model_dump()})

    async def start(self, plan, request, emit=None):
        task = AgentTask(id=f"task_{uuid.uuid4().hex}", user_id=request.user_id or "default_user",
            session_id=request.session_id or "default_session", prompt=request.message,
            created_at=datetime.now(timezone.utc).isoformat(), steps=[TaskStep(**s.model_dump()) for s in plan.steps])
        self.tasks[task.id] = task
        return await self._run(task, emit)

    def _resolve(self, value, task, index):
        if isinstance(value, dict):
            return {key: self._resolve(item, task, index) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve(item, task, index) for item in value]
        if isinstance(value, str) and value.startswith("$step_"):
            match = re.fullmatch(r"\$step_(\d+)\.output", value)
            previous = int(match[1]) - 1 if match else -1
            if previous < 0 or previous >= index or task.steps[previous].status != "completed":
                raise ValueError("Invalid step output reference.")
            return deepcopy(task.steps[previous].result["output"])
        return value

    def _can_retry(self, step):
        return step.tool_name == "web_search" or (step.tool_name == "calendar_reminders" and
                step.params.get("action", "list") in ("list", "get", "show"))

    async def _execute(self, task, step, approved=False):
        try:
            if approved:
                result = await risk_guardian.confirm_and_execute(step.ticket_id, task.user_id)
                if result is None:
                    return SkillResult(success=False, output="Approval ticket is unavailable.", error="missing_ticket")
                return result[1]
            skill = skill_registry.get_skill(step.tool_name)
            if not skill:
                return SkillResult(success=False, output="Tool unavailable.", error="missing_tool")
            return await skill.execute(step.params, user_id=task.user_id)
        except Exception:
            logger.exception("Tool execution failed for %s", step.tool_name)
            return SkillResult(success=False, output="Tool execution failed. No further steps were run.", error="tool_exception")

    async def _run(self, task, emit=None, approved_ticket=None):
        task.status = "running"
        await self._checkpoint(task, emit)
        try:
            for index, step in enumerate(task.steps):
                if step.status == "completed":
                    continue
                step.params = self._resolve(step.params, task, index)
                risk, approval, rationale = risk_guardian.assess_risk(step.tool_name, step.params, user_id=task.user_id)
                approved = step.ticket_id is not None and step.ticket_id == approved_ticket
                if approval and not approved:
                    ticket = risk_guardian.create_pending_action(task.user_id, step.tool_name, step.params, risk, rationale)
                    step.ticket_id, step.pending_action = ticket.ticket_id, ticket.to_dict()
                    step.status, task.status = "pending_approval", "pending_approval"
                    await self._checkpoint(task, emit)
                    return self.response(task)
                attempts = 1 + (settings.TOOL_READ_RETRIES if self._can_retry(step) and not approved else 0)
                for attempt in range(attempts):
                    step.status = "running"
                    step.attempts += 1
                    await self._checkpoint(task, emit)
                    result = await self._execute(task, step, approved)
                    audit_logger.log_decision(user_id=task.user_id, tool_name=step.tool_name, parameters=step.params,
                        risk_level=risk, status="EXECUTED" if result.success else "EXECUTION_ERROR",
                        rationale=f"Task {task.id}, step {index + 1}, attempt {step.attempts}.",
                        confirmed_by=task.user_id if approved else None, execution_latency_ms=result.execution_time_ms)
                    step.result = result.model_dump()
                    if result.success or attempt + 1 == attempts or result.error not in ("search_unavailable", "timeout", "transient", "tool_exception"):
                        break
                    if emit:
                        await emit({"event": "step_retry", "task_id": task.id, "step": index + 1})
                    await asyncio.sleep(0.2)
                step.status = "completed" if result.success else "failed"
                step.pending_action = None
                if not result.success:
                    task.status = "failed"
                    await self._checkpoint(task, emit)
                    return self.response(task)
                await self._checkpoint(task, emit)
            task.status = "completed"
        except asyncio.CancelledError:
            task.status = "interrupted"
            await asyncio.to_thread(self._save)
            raise
        except Exception:
            logger.exception("Agent task failed: %s", task.id)
            task.status = "failed"
        await self._checkpoint(task, emit)
        return self.response(task)

    async def resolve_approval(self, ticket_id, user_id, confirmed, emit=None):
        task = self.find_ticket(ticket_id, user_id)
        if not task:
            return None
        lock = self._locks.setdefault(task.id, asyncio.Lock())
        async with lock:
            if not self.find_ticket(ticket_id, user_id):
                return None
            if confirmed:
                return await self._run(task, emit, approved_ticket=ticket_id)
            risk_guardian.reject_action(ticket_id, user_id)
            task.status = "cancelled"
            for step in task.steps:
                if step.status != "completed":
                    step.status = "cancelled"
                    step.pending_action = None
            await self._checkpoint(task, emit)
            return self.response(task)

    def response(self, task):
        parts = []
        last_result = None
        pending = None
        for index, step in enumerate(task.steps, 1):
            if step.result:
                parts.append(f"Task {index}: {step.tool_name}\n{step.result['output']}")
                last_result = ToolExecutionItem(tool_name=step.tool_name, output=step.result["output"],
                    success=step.result["success"], latency_ms=step.result["execution_time_ms"],
                    mutated_state=step.result["mutated_state"])
            if step.status == "pending_approval":
                pending = PendingActionItem(**{k: v for k, v in step.pending_action.items() if k != "user_id"})
                parts.append(f"Task {index} needs approval: {pending.rationale}")
        if task.status == "cancelled":
            parts.append("Directive aborted. Remaining tasks were cancelled.")
        if task.status == "failed":
            parts.append("The task stopped after an error. Remaining steps have not run.")
        return ChatResponse(response="\n\n".join(parts), model="lara-agent",
            status="pending_confirmation" if pending else "error" if task.status in ("failed", "interrupted") else "success",
            pending_action=pending, tool_execution=last_result, task=task.model_dump())


agent_coordinator = AgentCoordinator()
