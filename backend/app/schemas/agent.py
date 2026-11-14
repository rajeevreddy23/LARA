from typing import Any, Literal
from pydantic import BaseModel, Field


class PlannedStep(BaseModel):
    tool_name: str = Field(min_length=1, max_length=80)
    params: dict[str, Any] = Field(default_factory=dict)


class ToolPlan(BaseModel):
    steps: list[PlannedStep] = Field(default_factory=list, max_length=8)


class TaskStep(PlannedStep):
    status: Literal["queued", "running", "pending_approval", "completed", "failed", "cancelled"] = "queued"
    attempts: int = 0
    ticket_id: str | None = None
    result: dict[str, Any] | None = None
    pending_action: dict[str, Any] | None = None


class AgentTask(BaseModel):
    id: str
    user_id: str
    session_id: str
    prompt: str
    created_at: str
    status: Literal["running", "pending_approval", "completed", "failed", "cancelled", "interrupted"] = "running"
    steps: list[TaskStep]
