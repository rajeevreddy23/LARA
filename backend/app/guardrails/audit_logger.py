"""Audit logging engine recording all tool calls, risk assessments, and decision rationales."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings

logger = logging.getLogger("lara.guardrails.audit")


class AuditLogger:
    """Maintains an append-only structured audit trail for LARA's tool calls and decisions."""

    def __init__(self):
        self.file_path = os.path.join(settings.LOCAL_DATA_DIR, "audit_log.json")
        self.logs: List[Dict[str, Any]] = self._load_logs()

    def _load_logs(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error reading audit log from disk: %s", e)
        return []

    def _save_logs(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save audit logs: %s", e)

    def log_decision(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        risk_level: str,
        status: str,
        rationale: str,
        execution_latency_ms: float = 0.0,
        confirmed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record an audit entry for a tool decision or execution."""
        entry_id = f"audit_{int(datetime.utcnow().timestamp())}_{len(self.logs) + 1}"
        entry = {
            "id": entry_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "risk_level": risk_level,  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
            "status": status,          # "AUTHORIZED", "EXECUTED", "BLOCKED", "REJECTED", "PENDING_CONFIRMATION"
            "rationale": rationale,
            "confirmed_by": confirmed_by,
            "execution_latency_ms": execution_latency_ms,
        }
        self.logs.append(entry)
        self._save_logs()
        logger.info("AUDIT [%s] Tool: %s, Risk: %s, Status: %s", entry_id, tool_name, risk_level, status)
        return entry

    def get_logs(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs."""
        filtered = self.logs
        if user_id:
            filtered = [l for l in self.logs if l.get("user_id") == user_id]
        return filtered[-limit:][::-1]


# Singleton
audit_logger = AuditLogger()
