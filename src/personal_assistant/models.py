"""Validated HTTP, extraction, and persistence contracts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Identifier = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")]


class MemoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    content: str = Field(min_length=1, max_length=500)
    memory_type: Literal["semantic", "episodic", "procedural"] = "semantic"


class Candidate(MemoryInput):
    source_quote: str = Field(min_length=3, max_length=1000)


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memories: list[Candidate] = Field(default_factory=list, max_length=5)


class Memory(MemoryInput):
    id: str
    user_id: str
    source_session_id: str | None = None
    source_quote: str | None = Field(default=None, min_length=3, max_length=1000)
    created_at: datetime
    updated_at: datetime


class RetrievedMemory(BaseModel):
    memory: Memory
    score: float
    retrieval_method: Literal["semantic", "keyword", "hybrid"] = "semantic"
    rank_score: float = 0.0


class MemoryEvent(BaseModel):
    action: str
    key: str | None = None
    memory_id: str | None = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: Identifier
    session_id: Identifier
    message: str = Field(min_length=1, max_length=4000)
    remember: bool = False


class ChatResult(BaseModel):
    session_id: str
    answer: str
    retrieved_memories: list[RetrievedMemory] = Field(default_factory=list)
    profile_memories: list[Memory] = Field(default_factory=list)
    memory_events: list[MemoryEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
