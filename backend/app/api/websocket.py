"""WebSocket handler for streaming chat tokens and proactive event broadcasting."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.llm_service import get_llm_service
from app.config import settings
from app.proactivity.scheduler import proactivity_scheduler

logger = logging.getLogger("lara.websocket")
ws_router = APIRouter()


@ws_router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time token-by-token streaming and proactive alerts.
    """
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    proactivity_scheduler.register_websocket(websocket)
    llm_service = get_llm_service()
    logger.info("WebSocket client connected and registered for proactive events.")

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except json.JSONDecodeError:
                payload = {"message": raw_data}

            from app.schemas.chat import ChatRequest
            from pydantic import ValidationError
            try:
                request = ChatRequest.model_validate(payload)
                if not request.message.strip():
                    raise ValueError("Empty message")
            except (ValidationError, ValueError):
                await websocket.send_json({"event": "error", "text": "Invalid chat request."})
                continue
            async for event in llm_service.stream_events(request):
                await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally.")
    except Exception as e:
        logger.error("WebSocket exception: %s", e)
        try:
            await websocket.send_json({
                "event": "error",
                "text": f"WebSocket server error: {str(e)}"
            })
        except Exception:
            pass
    finally:
        proactivity_scheduler.unregister_websocket(websocket)
