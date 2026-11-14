"""Memory CRUD routes, preserving the existing profile and upsert contracts."""
import asyncio
import re
from fastapi import APIRouter, HTTPException, Query
from app.schemas.chat import (MemoryProfileResponse, AddFactRequest, AddProjectRequest,
                              ProjectItem, UpdateProjectRequest, UpdateMemoryRequest)
from app.memory.structured import structured_memory
from app.memory.vector import vector_memory
from app.memory.service import memory_service

memory_router = APIRouter(prefix="/memory", tags=["Memory"])


@memory_router.get("/profile", response_model=MemoryProfileResponse)
async def profile(user_id: str = "default_user", session_id: str = "default_session"):
    def load():
        return MemoryProfileResponse(user_id=user_id, user_name="Commander",
            facts=structured_memory.get_user_facts(user_id), projects=structured_memory.get_projects(user_id),
            recent_session_turns=len(structured_memory.get_session_history(user_id, session_id)),
            total_episodic_memories=vector_memory.count_memories(user_id), storage_backend=structured_memory.backend_type)
    return await asyncio.to_thread(load)


@memory_router.post("/fact")
async def save_fact(request: AddFactRequest):
    await asyncio.to_thread(memory_service.save_fact, request.user_id or "default_user", request.key, request.value)
    return {"status": "success"}


@memory_router.put("/fact/{key}")
async def edit_fact(key: str, request: AddFactRequest):
    if key != request.key:
        raise HTTPException(422, "The fact key cannot be changed.")
    facts = await asyncio.to_thread(structured_memory.get_user_facts, request.user_id or "default_user")
    if key not in facts:
        raise HTTPException(404, "Fact not found.")
    return await save_fact(request)


@memory_router.delete("/fact/{key}")
async def delete_fact(key: str, user_id: str = "default_user"):
    if not await asyncio.to_thread(memory_service.delete_fact, user_id, key):
        raise HTTPException(404, "Fact not found.")
    return {"status": "success"}


@memory_router.post("/project")
async def save_project(request: AddProjectRequest):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", request.name).strip("-").lower()
    if not slug:
        raise HTTPException(422, "Project name needs a letter or number.")
    project = ProjectItem(id=slug, name=request.name, status=request.status,
                          summary=request.summary, pending_actions=request.pending_actions or [])
    await asyncio.to_thread(memory_service.save_project, request.user_id or "default_user", project)
    return {"status": "success", "project": project}


@memory_router.put("/project/{project_id}")
async def edit_project(project_id: str, request: UpdateProjectRequest):
    projects = await asyncio.to_thread(structured_memory.get_projects, request.user_id)
    if project_id not in {p.id for p in projects}:
        raise HTTPException(404, "Project not found.")
    project = ProjectItem(id=project_id, **request.model_dump(exclude={"user_id"}))
    await asyncio.to_thread(memory_service.save_project, request.user_id, project)
    return {"status": "success", "project": project}


@memory_router.delete("/project/{project_id}")
async def delete_project(project_id: str, user_id: str = "default_user"):
    if not await asyncio.to_thread(memory_service.delete_project, user_id, project_id):
        raise HTTPException(404, "Project not found.")
    return {"status": "success"}


@memory_router.get("/episodes")
async def episodes(user_id: str = "default_user", limit: int = Query(100, ge=1, le=500)):
    memories = await asyncio.to_thread(vector_memory.list_memories, user_id)
    return memories[-limit:][::-1]


@memory_router.get("/search")
async def search(q: str = Query(min_length=1, max_length=2000), user_id: str = "default_user"):
    return await asyncio.to_thread(vector_memory.search_memories, user_id, q)


@memory_router.put("/episodes/{memory_id}")
async def edit_episode(memory_id: str, request: UpdateMemoryRequest):
    try:
        found = await asyncio.to_thread(memory_service.edit_episode, request.user_id, memory_id, request.text)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if not found:
        raise HTTPException(404, "Memory not found.")
    return {"status": "success"}


@memory_router.delete("/episodes/{memory_id}")
async def delete_episode(memory_id: str, user_id: str = "default_user"):
    if not await asyncio.to_thread(memory_service.delete_episode, user_id, memory_id):
        raise HTTPException(404, "Memory not found.")
    return {"status": "success"}


@memory_router.delete("/session")
async def clear_session(user_id: str = "default_user", session_id: str = "default_session"):
    await asyncio.to_thread(structured_memory.clear_session_history, user_id, session_id)
    return {"status": "success"}
