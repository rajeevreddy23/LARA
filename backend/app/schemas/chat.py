"""Chat, memory, skills, and guardrails schemas for LARA OS (Phase 5)."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class MessageItem(BaseModel):
    """Single chat message format."""
    role: str = Field(..., description="Role of the speaker: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class UserFactItem(BaseModel):
    """Structured user knowledge item."""
    key: str = Field(..., description="Fact identifier or category (e.g. 'preferred_region', 'role')")
    value: str = Field(..., description="Fact description or value")
    confidence: float = Field(default=1.0, description="Confidence score 0.0-1.0")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ProjectItem(BaseModel):
    """Ongoing project tracking item."""
    id: str = Field(..., description="Unique project slug or ID")
    name: str = Field(..., description="Project name")
    status: str = Field(default="active", description="'active' | 'blocked' | 'completed' | 'paused'")
    summary: str = Field(..., description="Current status or goal of the project")
    pending_actions: List[str] = Field(default_factory=list, description="Pending tasks or follow-up items")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class RecalledMemoryItem(BaseModel):
    """Semantic vector memory snippet."""
    text: str
    relevance_score: float
    timestamp: str
    id: str = ""
    source: Optional[str] = None


class ToolExecutionItem(BaseModel):
    """Execution telemetry for a tool/skill invocation."""
    tool_name: str
    output: Any
    success: bool
    latency_ms: float = 0.0
    mutated_state: bool = False


class PendingActionItem(BaseModel):
    """Action awaiting explicit user confirmation."""
    ticket_id: str
    tool_name: str
    params: Dict[str, Any]
    risk_level: str
    rationale: str
    created_at: str


class AuditLogItem(BaseModel):
    """Audit entry recording system actions."""
    id: str
    timestamp: str
    user_id: str
    tool_name: str
    parameters: Dict[str, Any]
    risk_level: str
    status: str
    rationale: str
    confirmed_by: Optional[str] = None
    execution_latency_ms: float = 0.0


class ConfirmActionRequest(BaseModel):
    """Approval or rejection payload for pending actions."""
    ticket_id: str
    confirmed: bool = True
    user_id: Optional[str] = "default_user"


class ChatRequest(BaseModel):
    """Input payload for /api/chat endpoint."""
    message: str = Field(..., min_length=1, max_length=16000, description="User message prompt")
    user_name: Optional[str] = Field(default="Commander", description="User's preferred display name")
    user_id: Optional[str] = Field(default="default_user", description="User namespace ID")
    session_id: Optional[str] = Field(default="default_session", description="Session conversation ID")
    conversation_history: Optional[List[MessageItem]] = Field(
        default_factory=list,
        description="Optional list of prior turns in this session"
    )
    briefing_mode: Optional[bool] = Field(
        default=False,
        description="Whether to return a detailed briefing instead of terse casual response"
    )
    speak_response: bool = False


class ChatResponse(BaseModel):
    """Output payload from /api/chat endpoint."""
    response: str = Field(..., description="LARA's reply content")
    model: str = Field(..., description="Model identifier used to generate the reply")
    status: str = Field(default="success", description="Execution status ('success' | 'fallback' | 'pending_confirmation' | 'error')")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
    tool_execution: Optional[ToolExecutionItem] = Field(default=None, description="Tool execution output if a skill was invoked")
    pending_action: Optional[PendingActionItem] = Field(default=None, description="Action ticket if confirmation is required")
    recalled_memories: List[RecalledMemoryItem] = Field(default_factory=list, description="Semantic memories used")
    extracted_facts: List[str] = Field(default_factory=list, description="New facts learned this turn")
    audio_base64: Optional[str] = Field(default=None, description="Optional Base64 neural audio for live voice response")
    task: Optional[Dict[str, Any]] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="UTC response timestamp"
    )


class TTSRequest(BaseModel):
    """Payload for text-to-speech neural generation."""
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    voice: Optional[str] = Field(default="en-US-AriaNeural", description="Neural voice target")
    rate: Optional[str] = Field(default="+5%", description="Speech rate adjustment")
    pitch: Optional[str] = Field(default="+2Hz", description="Speech pitch adjustment")


class SkillInfo(BaseModel):
    name: str
    description: str
    trigger_examples: List[str]
    is_state_mutating: bool


class ExecuteSkillRequest(BaseModel):
    skill_name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = "default_user"


class MemoryProfileResponse(BaseModel):
    user_id: str
    user_name: str
    facts: Dict[str, str] = Field(default_factory=dict)
    projects: List[ProjectItem] = Field(default_factory=list)
    recent_session_turns: int = 0
    total_episodic_memories: int = 0
    storage_backend: str = "local_json"


class AddFactRequest(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[\w-]+$")
    value: str = Field(min_length=1, max_length=4000)
    user_id: Optional[str] = "default_user"


class AddProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=4000)
    status: Literal["active", "blocked", "completed", "paused"] = "active"
    pending_actions: Optional[List[str]] = Field(default_factory=list)
    user_id: Optional[str] = "default_user"


class UpdateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=4000)
    status: Literal["active", "blocked", "completed", "paused"] = "active"
    pending_actions: List[str] = Field(default_factory=list, max_length=50)
    user_id: str = "default_user"


class UpdateMemoryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    user_id: str = "default_user"


class StreamChunk(BaseModel):
    event: str = Field(..., description="'token', 'done', 'error'")
    text: Optional[str] = Field(default="", description="Token slice")
    model: Optional[str] = Field(default=None, description="Model identifier")


class HealthResponse(BaseModel):
    status: str = "operational"
    name: str = "LARA OS Orchestrator"
    version: str = "0.5.0"
    phase: str = "Phase 5 (Guardrails & Risk Guardian)"
    model_configured: bool = False
    active_model: str = "gemini-2.5-flash"
    active_skills: List[str] = Field(default_factory=list)
    memory_backend: str = "local_json"
    guardrails_active: bool = True
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
