"""Environment configuration; no external service is contacted while loading it."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    backend_url: str = "http://127.0.0.1:8000"
    chat_model: str = Field(default="qwen2.5:3b", min_length=1)
    embedding_model: str = Field(default="nomic-embed-text", min_length=1)
    database_path: Path = Path("data/assistant.sqlite3")
    history_turns: int = Field(default=6, ge=1, le=20)
    memory_top_k: int = Field(default=4, ge=1, le=10)
    memory_min_score: float = Field(default=0.25, ge=-1, le=1)
    request_timeout_seconds: float = Field(default=120, gt=0, le=600)
