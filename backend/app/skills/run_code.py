"""Python execution boundary; fails closed until an isolated runner is available."""

from typing import Dict, Any, List
from app.skills.base import BaseSkill, SkillResult


class RunCodeSkill(BaseSkill):
    """Preserves the tool interface while preventing unsafe host execution."""

    @property
    def name(self) -> str:
        return "run_code"

    @property
    def description(self) -> str:
        return "Python execution (unavailable until an isolated sandbox is configured)."

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "run code: print(2**16)",
            "execute this python script",
            "calculate the Fibonacci sequence up to 10",
            "run python: import math; print(math.pi)"
        ]

    @property
    def is_state_mutating(self) -> bool:
        return True

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        # A host subprocess is not a sandbox. Fail closed until isolated execution
        # with OS-enforced filesystem, network, and resource limits is installed.
        return SkillResult(
            success=False,
            output="Python execution is temporarily unavailable until the isolated sandbox is configured.",
            error="sandbox_unavailable",
        )
