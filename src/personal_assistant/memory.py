"""Memory validation and semantic retrieval, independent from chat orchestration."""

import math
import re

from personal_assistant.models import MemoryInput, RetrievedMemory
from personal_assistant.store import MemoryStore

# shortcut: heuristics miss obfuscated secrets; add reviewed DLP before deployment.
SENSITIVE = re.compile(
    r"password|passwd|api[ _-]?key|secret|access[ _-]?token|private[ _-]?key|"
    r"sk-[a-z0-9_-]+|diagnos|medical|health condition|credit[ -]?card|social security|"
    r"\bssn\b|mật khẩu|bệnh án|chẩn đoán|\b(?:\d[ -]?){13,19}\b",
    re.IGNORECASE,
)


def is_sensitive(text: str) -> bool:
    return bool(SENSITIVE.search(text))


def requests_no_storage(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:do not|don['’]?t|never)\s+(?:save|remember|store)\b|\boff the record\b",
            text,
            re.IGNORECASE,
        )
    )


def validate_vector(vector) -> list[float]:
    if not isinstance(vector, list) or not vector:
        raise ValueError("Embedding must be a nonempty numeric vector.")
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
        raise ValueError("Embedding must contain only finite numbers.")
    norm = math.hypot(*vector)
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Embedding must have a finite, nonzero norm.")
    return [value / norm for value in vector]


class MemoryService:
    def __init__(self, store: MemoryStore, provider, top_k: int, min_score: float):
        self.store = store
        self.provider = provider
        self.top_k = top_k
        self.min_score = min_score

    def save(self, user_id: str, item: MemoryInput, source_session_id: str | None = None):
        if is_sensitive(f"{item.key} {item.content}"):
            raise ValueError("Potentially sensitive information cannot be saved as memory.")
        vector = validate_vector(self.provider.embed(item.content))
        return self.store.upsert(user_id, item, vector, source_session_id)

    def update(self, user_id: str, memory_id: str, item: MemoryInput):
        if self.store.get(user_id, memory_id) is None:
            return None
        if is_sensitive(f"{item.key} {item.content}"):
            raise ValueError("Potentially sensitive information cannot be saved as memory.")
        vector = validate_vector(self.provider.embed(item.content))
        return self.store.update(user_id, memory_id, item, vector)

    def search(self, user_id: str, query: str) -> list[RetrievedMemory]:
        records = self.store.vectors(user_id)
        if not records:
            return []
        query_vector = validate_vector(self.provider.embed(query))
        hits = []
        for memory, stored_vector in records:
            vector = validate_vector(stored_vector)
            if len(vector) != len(query_vector):
                raise ValueError("Embedding dimension mismatch; use a consistent model.")
            score = max(
                -1.0, min(1.0, sum(a * b for a, b in zip(vector, query_vector, strict=True)))
            )
            if score >= self.min_score:
                hits.append(RetrievedMemory(memory=memory, score=score))
        hits.sort(key=lambda hit: (-hit.score, hit.memory.id))
        return hits[: self.top_k]
