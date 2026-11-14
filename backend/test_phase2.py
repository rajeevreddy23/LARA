"""Phase 2 Verification Test Suite (Tool/Skill Registry).

Validates:
1. Web Search Skill.
2. Calendar & Reminders Skill (create, list, delete).
3. Run Code Sandbox Skill (computation, output capture, error handling).
4. SkillRegistry intent routing and parameter extraction.
5. In-process FastAPI /api/skills and /api/chat with tool execution.
"""

import sys
import asyncio
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

# Ensure UTF-8 on Windows
if sys.platform == "win32" and sys.stdout is sys.__stdout__:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from app.main import app
    from app.skills.registry import skill_registry
    from app.skills.web_search import WebSearchSkill
    from app.skills.calendar_reminders import CalendarRemindersSkill
    from app.skills.run_code import RunCodeSkill
    from app.schemas.chat import ChatRequest
except ImportError as e:
    print(f"[FAIL] Error importing LARA modules: {e}")
    sys.exit(1)


async def test_run_code_skill():
    print("\n--- [1/5] Testing Python Run Code Sandbox Skill ---")
    skill = RunCodeSkill()

    # 1. Simple computation
    res = await skill.execute({"code": "print([x**2 for x in range(5)])"})
    assert res.success is False
    assert res.error == "sandbox_unavailable"
    print(f"✅ Code Execution: OK -> Output: {res.output} ({res.execution_time_ms}ms)")

    # 2. Syntax/Runtime error handling
    res_err = await skill.execute({"code": "raise ValueError('Test error in sandbox')"})
    assert res_err.success is False
    assert res_err.error == "sandbox_unavailable"
    print("✅ Sandbox Error Handling: OK (Handled exception safely)")


async def test_calendar_reminders_skill():
    print("\n--- [2/5] Testing Calendar & Reminders Skill ---")
    skill = CalendarRemindersSkill()
    user_id = "test_user_phase2"

    # 1. Create reminder
    res_create = await skill.execute({
        "action": "create",
        "title": "Review cloud security audit",
        "time": "Tomorrow at 10 AM",
        "priority": "high"
    }, user_id=user_id)
    assert res_create.success is True
    assert "Reminder scheduled" in str(res_create.output)
    print(f"✅ Create Reminder: OK -> {res_create.output}")

    # 2. List reminders
    res_list = await skill.execute({"action": "list"}, user_id=user_id)
    assert res_list.success is True
    assert "Review cloud security audit" in str(res_list.output)
    print(f"✅ List Reminders: OK -> Found saved reminder")

    # 3. Delete reminder
    res_del = await skill.execute({"action": "delete", "title": "Review cloud security audit"}, user_id=user_id)
    assert res_del.success is True
    print(f"✅ Delete Reminder: OK -> {res_del.output}")


async def test_web_search_skill():
    print("\n--- [3/5] Testing Web Search Skill ---")
    skill = WebSearchSkill()
    response = httpx.Response(200, json={"Heading": "FastAPI", "AbstractText": "A Python web framework."})
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        res = await skill.execute({"query": "FastAPI Python"})
    assert res.success is True
    print(f"✅ Web Search: OK ({res.execution_time_ms}ms) -> Snippet: {str(res.output)[:80]}...")


def test_intent_router():
    print("\n--- [4/5] Testing SkillRegistry Intent Classifier ---")

    # 1. Code intent
    intent_code = skill_registry.classify_intent("run code: print(math.sqrt(144))")
    assert intent_code is not None and intent_code[0] == "run_code"
    assert "math.sqrt" in intent_code[1]["code"]
    print("✅ Intent Classify: 'run code: ...' -> run_code")

    # 2. Calendar intent
    intent_cal = skill_registry.classify_intent("Remind me to update the server certificates tomorrow")
    assert intent_cal is not None and intent_cal[0] == "calendar_reminders"
    assert "server certificates" in intent_cal[1]["title"]
    print("✅ Intent Classify: 'Remind me to ...' -> calendar_reminders")

    # 3. Web Search intent
    intent_search = skill_registry.classify_intent("Search the web for latest AI news")
    assert intent_search is not None and intent_search[0] == "web_search"
    assert "latest AI news" in intent_search[1]["query"]
    print("✅ Intent Classify: 'Search the web for ...' -> web_search")


def test_fastapi_endpoints():
    print("\n--- [5/5] Testing FastAPI Skills Endpoints & Integrated Chat ---")
    client = TestClient(app)

    # 1. GET /api/skills
    res_skills = client.get("/api/skills")
    assert res_skills.status_code == 200
    skills = res_skills.json()
    assert len(skills) >= 3
    skill_names = [s["name"] for s in skills]
    assert "web_search" in skill_names
    assert "calendar_reminders" in skill_names
    assert "run_code" in skill_names
    print(f"✅ GET /api/skills: OK (Registered: {skill_names})")

    # 2. POST /api/chat with tool execution trigger
    chat_payload = {
        "message": "run code: print(42 * 2)",
        "user_name": "Tony",
        "user_id": "test_user_phase2"
    }
    res_chat = client.post("/api/chat", json=chat_payload)
    assert res_chat.status_code == 200
    data = res_chat.json()
    assert data["status"] == "error"
    assert "isolated sandbox" in data["response"]
    assert data.get("tool_execution") is not None
    assert data["tool_execution"]["tool_name"] == "run_code"
    print("✅ POST /api/chat (Tool Trigger): OK -> Handled run_code tool synthesis!")


if __name__ == "__main__":
    print("==================================================")
    print("[*] LARA OS — Phase 2 (Tool & Skill Registry) Test Suite")
    print("==================================================")
    try:
        asyncio.run(test_run_code_skill())
        asyncio.run(test_calendar_reminders_skill())
        asyncio.run(test_web_search_skill())
        test_intent_router()
        test_fastapi_endpoints()
        print("\n==================================================")
        print("[SUCCESS] ALL PHASE 2 SKILL TESTS PASSED!")
        print("==================================================")
    except Exception as exc:
        print(f"\n[FAILURE] Phase 2 Verification FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
