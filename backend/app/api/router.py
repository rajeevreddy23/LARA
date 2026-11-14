"""REST API router with Chat, Memory, Skills, Proactivity, and Guardrails endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from app.config import settings
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MemoryProfileResponse,
    AddFactRequest,
    AddProjectRequest,
    ProjectItem,
    SkillInfo,
    ExecuteSkillRequest,
    ToolExecutionItem,
    PendingActionItem,
    AuditLogItem,
    ConfirmActionRequest,
    TTSRequest
)
from app.services.llm_service import LLMService, get_llm_service
from app.memory.structured import structured_memory
from app.memory.vector import vector_memory
from app.skills.registry import skill_registry
from app.proactivity.briefing import briefing_generator
from app.proactivity.scheduler import proactivity_scheduler
from app.guardrails.risk_guardian import risk_guardian
from app.guardrails.audit_logger import audit_logger

from app.api.memory import memory_router
from app.api.agent import agent_router
from app.services.agent import agent_coordinator

api_router = APIRouter()
api_router.include_router(memory_router)
api_router.include_router(agent_router)


@api_router.get("/health", response_model=HealthResponse, tags=["System"])
async def get_health(llm_service: LLMService = Depends(get_llm_service)):
    """Health check endpoint providing system readiness, skills, and memory backend status."""
    skills = [s["name"] for s in skill_registry.list_skills()]
    return HealthResponse(
        status="operational",
        name="LARA OS Orchestrator",
        version="0.5.0",
        phase="Phase 5 (Guardrails & Risk Guardian)",
        model_configured=llm_service.is_configured,
        active_model=settings.MODEL_NAME,
        active_skills=skills,
        memory_backend=structured_memory.backend_type,
        guardrails_active=True,
    )


@api_router.post("/chat", response_model=ChatResponse, tags=["Conversation"])
async def chat_endpoint(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Primary chat endpoint with Risk Guardian Interception, Skill routing,
    Context injection, Memory recall, and Persona enforcement.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    response = await llm_service.generate_chat(request)
    return response


# -------------------------------------------------------------
# Guardrails Endpoints (Phase 5)
# -------------------------------------------------------------

@api_router.get("/guardrails/pending", tags=["Guardrails"])
async def list_pending_actions(user_id: str = Query("default_user")):
    """List all paused actions awaiting user confirmation."""
    return risk_guardian.list_pending_actions(user_id=user_id)


@api_router.post("/guardrails/confirm", tags=["Guardrails"])
async def confirm_action(request: ConfirmActionRequest):
    """Approve or reject a pending tool action ticket."""
    planned = await agent_coordinator.resolve_approval(request.ticket_id, request.user_id or "default_user", request.confirmed)
    if planned is not None:
        from app.memory.structured import structured_memory
        import asyncio
        await asyncio.to_thread(structured_memory.append_session_message,
            planned.task["user_id"], planned.task["session_id"], "assistant", planned.response)
        return {
            "status": planned.status, "success": planned.status == "success",
            "skill_name": planned.tool_execution.tool_name if planned.tool_execution else "agent",
            "output": planned.response, "chat_response": planned.model_dump(),
        }
    if request.confirmed:
        exec_res = await risk_guardian.confirm_and_execute(request.ticket_id, user_id=request.user_id or "default_user")
        if not exec_res:
            raise HTTPException(status_code=404, detail="Pending action ticket not found or expired.")
        skill_name, result = exec_res
        return {
            "status": "authorized_and_executed" if result.success else "execution_error",
            "skill_name": skill_name,
            "output": result.output,
            "success": result.success,
        }
    else:
        success = risk_guardian.reject_action(request.ticket_id, user_id=request.user_id or "default_user")
        if not success:
            raise HTTPException(status_code=404, detail="Pending action ticket not found or expired.")
        return {"status": "rejected", "message": f"Action ticket '{request.ticket_id}' aborted."}


@api_router.get("/guardrails/audit-logs", tags=["Guardrails"])
async def get_audit_logs(
    limit: int = Query(50, description="Max logs to return"),
    user_id: str = Query("default_user", description="User ID")
):
    """Retrieve decision rationale and tool execution audit trail."""
    return audit_logger.get_logs(limit=limit, user_id=user_id)


# -------------------------------------------------------------
# Proactivity Endpoints (Phase 4)
# -------------------------------------------------------------

@api_router.get("/proactivity/briefing", tags=["Proactivity"])
async def get_executive_briefing(
    user_id: str = Query("default_user"),
    user_name: str = Query("Commander")
):
    """Generate and return an autonomous executive briefing."""
    return briefing_generator.generate_briefing(user_id=user_id, user_name=user_name)


@api_router.get("/proactivity/followups", tags=["Proactivity"])
async def get_proactive_followups(
    user_id: str = Query("default_user"),
    user_name: str = Query("Commander")
):
    """Return all active follow-up items and scheduled alerts."""
    return proactivity_scheduler.check_followups(user_id=user_id, user_name=user_name)


@api_router.post("/proactivity/trigger", tags=["Proactivity"])
async def trigger_proactive_evaluation(user_id: str = "default_user"):
    """Manually trigger a proactive evaluation and broadcast to WebSockets."""
    await proactivity_scheduler.execute_proactive_check(user_id=user_id)
    return {"status": "success", "message": "Proactive check evaluated and broadcasted."}


# -------------------------------------------------------------
# Skills & Tool Endpoints (Phase 2)
# -------------------------------------------------------------

@api_router.get("/skills", response_model=List[SkillInfo], tags=["Skills"])
async def list_skills():
    """List all registered tools/skills in LARA's registry."""
    return skill_registry.list_skills()


