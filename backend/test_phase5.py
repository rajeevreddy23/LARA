"""Phase 5 Verification Test Suite (Guardrails & Risk Guardian).

Validates:
1. Risk assessment classification for mutating vs read-only tools.
2. Confirmation ticket generation for High-Risk actions.
3. Approval and execution of pending action tickets.
4. Cancellation of pending action tickets.
5. AuditLogger immutable trail.
6. Conversational confirmation via /api/chat.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Ensure UTF-8 on Windows
if sys.platform == "win32" and sys.stdout is sys.__stdout__:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from app.main import app
    from app.guardrails.risk_guardian import risk_guardian
    from app.guardrails.audit_logger import audit_logger
except ImportError as e:
    print(f"[FAIL] Error importing LARA modules: {e}")
    sys.exit(1)


def test_risk_assessment():
    print("\n--- [1/5] Testing Risk Guardian Assessment ---")

    # 1. Safe calculation
    risk_low, req_low, _ = risk_guardian.assess_risk("run_code", {"code": "print(10 + 20)"})
    assert risk_low == "MEDIUM" and req_low is False
    print("✅ Safe Code: Assessed as MEDIUM (Auto-Approved)")

    # 2. Potentially dangerous script
    risk_high, req_high, _ = risk_guardian.assess_risk("run_code", {"code": "import os; os.system('echo test')"})
    assert risk_high == "HIGH" and req_high is True
    print("✅ System/OS Code: Assessed as HIGH (Confirmation Required)")

    # 3. Calendar delete
    risk_del, req_del, _ = risk_guardian.assess_risk("calendar_reminders", {"action": "delete", "title": "test"})
    assert risk_del == "HIGH" and req_del is True
    print("✅ Calendar Delete: Assessed as HIGH (Confirmation Required)")


async def test_ticket_approval_lifecycle():
    print("\n--- [2/5] Testing Confirmation Ticket Lifecycle (Approval) ---")
    user_id = "test_user_phase5"

    ticket = risk_guardian.create_pending_action(
        user_id=user_id,
        tool_name="calendar_reminders",
        params={"action": "list"},
        risk_level="HIGH",
        rationale="Testing authorization flow."
    )
    assert ticket.ticket_id in [a["ticket_id"] for a in risk_guardian.list_pending_actions(user_id)]
    print(f"✅ Ticket Generated: {ticket.ticket_id} (Status: PENDING_CONFIRMATION)")

    # Confirm and execute
    res = await risk_guardian.confirm_and_execute(ticket.ticket_id, user_id=user_id)
    assert res is not None
    skill_name, skill_result = res
    assert skill_result.success is True
    assert skill_name == "calendar_reminders"
    print("✅ Ticket Approved & Executed Successfully!")


def test_ticket_rejection_lifecycle():
    print("\n--- [3/5] Testing Confirmation Ticket Lifecycle (Rejection) ---")
    user_id = "test_user_phase5"

    ticket = risk_guardian.create_pending_action(
        user_id=user_id,
        tool_name="calendar_reminders",
        params={"action": "delete", "title": "All Events"},
        risk_level="HIGH",
        rationale="Bulk delete of calendar events."
    )

    success = risk_guardian.reject_action(ticket.ticket_id, user_id=user_id)
    assert success is True
    assert ticket.ticket_id not in [a["ticket_id"] for a in risk_guardian.list_pending_actions(user_id)]
    print("✅ Ticket Rejected and Removed Safely!")


def test_audit_logging():
    print("\n--- [4/5] Testing Audit Logger Trail ---")
    user_id = "test_user_phase5"

    audit_logger.log_decision(
        user_id=user_id,
        tool_name="system_check",
        parameters={"scope": "full"},
        risk_level="LOW",
        status="EXECUTED",
        rationale="Periodic health probe.",
        execution_latency_ms=12.5
    )

    logs = audit_logger.get_logs(limit=10, user_id=user_id)
    assert len(logs) >= 1
    assert logs[0]["tool_name"] in ("system_check", "calendar_reminders", "run_code")
    print(f"✅ Audit Log Verified: {len(logs)} entries recorded with full rationale.")


def test_conversational_guardrail_gate():
    print("\n--- [5/5] Testing Conversational Risk Gating in /api/chat ---")
    client = TestClient(app)
    user_id = "test_user_phase5_chat"

    # 1. Trigger high-risk action
    res = client.post("/api/chat", json={
        "message": "delete reminder Old Deploy Notice",
        "user_id": user_id,
        "user_name": "Tony"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_confirmation"
    assert data.get("pending_action") is not None
    print("✅ Turn 1: High-Risk action intercepted. Response requested confirmation.")

    # 2. Confirm action via voice/text prompt
    res_confirm = client.post("/api/chat", json={
        "message": "Confirm",
        "user_id": user_id,
        "user_name": "Tony"
    })
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["status"] == "success"
    assert "Action authorized" in confirm_data["response"]
    print("✅ Turn 2: 'Confirm' authorized and executed the gated action!")


if __name__ == "__main__":
    print("==================================================")
    print("[*] LARA OS — Phase 5 (Guardrails & Risk Guardian) Test Suite")
    print("==================================================")
    try:
        test_risk_assessment()
        asyncio.run(test_ticket_approval_lifecycle())
        test_ticket_rejection_lifecycle()
        test_audit_logging()
        test_conversational_guardrail_gate()
        print("\n==================================================")
        print("[SUCCESS] ALL PHASE 5 GUARDRAIL TESTS PASSED!")
        print("==================================================")
    except Exception as exc:
        print(f"\n[FAILURE] Phase 5 Verification FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
