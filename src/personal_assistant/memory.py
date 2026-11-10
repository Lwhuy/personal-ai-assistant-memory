"""Memory validation and hybrid retrieval, independent from chat orchestration."""

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

    def save(
        self,
        user_id: str,
        item: MemoryInput,
        source_session_id: str | None = None,
        *,
        source_quote: str | None = None,
    ):
        if is_sensitive(f"{item.key} {item.content} {source_quote or ''}"):
            raise ValueError("Potentially sensitive information cannot be saved as memory.")
        if source_quote is not None and (
            not source_session_id or not 3 <= len(source_quote) <= 1000
        ):
            raise ValueError("Source evidence requires a conversation and a bounded quote.")
        vector = validate_vector(self.provider.embed(item.content))
        return self.store.upsert(
            user_id, item, vector, source_session_id, source_quote=source_quote
        )

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
        scores = {}
        for memory, stored_vector in records:
            vector = validate_vector(stored_vector)
            if len(vector) != len(query_vector):
                raise ValueError("Embedding dimension mismatch; use a consistent model.")
            score = max(
                -1.0, min(1.0, sum(a * b for a, b in zip(vector, query_vector, strict=True)))
            )
            scores[memory.id] = score
        semantic = sorted(
            (memory for memory, _ in records if scores[memory.id] >= self.min_score),
            key=lambda memory: (-scores[memory.id], memory.id),
        )[: self.top_k]
        keyword = self.store.keyword_search(user_id, query, self.top_k)
        hits = {}
        for method, memories in (("semantic", semantic), ("keyword", keyword)):
            for rank, memory in enumerate(memories, 1):
                if memory.id not in hits:
                    hits[memory.id] = RetrievedMemory(
                        memory=memory, score=scores[memory.id], retrieval_method=method
                    )
                else:
                    hits[memory.id].retrieval_method = "hybrid"
                hits[memory.id].rank_score += 1 / (60 + rank)
        return sorted(hits.values(), key=lambda hit: (-hit.rank_score, hit.memory.id))[: self.top_k]
