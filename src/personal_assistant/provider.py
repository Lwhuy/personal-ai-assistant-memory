"""Ollama's native HTTP API; failures never include upstream bodies or user text."""

from typing import Protocol

import httpx

from personal_assistant.config import Settings
from personal_assistant.memory import validate_vector


class ProviderError(RuntimeError):
    pass


class Provider(Protocol):
    embedding_id: str

    def chat(self, messages: list[dict[str, str]], *, schema: dict | None = None) -> str: ...

    def embed(self, text: str) -> list[float]: ...


class OllamaProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_id = f"ollama:{settings.embedding_model}"
        self.client = httpx.Client(
            base_url=settings.ollama_base_url, timeout=settings.request_timeout_seconds
        )

    def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            response = self.client.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError("Invalid object")
            return result
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(
                "Ollama request failed. Start Ollama and pull CHAT_MODEL and EMBEDDING_MODEL; "
                "check OLLAMA_BASE_URL and the configured timeout."
            ) from exc

    def chat(self, messages: list[dict[str, str]], *, schema: dict | None = None) -> str:
        payload = {
            "model": self.settings.chat_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 1024},
        }
        if schema is not None:
            payload["format"] = schema
        result = self._post("/api/chat", payload)
        try:
            content = result["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty answer")
            return content[:8000]
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(
                "Ollama returned an invalid chat response. Check CHAT_MODEL."
            ) from exc

    def embed(self, text: str) -> list[float]:
        result = self._post(
            "/api/embed",
            {
                "model": self.settings.embedding_model,
                "input": text,
                "truncate": False,
            },
        )
        try:
            vectors = result["embeddings"]
            if not isinstance(vectors, list) or len(vectors) != 1 or not vectors[0]:
                raise ValueError("Invalid embeddings")
            validate_vector(vectors[0])
            return vectors[0]
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(
                "Ollama returned invalid embeddings. Check EMBEDDING_MODEL."
            ) from exc

    def close(self):
        self.client.close()