@api_router.post("/skills/execute", response_model=ToolExecutionItem | ChatResponse, tags=["Skills"])
async def execute_skill(request: ExecuteSkillRequest):
    """Directly trigger and execute a registered skill with parameters."""
    skill = skill_registry.get_skill(request.skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{request.skill_name}' not found.")

    user_id = request.user_id or "default_user"
    risk, needs_approval, rationale = risk_guardian.assess_risk(request.skill_name, request.params, user_id=user_id)
    if needs_approval:
        ticket = risk_guardian.create_pending_action(user_id, request.skill_name, request.params, risk, rationale)
        return ChatResponse(
            response=rationale,
            model="lara-guardrail:gatekeeper",
            status="pending_confirmation",
            pending_action=PendingActionItem(**{k: v for k, v in ticket.to_dict().items() if k != "user_id"}),
        )
    res = await skill.execute(request.params, user_id=user_id)
    audit_logger.log_decision(
        user_id=user_id, tool_name=request.skill_name, parameters=request.params,
        risk_level=risk, status="AUTO_AUTHORIZED" if res.success else "EXECUTION_ERROR",
        rationale=rationale, execution_latency_ms=res.execution_time_ms,
    )
    return ToolExecutionItem(
        tool_name=request.skill_name,
        output=res.output,
        success=res.success,
        latency_ms=res.execution_time_ms,
        mutated_state=res.mutated_state
    )


# -------------------------------------------------------------
# Device Bridge & Mobile Pairing Endpoints
# -------------------------------------------------------------

@api_router.get("/device/info", tags=["Device Bridge"])
async def get_device_info():
    """Returns local network IPs, hostname, and mobile pairing access URLs."""
    import socket
    hostname = socket.gethostname()
    local_ips = []
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        local_ips.append(primary_ip)
    except Exception:
        primary_ip = "127.0.0.1"

    try:
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in local_ips and not ip.startswith("127."):
                local_ips.append(ip)
    except Exception:
        pass

    if "127.0.0.1" not in local_ips:
        local_ips.append("127.0.0.1")

    return {
        "hostname": hostname,
        "primary_ip": primary_ip,
        "all_ips": local_ips,
        "frontend_port": 3000,
        "backend_port": 8000,
        "mobile_web_url": f"http://{primary_ip}:3000",
        "backend_api_url": f"http://{primary_ip}:8000",
        "qr_code_target": f"http://{primary_ip}:3000",
        "status": "ready"
    }


# -------------------------------------------------------------
# Fast Mail & File Explorer Endpoints
# -------------------------------------------------------------

@api_router.get("/mail/inbox", tags=["Mail Hub"])
async def get_mail_inbox():
    """Retrieve full inbox and unread summary for HUD."""
    from app.skills.mail_hub import MailHubSkill
    mail_skill: MailHubSkill = skill_registry.get_skill("mail_hub")  # type: ignore
    if not mail_skill:
        return {"inbox": [], "drafts": [], "unread_count": 0}
    data = mail_skill._read_data()
    inbox = data.get("inbox", [])
    unread_count = len([m for m in inbox if m.get("unread", False)])
    return {
        "inbox": inbox,
        "drafts": data.get("drafts", []),
        "unread_count": unread_count
    }


@api_router.get("/files/browse", tags=["File Hub"])
async def browse_files(path: str = Query("D:\\LARA", description="Path or alias to explore")):
    """Retrieve directory items for File Explorer Widget."""
    import os
    from datetime import datetime
    from app.skills.system_file_hub import SystemFileHubSkill
    
    file_skill: SystemFileHubSkill = skill_registry.get_skill("system_file_hub")  # type: ignore
    resolved = file_skill._resolve_folder_alias(path) if file_skill else path
    
    if not os.path.exists(resolved) or not os.path.isdir(resolved):
        resolved = os.path.dirname(resolved) if os.path.exists(resolved) else "D:\\LARA"

    items = []
    try:
        for item in os.listdir(resolved):
            if item.startswith(".") and item not in [".env", ".gitignore"]:
                continue
            full = os.path.join(resolved, item)
            is_d = os.path.isdir(full)
            sz = 0 if is_d else os.path.getsize(full)
            mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
            items.append({
                "name": item,
                "path": full,
                "is_dir": is_d,
                "size_kb": round(sz / 1024, 1),
                "modified": mtime
            })
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    except Exception as e:
        return {"path": resolved, "error": str(e), "items": []}

    return {
        "path": resolved,
        "parent_path": os.path.dirname(resolved),
        "total_items": len(items),
        "items": items[:50]
    }


@api_router.get("/system/apps", tags=["System Apps"])
async def get_installed_apps():
    """Retrieve scanned installed applications across Windows."""
    from app.skills.system_control import SystemControlSkill
    sys_skill: SystemControlSkill = skill_registry.get_skill("system_control")  # type: ignore
    if not sys_skill:
        return {"total": 0, "apps": []}
    apps_dict = sys_skill.scan_installed_apps()
    app_list = list(apps_dict.values())
    app_list.sort(key=lambda x: (x.get("category", "Other"), x.get("name", "").lower()))
    return {
        "total": len(app_list),
        "apps": app_list
    }


@api_router.post("/voice/tts", tags=["Voice Engine"])
async def generate_voice_tts(req: TTSRequest):
    """Generate high-fidelity streaming neural speech audio."""
    from app.services.voice_service import voice_service
    audio_bytes = await voice_service.generate_speech_bytes(
        text=req.text,
        voice=req.voice,
        rate=req.rate or "+5%",
        pitch=req.pitch or "+2Hz"
    )
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@api_router.get("/voice/tts", tags=["Voice Engine"])
async def stream_voice_tts(text: str = Query(..., min_length=1), voice: str = Query("en-US-AriaNeural")):
    """GET endpoint to stream speech audio for any text."""
    from app.services.voice_service import voice_service
    audio_bytes = await voice_service.generate_speech_bytes(text=text, voice=voice)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")
    return Response(content=audio_bytes, media_type="audio/mpeg")
