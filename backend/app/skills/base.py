"""Base plugin interface for LARA skills/tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SkillResult(BaseModel):
    """Result returned by a skill execution."""
    success: bool = True
    output: Any = Field(..., description="Result payload or text output")
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    mutated_state: bool = False


class BaseSkill(ABC):
    """Standardized contract for all LARA skills."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier (e.g. 'web_search', 'run_code')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what the skill does."""
        pass

    @property
    @abstractmethod
    def trigger_examples(self) -> List[str]:
        """Example phrases that should trigger this skill."""
        pass

    @property
    def is_state_mutating(self) -> bool:
        """Whether this tool call mutates external state (requires risk guardrails)."""
        return False

    @abstractmethod
    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        """Execute the skill handler asynchronously."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Return JSON-serializable schema description for LLM tool calling."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger_examples": self.trigger_examples,
            "is_state_mutating": self.is_state_mutating,
        }
