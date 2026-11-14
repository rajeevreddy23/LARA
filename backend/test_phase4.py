"""Phase 4 Verification Test Suite (Proactivity Engine).

Validates:
1. Autonomous Daily & System Briefing Generation.
2. ProactivityScheduler follow-up formulation for tracked projects.
3. Proactive reminder alerts.
4. FastAPI proactivity REST endpoints.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Ensure UTF-8 on Windows
if sys.platform == "win32" and sys.stdout is sys.__stdout__:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from app.main import app
    from app.proactivity.briefing import briefing_generator
    from app.proactivity.scheduler import proactivity_scheduler
    from app.memory.structured import structured_memory
    from app.schemas.chat import ProjectItem
    from app.skills.calendar_reminders import CalendarRemindersSkill
except ImportError as e:
    print(f"[FAIL] Error importing LARA modules: {e}")
    sys.exit(1)


def test_briefing_generation():
    print("\n--- [1/4] Testing Autonomous Executive Briefing Generator ---")
    user_id = "test_user_phase4"

    # Setup dummy project and facts
    structured_memory.set_user_fact(user_id, "primary_focus", "Autonomous AI OS")
    proj = ProjectItem(
        id="project-aura",
        name="Project AURA",
        status="active",
        summary="Next-gen context engine",
        pending_actions=["Run benchmark tests", "Optimize memory cache"]
    )
    structured_memory.upsert_project(user_id, proj)

    briefing = briefing_generator.generate_briefing(user_id=user_id, user_name="Commander")
    assert "Executive System Briefing" in briefing["briefing"]
    assert "Project AURA" in briefing["briefing"]
    assert "Run benchmark tests" in briefing["briefing"]
    print("✅ Executive Briefing Generated Successfully!")
    print(f"   Briefing Title: {briefing['title']}")
    print(f"   Tracked Projects Included: {briefing['project_count']}")


async def test_followup_detection():
    print("\n--- [2/4] Testing Proactive Project Follow-Up Engine ---")
    user_id = "test_user_phase4"

    followups = proactivity_scheduler.check_followups(user_id=user_id, user_name="Commander")
    assert len(followups) >= 1
    proj_followup = next((f for f in followups if f.get("type") == "project_followup"), None)
    assert proj_followup is not None
    assert "Project AURA" in proj_followup["title"]
    assert "Run benchmark tests" in proj_followup["message"]
    print(f"✅ Proactive Project Follow-up: \"{proj_followup['message']}\"")


async def test_reminder_alert_dispatch():
    print("\n--- [3/4] Testing Proactive Reminder Alert Detection ---")
    user_id = "test_user_phase4"
    skill = CalendarRemindersSkill()

    # Create urgent reminder
    await skill.execute({
        "action": "create",
        "title": "Production Deployment Window",
        "time": "18:00 UTC",
        "priority": "critical"
    }, user_id=user_id)

    followups = proactivity_scheduler.check_followups(user_id=user_id)
    rem_alert = next((f for f in followups if f.get("type") == "reminder_alert" and "Production Deployment Window" in f.get("title")), None)
    assert rem_alert is not None
    print(f"✅ Proactive Reminder Alert: \"{rem_alert['message']}\" (Priority: {rem_alert.get('priority')})")


def test_fastapi_proactivity_endpoints():
    print("\n--- [4/4] Testing FastAPI Proactivity REST Endpoints ---")
    client = TestClient(app)
    user_id = "test_user_phase4"

    # 1. GET /api/proactivity/briefing
    res_brief = client.get(f"/api/proactivity/briefing?user_id={user_id}")
    assert res_brief.status_code == 200
    brief_data = res_brief.json()
    assert "briefing" in brief_data
    print("✅ GET /api/proactivity/briefing: OK")

    # 2. GET /api/proactivity/followups
    res_fol = client.get(f"/api/proactivity/followups?user_id={user_id}")
    assert res_fol.status_code == 200
    fol_data = res_fol.json()
    assert len(fol_data) >= 1
    print(f"✅ GET /api/proactivity/followups: OK ({len(fol_data)} active follow-ups)")


if __name__ == "__main__":
    print("==================================================")
    print("[*] LARA OS — Phase 4 (Proactivity Engine) Test Suite")
    print("==================================================")
    try:
        test_briefing_generation()
        asyncio.run(test_followup_detection())
        asyncio.run(test_reminder_alert_dispatch())
        test_fastapi_proactivity_endpoints()
        print("\n==================================================")
        print("[SUCCESS] ALL PHASE 4 PROACTIVITY TESTS PASSED!")
        print("==================================================")
    except Exception as exc:
        print(f"\n[FAILURE] Phase 4 Verification FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
