import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.llm_service import get_llm_service
from app.services.agent import agent_coordinator

agent_router = APIRouter(tags=["Agent"])


@agent_router.post("/chat/stream")
async def stream_chat(request: ChatRequest, service=Depends(get_llm_service)):
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty.")
    async def events():
        async for event in service.stream_events(request):
            yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@agent_router.get("/tasks")
async def tasks(user_id: str = "default_user", session_id: str | None = None):
    return agent_coordinator.list_tasks(user_id, session_id)
