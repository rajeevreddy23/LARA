"""Phase 1 Verification Test Suite (Identity & Memory).

Validates:
1. Structured long-term memory (user facts and project tracking).
2. Short-term session memory turn buffers.
3. Vector memory semantic similarity search ("remember when I...").
4. Autonomous memory extractor parsing facts and projects from prompts.
5. In-process FastAPI endpoints for /api/memory/profile and /api/chat.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Ensure UTF-8 on Windows
if sys.platform == "win32" and sys.stdout is sys.__stdout__:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from app.main import app
    from app.memory.structured import structured_memory
    from app.memory.vector import vector_memory
    from app.memory.extractor import memory_extractor
    from app.schemas.chat import ChatRequest, ProjectItem
    from app.services.llm_service import get_llm_service
except ImportError as e:
    print(f"[FAIL] Error importing LARA modules: {e}")
    sys.exit(1)


def test_structured_memory():
    print("\n--- [1/5] Testing Structured Long-Term Memory (Facts & Projects) ---")
    user_id = "test_user_phase1"

    # Set user facts
    structured_memory.set_user_fact(user_id, "preferred_deploy_region", "us-central1")
    structured_memory.set_user_fact(user_id, "primary_language", "Python")

    facts = structured_memory.get_user_facts(user_id)
    assert facts.get("preferred_deploy_region") == "us-central1"
    assert facts.get("primary_language") == "Python"
    print(f"✅ User Facts Stored & Retrieved: {facts}")

    # Track ongoing project
    proj = ProjectItem(
        id="bekki-voice-agent",
        name="BEKKI Voice Agent",
        status="active",
        summary="Automated Telugu/English conversational customer agent.",
        pending_actions=["Check telephony logs", "Calibrate latency"]
    )
    structured_memory.upsert_project(user_id, proj)
    projects = structured_memory.get_projects(user_id)
    assert len(projects) >= 1
    assert projects[0].id == "bekki-voice-agent"
    print(f"✅ Project Stored & Retrieved: {projects[0].name} (Status: {projects[0].status})")


def test_session_memory():
    print("\n--- [2/5] Testing Short-Term Session Conversation Buffer ---")
    user_id = "test_user_phase1"
    session_id = "session_alpha"

    # Clean session
    structured_memory.clear_session_history(user_id, session_id)
    history_init = structured_memory.get_session_history(user_id, session_id)
    assert len(history_init) == 0

    # Append turns
    structured_memory.append_session_message(user_id, session_id, "user", "Initiate project overview.")
    structured_memory.append_session_message(user_id, session_id, "assistant", "BEKKI systems online.")

    history = structured_memory.get_session_history(user_id, session_id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
    print(f"✅ Session History Buffer Verified: {len(history)} turns recorded correctly.")


def test_vector_memory_recall():
    print("\n--- [3/5] Testing Vector Memory & Semantic Recall ---")
    user_id = "test_user_phase1"

    # Add specific episodic memories
    vector_memory.add_memory(user_id, "User instructed that production deploys must occur only after 18:00 UTC.")
    vector_memory.add_memory(user_id, "Favorite coffee order is double espresso with oat milk.")

    # Search for deployment constraints
    results_deploy = vector_memory.search_memories(user_id, "When can we deploy to production?")
    assert len(results_deploy) > 0
    top_result = results_deploy[0]
    print(f"✅ Semantic Search for 'deploy to production' -> Matched: \"{top_result.text}\" (Score: {top_result.relevance_score})")

    # Search for food / beverage
    results_coffee = vector_memory.search_memories(user_id, "What coffee do I like?")
    assert len(results_coffee) > 0
    print(f"✅ Semantic Search for 'coffee' -> Matched: \"{results_coffee[0].text}\" (Score: {results_coffee[0].relevance_score})")


def test_autonomous_extractor():
    print("\n--- [4/5] Testing Autonomous Memory Extractor ---")
    user_id = "test_user_phase1"

    # Test preference extraction
    extracted = memory_extractor.extract_and_persist(user_id, "Remember that my secondary cluster is located in eu-west1.")
    assert len(extracted) > 0
    print(f"✅ Extracted Fact: {extracted[0]}")

    facts = structured_memory.get_user_facts(user_id)
    assert any("eu-west1" in str(v) for v in facts.values())
    print("✅ Verified autonomous fact saved into structured storage.")


def test_fastapi_endpoints():
    print("\n--- [5/5] Testing FastAPI Memory REST Endpoints ---")
    client = TestClient(app)
    user_id = "test_user_phase1"

    # 1. Profile check
    res = client.get(f"/api/memory/profile?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "facts" in data
    assert "projects" in data
    print(f"✅ GET /api/memory/profile: OK ({len(data['facts'])} facts, {len(data['projects'])} projects)")

    # 2. Chat with memory context
    chat_payload = {
        "message": "What is my preferred deploy region?",
        "user_id": user_id,
        "user_name": "Tony",
        "briefing_mode": False
    }
    res_chat = client.post("/api/chat", json=chat_payload)
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    print(f"✅ POST /api/chat with Memory Context: OK")
    print(f"   LARA Response: \"{chat_data.get('response')}\"")


if __name__ == "__main__":
    print("==================================================")
    print("[*] LARA OS — Phase 1 (Identity & Memory) Test Suite")
    print("==================================================")
    try:
        test_structured_memory()
        test_session_memory()
        test_vector_memory_recall()
        test_autonomous_extractor()
        test_fastapi_endpoints()
        print("\n==================================================")
        print("[SUCCESS] ALL PHASE 1 MEMORY TESTS PASSED!")
        print("==================================================")
    except Exception as exc:
        print(f"\n[FAILURE] Phase 1 Verification FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
