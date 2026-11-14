import asyncio
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import pytest
from app.main import app
from app.config import settings
from app.guardrails.risk_guardian import RiskGuardian, risk_guardian
from app.guardrails.audit_logger import audit_logger
from app.schemas.chat import ChatRequest
from app.services.llm_service import LLMService
from app.skills.base import SkillResult
from app.skills.registry import skill_registry
from app.skills.run_code import RunCodeSkill
from app.skills.calendar_reminders import CalendarRemindersSkill
from app.skills.web_search import WebSearchSkill


def test_ticket_owner_and_single_use():
    guardian = RiskGuardian()
    ticket = guardian.create_pending_action("owner", "calendar_reminders", {"action": "list"}, "HIGH", "test")
    assert asyncio.run(guardian.confirm_and_execute(ticket.ticket_id, "other")) is None
    assert not guardian.reject_action(ticket.ticket_id, "other")
    assert len(guardian.list_pending_actions("owner")) == 1
    assert asyncio.run(guardian.confirm_and_execute(ticket.ticket_id, "owner")) is not None
    assert asyncio.run(guardian.confirm_and_execute(ticket.ticket_id, "owner")) is None


def test_direct_tool_cannot_bypass_approval():
    skill = skill_registry.get_skill("system_control")
    with patch.object(skill, "execute", new_callable=AsyncMock) as execute:
        result = TestClient(app).post("/api/skills/execute", json={
            "skill_name": "system_control", "params": {"target": "notepad"}, "user_id": "direct-test",
        })
    assert result.status_code == 200
    assert result.json()["status"] == "pending_confirmation"
    execute.assert_not_awaited()


def test_chained_tasks_stop_before_risky_step():
    service = LLMService()
    system = skill_registry.get_skill("system_control")
    calendar = skill_registry.get_skill("calendar_reminders")
    with patch.object(skill_registry, "classify_multi_intent", return_value=[
        ("calendar_reminders", {"action": "list"}),
        ("system_control", {"target": "notepad"}),
        ("calendar_reminders", {"action": "list"}),
    ]), patch.object(system, "execute", new_callable=AsyncMock) as system_execute, patch.object(
        calendar, "execute", new_callable=AsyncMock,
        return_value=SkillResult(success=True, output="No reminders"),
    ) as calendar_execute:
        result = asyncio.run(service.generate_chat(ChatRequest(message="compound task", user_id="chain-test")))
    assert result.status == "pending_confirmation"
    assert result.pending_action.tool_name == "system_control"
    system_execute.assert_not_awaited()
    assert calendar_execute.await_count == 1
    assert audit_logger.get_logs(user_id="chain-test")


def test_external_messaging_requires_approval():
    risk, approval, _ = risk_guardian.assess_risk("whatsapp_hub", {"action": "send"})
    assert risk == "HIGH" and approval


def test_unclassified_tools_require_approval():
    assert risk_guardian.assess_risk("future_tool", {})[1]


def test_code_fails_closed_without_spawning_host_process():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as spawn:
        result = asyncio.run(RunCodeSkill().execute({"code": "print(42)"}))
    assert not result.success and result.error == "sandbox_unavailable"
    spawn.assert_not_awaited()


def test_empty_reminder_delete_is_rejected():
    result = asyncio.run(CalendarRemindersSkill().execute({"action": "delete"}))
    assert not result.success and result.error == "missing_target"


def test_search_failure_is_not_reported_as_success():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("offline")):
        result = asyncio.run(WebSearchSkill().execute({"query": "fastapi"}))
    assert not result.success and result.error == "search_unavailable"


def test_safe_direct_execution_is_audited():
    result = TestClient(app).post("/api/skills/execute", json={
        "skill_name": "calendar_reminders", "params": {"action": "list"}, "user_id": "safe-test",
    })
    assert result.status_code == 200 and result.json()["success"]
    assert audit_logger.get_logs(user_id="safe-test")[0]["status"] == "AUTO_AUTHORIZED"


def test_only_configured_origins_are_allowed():
    client = TestClient(app)
    for origin, allowed in [(settings.CORS_ORIGINS[0], True), ("https://untrusted.example", False)]:
        result = client.options("/api/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert (result.status_code == 200) == allowed


def test_backend_lifespan_and_health():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/").status_code == 200
        assert client.post("/api/chat", json={"message": ""}).status_code == 422


def test_untrusted_websocket_origin_is_rejected():
    with pytest.raises(WebSocketDisconnect) as exc:
        with TestClient(app).websocket_connect("/ws/chat", headers={"Origin": "https://untrusted.example"}):
            pass
    assert exc.value.code == 1008
