import asyncio
import json
import os
import subprocess
import sys
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.schemas.chat import ChatRequest, ProjectItem
from app.schemas.agent import ToolPlan, PlannedStep
from app.skills.base import SkillResult
from app.skills.registry import skill_registry
from app.memory.structured import structured_memory
from app.memory.vector import VectorMemoryManager, vector_memory, LOCAL_VERSION
from app.memory.service import memory_service
from app.memory.extractor import memory_extractor
from app.services.agent import AgentCoordinator, agent_coordinator
from app.services.llm_service import LLMService, get_llm_service
from app.services.planner import Planner


class FakeProvider:
    configured = True
    model_name = "fake-provider"

    def __init__(self, steps=None):
        self.steps = steps or []
        self.calls = []

    async def complete(self, system, messages, schema=None):
        self.calls.append((system, messages, schema))
        return json.dumps({"steps": self.steps}) if schema else "A real provider response."

    async def stream(self, system, messages):
        self.calls.append((system, messages, None))
        yield "Hello "
        await asyncio.sleep(0)
        yield "there."


def test_fallback_vectors_are_stable_across_processes():
    script = "import json; from app.memory.vector import vector_memory; print(json.dumps(vector_memory._local_embedding('Production deployments after evening review')))"
    outputs = []
    for seed in ("11", "99"):
        result = subprocess.run([sys.executable, "-c", script], env={**os.environ, "PYTHONHASHSEED": seed},
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1]


def test_legacy_vectors_migrate_and_remain_searchable():
    memory_id = vector_memory.add_memory("legacy-vector", "Coffee preference is oat milk espresso")
    memory = next(m for m in vector_memory.memories if m["id"] == memory_id)
    memory.pop("embedding_version")
    memory["embedding"] = [0.0] * 256
    results = vector_memory.search_memories("legacy-vector", "coffee espresso")
    assert results[0].id == memory_id
    reloaded = VectorMemoryManager()
    assert next(m for m in reloaded.memories if m["id"] == memory_id)["embedding_version"] == LOCAL_VERSION


def test_memory_context_excludes_unrelated_facts_and_other_users():
    memory_service.save_fact("context-user", "coffee", "oat milk espresso")
    memory_service.save_fact("context-user", "database", "Postgres production cluster")
    memory_service.save_fact("someone-else", "coffee", "secret coffee recipe")
    context, _ = memory_service.relevant_context("context-user", "What coffee do I prefer?")
    assert "oat milk" in context
    assert "Postgres" not in context and "secret" not in context
    assert len(context) <= settings.MEMORY_CONTEXT_CHARS


def test_updated_fact_replaces_index_and_clears_stale_history():
    memory_service.save_fact("fact-edit", "coffee", "espresso")
    structured_memory.append_session_message("fact-edit", "session", "user", "espresso")
    memory_service.save_fact("fact-edit", "coffee", "matcha")
    records = vector_memory.list_memories("fact-edit")
    assert len(records) == 1 and "matcha" in records[0]["text"]
    assert "espresso" not in records[0]["text"]
    assert structured_memory.get_session_history("fact-edit", "session") == []


def test_fact_delete_removes_linked_and_legacy_memories():
    memory_service.save_fact("fact-delete", "coffee", "espresso")
    vector_memory.add_memory("fact-delete", "I always order espresso after lunch.")
    assert memory_service.delete_fact("fact-delete", "coffee")
    assert vector_memory.list_memories("fact-delete") == []
    assert not memory_service.delete_fact("another-user", "coffee")


def test_project_edit_keeps_id_and_deletion_removes_index():
    project = ProjectItem(id="lara-project", name="LARA", summary="Memory upgrade")
    memory_service.save_project("project-edit", project)
    project.name, project.summary = "LARA upgraded", "Task planner"
    memory_service.save_project("project-edit", project)
    records = vector_memory.list_memories("project-edit")
    assert len(records) == 1 and records[0]["source"] == "project:lara-project"
    assert memory_service.delete_project("project-edit", project.id)
    assert not vector_memory.list_memories("project-edit")


def test_questions_are_not_saved_as_facts_and_plain_preference_works():
    assert not memory_extractor.extract_and_persist("extractor-test", "Remember when we worked on coffee?")
    assert not structured_memory.get_user_facts("extractor-test")
    assert memory_extractor.extract_and_persist("extractor-test", "I prefer concise replies.")
    assert "concise replies" in structured_memory.get_user_facts("extractor-test")["general_preference"]


