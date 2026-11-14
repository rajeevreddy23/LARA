"""Phase 0 Verification Test Script.

Validates:
1. LLMService direct execution & fallback mechanism.
2. FastAPI app routes & schema validation using TestClient.
3. Live server connectivity (if server is currently running on port 8000).
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Import backend application
try:
    from app.main import app
    from app.schemas.chat import ChatRequest
    from app.services.llm_service import get_llm_service
except ImportError as e:
    print(f"❌ Error importing LARA backend modules: {e}")
    sys.exit(1)


def test_in_process_endpoints():
    """Test FastAPI endpoints in-process via Starlette TestClient."""
    print("\n--- [1/3] Running In-Process FastAPI Endpoint Tests ---")
    client = TestClient(app)

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed with {res.status_code}"
    health_data = res.json()
    print(f"✅ /api/health: OK (Status: {health_data.get('status')}, Phase: {health_data.get('phase')})")

    # 2. Chat endpoint (casual mode)
    payload = {
        "message": "System status check.",
        "user_name": "Commander",
        "briefing_mode": False
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200, f"Chat POST failed with {res.status_code}"
    chat_data = res.json()
    print(f"✅ /api/chat (Casual): OK (Model: {chat_data.get('model')}, Latency: {chat_data.get('latency_ms')}ms)")
    print(f"   Response snippet: \"{chat_data.get('response')[:80]}...\"")

    # 3. Chat endpoint (briefing mode)
    payload_brief = {
        "message": "Summarize today's goals.",
        "user_name": "Commander",
        "briefing_mode": True
    }
    res = client.post("/api/chat", json=payload_brief)
    assert res.status_code == 200, f"Briefing chat failed with {res.status_code}"
    brief_data = res.json()
    print(f"✅ /api/chat (Briefing): OK (Model: {brief_data.get('model')})")

    # 4. Validation error for empty message
    res_empty = client.post("/api/chat", json={"message": ""})
    assert res_empty.status_code in (400, 422), "Empty message did not trigger validation error"
    print("✅ /api/chat (Validation check on empty input): OK")


async def test_llm_service_streaming():
    """Test LLM service streaming generation."""
    print("\n--- [2/3] Testing LLM Streaming Service Generator ---")
    service = get_llm_service()
    chunks = []
    async for chunk in service.stream_chat("Hello LARA, report readiness.", "Commander"):
        chunks.append(chunk)

    full_text = "".join(chunks)
    assert len(chunks) > 0, "No stream chunks were produced"
    print(f"✅ LLMService Stream: Generated {len(chunks)} chunks successfully.")
    print(f"   Streamed text preview: \"{full_text[:80]}...\"")


def test_live_server():
    """Optional check against a running server at http://127.0.0.1:8000."""
    print("\n--- [3/3] Checking Live Network Connectivity (if running) ---")
    import httpx
    try:
        with httpx.Client(timeout=2.0) as client:
            res = client.get("http://127.0.0.1:8000/api/health")
            if res.status_code == 200:
                print("✅ Live Server at http://127.0.0.1:8000 is reachable and active.")
            else:
                print(f"⚠️ Live Server returned status {res.status_code}")
    except Exception:
        print("ℹ️ Live server not currently running on port 8000 (standard for offline test). In-process tests verified.")


if __name__ == "__main__":
    # Ensure stdout handles UTF-8 on Windows
    if sys.platform == "win32" and sys.stdout is sys.__stdout__:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("==================================================")
    print("[*] LARA OS - Phase 0 Verification Test Suite")
    print("==================================================")
    try:
        test_in_process_endpoints()
        asyncio.run(test_llm_service_streaming())
        test_live_server()
        print("\n==================================================")
        print("[SUCCESS] ALL PHASE 0 BACKEND TESTS PASSED!")
        print("==================================================")
    except Exception as exc:
        print(f"\n[FAILURE] Phase 0 Verification FAILED: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

