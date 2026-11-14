"""Versioned semantic recall with a deterministic offline lexical fallback."""
import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
import numpy as np
from app.config import settings
from app.schemas.chat import RecalledMemoryItem
from app.services.storage import locked, write_json

logger = logging.getLogger("lara.memory.vector")
LOCAL_VERSION = "blake2-ngrams-v2-512"
STOPWORDS = set("a an the in on at to for is are was were of and or what when how do we i my you your user prefers that me about".split())


def tokens(text):
    return {w for w in re.findall(r"\w+", text.lower().replace("_", " ")) if w not in STOPWORDS}


class VectorMemoryManager:
    def __init__(self):
        self.file_path = os.path.join(settings.LOCAL_DATA_DIR, "vector_memories.json")
        self.memories = self._load_memories()

    def _load_memories(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, encoding="utf-8") as stream:
                return json.load(stream)
        return []

    def _save_memories(self):
        write_json(self.file_path, self.memories)

    def _local_embedding(self, text):
        vector = np.zeros(512)
        def add(token, weight):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            vector[int.from_bytes(digest, "big") % 512] += weight
        for word in sorted(tokens(text)):
            add(word, 3)
            for index in range(max(0, len(word) - 2)):
                add(word[index:index + 3], 0.3)
        norm = np.linalg.norm(vector)
        return (vector / norm if norm else vector).tolist()

    def _embed(self, text, task_type="RETRIEVAL_DOCUMENT"):
        if settings.GEMINI_API_KEY.strip():
            try:
                from google import genai
                with genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"timeout": 8000}) as client:
                    response = client.models.embed_content(
                        model=settings.EMBEDDING_MODEL, contents=text,
                        config={"task_type": task_type, "output_dimensionality": 768})
                values = response.embeddings[0].values
                if values:
                    return values, f"gemini:{settings.EMBEDDING_MODEL}:768"
            except Exception:
                logger.warning("Semantic embedding unavailable; using local lexical recall.")
        return self._local_embedding(text), LOCAL_VERSION

    def _compute_embedding(self, text):
        return self._embed(text)[0]

    @locked
    def add_memory(self, user_id, text, source=None):
        text = text.strip()
        if not text:
            return ""
        embedding, version = self._embed(text)
        for memory in self.memories:
            if memory["user_id"] == user_id and ((source and memory.get("source") == source) or
                    (not source and not memory.get("source") and memory["text"] == text)):
                memory.update(text=text, embedding=embedding, embedding_version=version, source=source)
                self._save_memories()
                return memory["id"]
        record = {"id": f"mem_{uuid.uuid4().hex}", "user_id": user_id, "text": text,
                  "created_at": datetime.now(timezone.utc).isoformat(), "embedding": embedding,
                  "embedding_version": version, "source": source}
        self.memories.append(record)
        self._save_memories()
        return record["id"]

    @locked
    def search_memories(self, user_id, query, top_k=4, min_score=0.2):
        memories = [m for m in self.memories if m.get("user_id") == user_id]
        if not memories:
            return []
        values, version = self._embed(query, "RETRIEVAL_QUERY")
        query_vector = np.array(values, dtype=float)
        query_norm = np.linalg.norm(query_vector)
        if not query_norm:
            return []
        results, dirty = [], False
        for memory in memories:
            if memory.get("embedding_version") != version:
                if version == LOCAL_VERSION:
                    embedding, current = self._local_embedding(memory["text"]), LOCAL_VERSION
                else:
                    embedding, current = self._embed(memory["text"])
                if current != version:
                    continue  # Never compare embeddings from different models/spaces.
                memory.update(embedding=embedding, embedding_version=current)
                dirty = True
            vector = np.array(memory.get("embedding", []), dtype=float)
            if vector.shape != query_vector.shape or not np.linalg.norm(vector):
                continue
            if version == LOCAL_VERSION and not tokens(query).intersection(tokens(memory["text"])):
                continue  # Hash collisions are not evidence of relevance.
            score = float(np.dot(query_vector, vector) / (query_norm * np.linalg.norm(vector)))
            if score >= min_score:
                results.append(RecalledMemoryItem(id=memory["id"], text=memory["text"],
                    source=memory.get("source"), relevance_score=round(score, 3), timestamp=memory.get("created_at", "")))
        if dirty:
            self._save_memories()
        return sorted(results, key=lambda m: m.relevance_score, reverse=True)[:top_k]

    @locked
    def list_memories(self, user_id):
        return [{k: v for k, v in m.items() if k not in ("embedding", "user_id")}
                for m in self.memories if m.get("user_id") == user_id]

    @locked
    def delete_memory(self, user_id, memory_id):
        original = len(self.memories)
        self.memories = [m for m in self.memories if not (m.get("user_id") == user_id and m["id"] == memory_id)]
        if len(self.memories) != original:
            self._save_memories()
            return True
        return False

    @locked
    def remove_source(self, user_id, source, legacy_texts=()):
        self.memories = [m for m in self.memories if not (m.get("user_id") == user_id and
            (m.get("source") == source or (not m.get("source") and m["text"] in legacy_texts)))]
        self._save_memories()

    @locked
    def count_memories(self, user_id):
        return sum(m.get("user_id") == user_id for m in self.memories)


vector_memory = VectorMemoryManager()
