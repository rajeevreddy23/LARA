"""Coordinates structured facts/projects and their searchable representations."""
import re
from app.config import settings
from app.memory.structured import structured_memory
from app.memory.vector import vector_memory, tokens
from app.schemas.chat import ProjectItem
from app.services.storage import locked


class MemoryService:
    @locked
    def save_fact(self, user_id, key, value):
        old = structured_memory.get_user_facts(user_id).get(key)
        legacy = (f"{key}: {old}", f"User prefers {key}: {old}", f"User role is {old}", old)
        vector_memory.remove_source(user_id, f"fact:{key}", legacy)
        structured_memory.set_user_fact(user_id, key, value)
        vector_memory.add_memory(user_id, f"{key}: {value}", source=f"fact:{key}")
        if old is not None and old != value:
            self._clear_stale_context(user_id, str(old))

    @locked
    def save_project(self, user_id, project):
        old = next((p for p in structured_memory.get_projects(user_id) if p.id == project.id), None)
        legacy = (f"Project {old.name}: {old.summary}", f"Ongoing project: {old.name}") if old else ()
        vector_memory.remove_source(user_id, f"project:{project.id}", legacy)
        structured_memory.upsert_project(user_id, project)
        vector_memory.add_memory(user_id, f"Project {project.name}: {project.summary}. " + "; ".join(project.pending_actions),
                                 source=f"project:{project.id}")
        if old and old != project:
            self._clear_stale_context(user_id, old.summary)

    def _clear_stale_context(self, user_id, text):
        # Older releases also indexed raw user statements without source links.
        for memory in vector_memory.list_memories(user_id):
            if not memory.get("source") and text and text.lower() in memory["text"].lower():
                vector_memory.delete_memory(user_id, memory["id"])
        structured_memory.clear_all_sessions(user_id)

    @locked
    def delete_fact(self, user_id, key):
        old = structured_memory.get_user_facts(user_id).get(key)
        if old is None or not structured_memory.delete_fact(user_id, key):
            return False
        vector_memory.remove_source(user_id, f"fact:{key}", (f"{key}: {old}", f"User prefers {key}: {old}", old))
        self._clear_stale_context(user_id, old)
        return True

    @locked
    def delete_project(self, user_id, project_id):
        old = next((p for p in structured_memory.get_projects(user_id) if p.id == project_id), None)
        if not old or not structured_memory.delete_project(user_id, project_id):
            return False
        vector_memory.remove_source(user_id, f"project:{project_id}",
                                    (f"Project {old.name}: {old.summary}", f"Ongoing project: {old.name}"))
        self._clear_stale_context(user_id, old.name)
        return True

    @locked
    def edit_episode(self, user_id, memory_id, text):
        memory = next((m for m in vector_memory.list_memories(user_id) if m["id"] == memory_id), None)
        if not memory:
            return False
        source = memory.get("source") or ""
        if source:
            raise ValueError("Edit this memory through its linked fact or project.")
        vector_memory.delete_memory(user_id, memory_id)
        vector_memory.add_memory(user_id, text)
        structured_memory.clear_all_sessions(user_id)
        return True

    @locked
    def delete_episode(self, user_id, memory_id):
        memory = next((m for m in vector_memory.list_memories(user_id) if m["id"] == memory_id), None)
        if not memory:
            return False
        source = memory.get("source") or ""
        if source.startswith("fact:"):
            return self.delete_fact(user_id, source[5:])
        if source.startswith("project:"):
            return self.delete_project(user_id, source[8:])
        vector_memory.delete_memory(user_id, memory_id)
        structured_memory.clear_all_sessions(user_id)
        return True

    def relevant_context(self, user_id, query, briefing=False):
        recalled = vector_memory.search_memories(user_id, query, top_k=settings.VECTOR_TOP_K)
        words = tokens(query)
        facts = structured_memory.get_user_facts(user_id)
        projects = structured_memory.get_projects(user_id)
        sources = {m.source for m in recalled}
        all_facts = bool(re.search(r"my (profile|facts|preferences)|know about me", query, re.I))
        all_projects = briefing or bool(re.search(r"my projects|active projects|what projects", query, re.I))
        lines = []
        for key, value in facts.items():
            if all_facts or f"fact:{key}" in sources or words.intersection(tokens(f"{key} {value}")):
                lines.append(f"Fact {key}: {value}")
        for project in projects:
            if all_projects or f"project:{project.id}" in sources or words.intersection(tokens(project.name + " " + project.summary)):
                lines.append(f"Project [{project.status}] {project.name}: {project.summary}; pending: {'; '.join(project.pending_actions)}")
        lines.extend(f"Recall: {m.text}" for m in recalled if not m.source)
        context = "\n".join(lines)[:settings.MEMORY_CONTEXT_CHARS]
        return context, recalled


memory_service = MemoryService()