def test_memory_crud_api_and_user_isolation():
    client = TestClient(app)
    body = {"key": "timezone", "value": "Asia/Kolkata", "user_id": "crud-test"}
    assert client.post("/api/memory/fact", json=body).status_code == 200
    body["value"] = "UTC"
    assert client.put("/api/memory/fact/timezone", json=body).status_code == 200
    assert client.get("/api/memory/profile?user_id=crud-test").json()["facts"]["timezone"] == "UTC"
    assert client.delete("/api/memory/fact/timezone?user_id=other").status_code == 404
    assert client.delete("/api/memory/fact/timezone?user_id=crud-test").status_code == 200
    assert client.get("/api/memory/episodes?user_id=crud-test").json() == []
    assert client.post("/api/memory/fact", json={"key": "", "value": ""}).status_code == 422


def test_episode_edit_and_linked_record_protection():
    memory_id = vector_memory.add_memory("episode-edit", "Old coffee note")
    assert memory_service.edit_episode("episode-edit", memory_id, "Updated tea note")
    assert vector_memory.list_memories("episode-edit")[0]["text"] == "Updated tea note"
    memory_service.save_fact("episode-edit", "coffee", "espresso")
    linked = next(m for m in vector_memory.list_memories("episode-edit") if m.get("source"))
    with pytest.raises(ValueError):
        memory_service.edit_episode("episode-edit", linked["id"], "wrong path")
    assert memory_service.delete_episode("episode-edit", linked["id"])
    assert "coffee" not in structured_memory.get_user_facts("episode-edit")


async def test_provider_receives_relevant_memory_and_session_history():
    provider = FakeProvider()
    service = LLMService(provider)
    memory_service.save_fact("provider-context", "coffee", "espresso")
    memory_service.save_fact("provider-context", "database", "secret-database-host")
    structured_memory.append_session_message("provider-context", "chat", "user", "Please remember this conversation")
    response = await service.generate_chat(ChatRequest(message="What coffee do I prefer?", user_id="provider-context", session_id="chat"))
    assert response.model == "fake-provider"
    system, messages, _ = provider.calls[-1]
    assert "espresso" in system and "secret-database-host" not in system
    assert messages[0]["content"] == "Please remember this conversation"


async def test_stream_yields_provider_chunks_before_done():
    events = [event async for event in LLMService(FakeProvider()).stream_events(ChatRequest(message="hello", user_id="stream-test"))]
    assert [e["text"] for e in events if e["event"] == "token"] == ["Hello ", "there."]
    assert events[-1]["event"] == "done"
    assert events[-1]["response"]["response"] == "Hello there."


async def test_model_plan_unknown_tool_is_rejected_before_execution():
    provider = FakeProvider([{"tool_name": "invented_tool", "params": {}}])
    with patch.object(skill_registry, "classify_multi_intent", return_value=[]):
        response = await LLMService(provider).generate_chat(ChatRequest(message="do a thing", user_id="bad-plan"))
    assert response.status == "error" and "No tools were run" in response.response


async def test_planner_rejects_forward_references():
    provider = FakeProvider([{"tool_name": "web_search", "params": {"query": "$step_2.output"}}])
    with patch.object(skill_registry, "classify_multi_intent", return_value=[]), pytest.raises(ValueError):
        await Planner(provider).plan("do a thing")


async def test_read_failure_retries_but_mutating_failure_does_not(tmp_path):
    coordinator = AgentCoordinator(str(tmp_path / "tasks.json"))
    search = skill_registry.get_skill("web_search")
    with patch.object(search, "execute", new_callable=AsyncMock, side_effect=[
        SkillResult(success=False, output="unavailable", error="search_unavailable"), SkillResult(success=True, output="found")
    ]) as execute:
        response = await coordinator.start(ToolPlan(steps=[PlannedStep(tool_name="web_search", params={"query": "coffee"})]), ChatRequest(message="search", user_id="retry-test"))
    assert response.status == "success" and execute.await_count == 2
    calendar = skill_registry.get_skill("calendar_reminders")
    with patch.object(calendar, "execute", new_callable=AsyncMock, return_value=SkillResult(success=False, output="unavailable", error="timeout")) as execute:
        response = await coordinator.start(ToolPlan(steps=[PlannedStep(tool_name="calendar_reminders", params={"action": "create", "title": "test"})]), ChatRequest(message="remind", user_id="retry-test"))
    assert response.status == "error" and execute.await_count == 1


