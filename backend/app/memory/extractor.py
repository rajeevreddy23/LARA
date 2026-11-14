"""Autonomous memory extraction pipeline to discover user facts and project updates from conversation."""

import re
import logging
import uuid
from typing import List, Tuple
from app.memory.structured import structured_memory
from app.memory.vector import vector_memory
from app.schemas.chat import ProjectItem
from app.memory.service import memory_service

logger = logging.getLogger("lara.memory.extractor")


class MemoryExtractor:
    """Extracts facts, preferences, and project updates from natural language user turns."""

    def extract_and_persist(self, user_id: str, user_message: str) -> List[str]:
        """
        Scan user input for key facts, preferences, and ongoing tasks.
        Persists identified information and returns list of extracted summary strings.
        """
        extracted_facts: List[str] = []
        text = user_message.strip()
        if re.match(r"^(?:remember when|did i mention|what|how|why|who|when|can you|could you|do you)\b", text, re.I):
            return []

        # 1. Explicit Remember pattern: "Remember that X", "Remember X", "Don't forget that X"
        rem_match = re.search(r"^(?:remember\s+(?:that\s+)?|don't\s+forget\s+(?:that\s+)?)(.+)", text, re.IGNORECASE)
        if rem_match:
            fact_body = rem_match.group(1).strip()
            # Clean trailing punctuation
            fact_body = re.sub(r"[.!?]+$", "", fact_body)
            key = "note_" + uuid.uuid4().hex[:12]
            memory_service.save_fact(user_id, key, fact_body)
            extracted_facts.append(f"Remembered: '{fact_body}'")

        # 2. Preference pattern: "My preferred X is Y", "I prefer X"
        pref_match = re.search(r"(?:my\s+preferred\s+([a-zA-Z\s_]+)\s+is\s+([^\n.]+)|i\s+prefer\s+([^\n.]+))", text, re.IGNORECASE)
        if pref_match:
            if pref_match.group(1) and pref_match.group(2):
                cat = pref_match.group(1).strip().replace(" ", "_").lower()
                val = pref_match.group(2).strip()
                memory_service.save_fact(user_id, cat, val)
                extracted_facts.append(f"Preference noted: {cat} -> {val}")
            elif pref_match.group(3):
                memory_service.save_fact(user_id, "general_preference", pref_match.group(3).strip())
                extracted_facts.append("Preference saved")

        # 3. Project / Task Working pattern: "I am working on X", "I'm developing X", "Working on X"
        proj_match = re.search(r"(?:i\s+am\s+working\s+on\s+|i'm\s+working\s+on\s+|working\s+on\s+|building\s+)([a-zA-Z0-9\s_-]+)", text, re.IGNORECASE)
        if proj_match:
            proj_name = proj_match.group(1).strip()
            proj_name = re.sub(r"[.!?]+$", "", proj_name)
            if len(proj_name) > 3 and not any(w in proj_name.lower() for w in ["it", "this", "something", "that"]):
                slug = re.sub(r"[^a-zA-Z0-9]+", "-", proj_name).strip("-").lower()
                project = ProjectItem(
                    id=slug,
                    name=proj_name,
                    status="active",
                    summary=f"Active project: {proj_name}",
                    pending_actions=[]
                )
                existing = next((p for p in structured_memory.get_projects(user_id) if p.id == slug), None)
                if not existing:
                    memory_service.save_project(user_id, project)
                extracted_facts.append(f"Tracked Project: {proj_name}")

        # 4. Role / Identity pattern: "I am a [role]", "I work as a [role]"
        role_match = re.search(r"(?:i\s+am\s+a\s+|i\s+work\s+as\s+(?:a\s+)?)([a-zA-Z\s]+(?:\bdeveloper\b|\bengineer\b|\barchitect\b|\bdesigner\b|\bmanager\b|\blead\b))", text, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip()
            memory_service.save_fact(user_id, "role", role)
            extracted_facts.append(f"Role updated: {role}")

        # If substantial statement, also index into vector memory for semantic search
        if not extracted_facts and len(text) > 25 and re.match(r"^(?:i (?:am|work|like|live|use)|my )", text, re.I):
            vector_memory.add_memory(user_id, text)

        return extracted_facts


# Singleton
memory_extractor = MemoryExtractor()
