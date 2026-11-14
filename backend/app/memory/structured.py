"""Structured memory manager with Firestore integration and local JSON persistence fallback."""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.config import settings
from app.schemas.chat import MessageItem, ProjectItem
from app.services.storage import locked, write_json

logger = logging.getLogger("lara.memory.structured")


class StructuredMemoryManager:
    """Manages short-term conversation sessions, long-term user facts, and ongoing projects."""

    def __init__(self):
        self.local_file_path = os.path.join(settings.LOCAL_DATA_DIR, "structured_memory.json")
        self.firestore_db = None
        self.backend_type = "local_json"

        # Attempt to initialize Firestore if configured
        if settings.FIREBASE_PROJECT_ID:
            self._init_firestore()

        # In-memory cache loaded from local JSON file
        self._data: Dict[str, Any] = self._load_local_data()

    def _init_firestore(self):
        """Initialize Firebase Admin Firestore client if credentials exist."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
                else:
                    firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})

            self.firestore_db = firestore.client()
            self.backend_type = "firestore"
            logger.info("Connected to Google Cloud Firestore successfully for memory storage.")
        except Exception as e:
            logger.warning("Firestore connection failed (%s); using local file persistence.", e)
            self.firestore_db = None
            self.backend_type = "local_json"

    def _load_local_data(self) -> Dict[str, Any]:
        """Load local JSON memory store from disk."""
        if os.path.exists(self.local_file_path):
            try:
                with open(self.local_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                logger.exception("Unable to read saved memory; refusing to overwrite it.")
                raise
        return {"users": {}}

    def _save_local_data(self):
        """Persist in-memory cache to disk."""
        write_json(self.local_file_path, self._data)

    def _ensure_user_exists(self, user_id: str, user_name: str = "Commander"):
        """Ensure user record exists in memory."""
        if "users" not in self._data:
            self._data["users"] = {}
        if user_id not in self._data["users"]:
            self._data["users"][user_id] = {
                "name": user_name,
                "facts": {},
                "projects": {},
                "sessions": {}
            }
            self._save_local_data()

    # -------------------------------------------------------------
    # User Profile & Facts (Long-Term Memory)
    # -------------------------------------------------------------

    @locked
    def get_user_facts(self, user_id: str) -> Dict[str, str]:
        """Retrieve dictionary of all known facts about the user."""
        self._ensure_user_exists(user_id)
        if self.firestore_db:
            try:
                doc = self.firestore_db.collection("users").document(user_id).get()
                if doc.exists:
                    return doc.to_dict().get("facts", {})
            except Exception as e:
                logger.error("Firestore get_user_facts error: %s", e)
        return dict(self._data["users"].get(user_id, {}).get("facts", {}))

    @locked
    def set_user_fact(self, user_id: str, key: str, value: str):
        """Save or update a specific user fact (e.g. 'preferred_region': 'us-central1')."""
        self._ensure_user_exists(user_id)
        self._data["users"][user_id]["facts"][key] = value
        self._save_local_data()

        if self.firestore_db:
            try:
                self.firestore_db.collection("users").document(user_id).set(
                    {"facts": {key: value}}, merge=True
                )
            except Exception as e:
                logger.error("Firestore set_user_fact error: %s", e)

    # -------------------------------------------------------------
    # Ongoing Projects (Structured Project Memory)
    # -------------------------------------------------------------

    @locked
    def get_projects(self, user_id: str) -> List[ProjectItem]:
        """Retrieve all tracked ongoing projects for the user."""
        self._ensure_user_exists(user_id)
        if self.firestore_db:
            documents = self.firestore_db.collection("users").document(user_id).collection("projects").stream()
            projects = {doc.id: doc.to_dict() for doc in documents}
            self._data["users"][user_id]["projects"] = projects
        projects_dict = self._data["users"].get(user_id, {}).get("projects", {})
        results = []
        for p_id, p_data in projects_dict.items():
            results.append(ProjectItem(**p_data))
        return results

    @locked
    def upsert_project(self, user_id: str, project: ProjectItem):
        """Save or update an ongoing project."""
        self._ensure_user_exists(user_id)
        project_dict = project.model_dump()
        project_dict["last_updated"] = datetime.utcnow().isoformat() + "Z"
        
        self._data["users"][user_id]["projects"][project.id] = project_dict
        self._save_local_data()

        if self.firestore_db:
            try:
                self.firestore_db.collection("users").document(user_id).collection("projects").document(project.id).set(
                    project_dict
                )
            except Exception as e:
                logger.error("Firestore upsert_project error: %s", e)

    # -------------------------------------------------------------
    # Short-Term Session History
    # -------------------------------------------------------------

    @locked
    def get_session_history(self, user_id: str, session_id: str, limit: int = 15) -> List[MessageItem]:
        """Fetch recent conversation turns for this session."""
        self._ensure_user_exists(user_id)
        sessions = self._data["users"][user_id].get("sessions", {})
        raw_msgs = sessions.get(session_id, [])
        return [MessageItem(**msg) for msg in raw_msgs[-limit:]]

    @locked
    def append_session_message(self, user_id: str, session_id: str, role: str, content: str):
        """Append a message turn to the session history buffer."""
        self._ensure_user_exists(user_id)
        sessions = self._data["users"][user_id].setdefault("sessions", {})
        session_list = sessions.setdefault(session_id, [])

        msg = MessageItem(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        session_list.append(msg.model_dump())

        # Trim buffer to max turns
        if len(session_list) > settings.SESSION_MAX_TURNS * 2:
            session_list = session_list[-settings.SESSION_MAX_TURNS * 2:]
            sessions[session_id] = session_list

        self._save_local_data()

    @locked
    def clear_session_history(self, user_id: str, session_id: str):
        """Reset short-term conversation history for a session."""
        self._ensure_user_exists(user_id)
        if "sessions" in self._data["users"][user_id]:
            self._data["users"][user_id]["sessions"].pop(session_id, None)
            self._save_local_data()

    @locked
    def clear_all_sessions(self, user_id: str):
        self._ensure_user_exists(user_id)
        self._data["users"][user_id]["sessions"] = {}
        self._save_local_data()

    @locked
    def delete_fact(self, user_id: str, key: str) -> bool:
        self._ensure_user_exists(user_id)
        facts = self.get_user_facts(user_id)
        if key not in facts:
            return False
        if self.firestore_db:
            from firebase_admin import firestore
            self.firestore_db.collection("users").document(user_id).set(
                {"facts": {key: firestore.DELETE_FIELD}}, merge=True)
        self._data["users"][user_id]["facts"].pop(key, None)
        self._save_local_data()
        return True

    @locked
    def delete_project(self, user_id: str, project_id: str) -> bool:
        if project_id not in {p.id for p in self.get_projects(user_id)}:
            return False
        if self.firestore_db:
            self.firestore_db.collection("users").document(user_id).collection("projects").document(project_id).delete()
        self._data["users"][user_id]["projects"].pop(project_id, None)
        self._save_local_data()
        return True


# Singleton
structured_memory = StructuredMemoryManager()