async def test_task_pauses_resumes_and_never_replays_completed_steps(tmp_path):
    coordinator = AgentCoordinator(str(tmp_path / "tasks.json"))
    calendar, system = skill_registry.get_skill("calendar_reminders"), skill_registry.get_skill("system_control")
    plan = ToolPlan(steps=[PlannedStep(tool_name="calendar_reminders", params={"action": "list"}),
        PlannedStep(tool_name="system_control", params={"target": "notepad"}),
        PlannedStep(tool_name="calendar_reminders", params={"action": "list"})])
    with patch.object(calendar, "execute", new_callable=AsyncMock, return_value=SkillResult(output="listed")) as calendar_exec, patch.object(
        system, "execute", new_callable=AsyncMock, return_value=SkillResult(output="opened")) as system_exec:
        response = await coordinator.start(plan, ChatRequest(message="three tasks", user_id="resume-test"))
        ticket = response.pending_action.ticket_id
        assert system_exec.await_count == 0 and calendar_exec.await_count == 1
        assert await coordinator.resolve_approval(ticket, "wrong-user", True) is None
        response = await coordinator.resolve_approval(ticket, "resume-test", True)
        assert response.status == "success"
        assert calendar_exec.await_count == 2 and system_exec.await_count == 1
        assert await coordinator.resolve_approval(ticket, "resume-test", True) is None


async def test_rejection_cancels_remaining_steps(tmp_path):
    coordinator = AgentCoordinator(str(tmp_path / "tasks.json"))
    plan = ToolPlan(steps=[PlannedStep(tool_name="system_control", params={"target": "notepad"}),
                          PlannedStep(tool_name="calendar_reminders", params={"action": "list"})])
    calendar = skill_registry.get_skill("calendar_reminders")
    with patch.object(calendar, "execute", new_callable=AsyncMock) as execute:
        response = await coordinator.start(plan, ChatRequest(message="two tasks", user_id="deny-test"))
        denied = await coordinator.resolve_approval(response.pending_action.ticket_id, "deny-test", False)
    assert denied.task["status"] == "cancelled"
    execute.assert_not_awaited()


async def test_pending_task_survives_restart_without_replaying(tmp_path):
    path = str(tmp_path / "tasks.json")
    coordinator = AgentCoordinator(path)
    response = await coordinator.start(ToolPlan(steps=[PlannedStep(tool_name="system_control", params={"target": "notepad"})]),
                                       ChatRequest(message="open", user_id="restart-test"))
    restored = AgentCoordinator(path)
    assert restored.find_ticket(response.pending_action.ticket_id, "restart-test") is not None
    system = skill_registry.get_skill("system_control")
    with patch.object(system, "execute", new_callable=AsyncMock, return_value=SkillResult(output="opened")) as execute:
        resumed = await restored.resolve_approval(response.pending_action.ticket_id, "restart-test", True)
    assert resumed.status == "success" and execute.await_count == 1


async def test_step_output_reference_is_resolved(tmp_path):
    coordinator = AgentCoordinator(str(tmp_path / "tasks.json"))
    search = skill_registry.get_skill("web_search")
    with patch.object(search, "execute", new_callable=AsyncMock, return_value=SkillResult(output="first result")) as execute:
        response = await coordinator.start(ToolPlan(steps=[PlannedStep(tool_name="web_search", params={"query": "first"}),
            PlannedStep(tool_name="web_search", params={"query": "$step_1.output"})]), ChatRequest(message="dependent steps", user_id="refs-test"))
    assert response.status == "success"
    assert execute.await_args_list[1].args[0]["query"] == "first result"


def test_sse_endpoint_delivers_final_metadata():
    service = LLMService(FakeProvider())
    app.dependency_overrides[get_llm_service] = lambda: service
    try:
        response = TestClient(app).post("/api/chat/stream", json={"message": "hello", "user_id": "sse-test"})
        assert response.status_code == 200 and "text/event-stream" in response.headers["content-type"]
        events = [json.loads(frame[6:]) for frame in response.text.strip().split("\n\n")]
        assert events[-1]["event"] == "done"
        assert events[-1]["response"]["model"] == "fake-provider"
    finally:
        app.dependency_overrides.clear()
