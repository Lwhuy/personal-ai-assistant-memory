"""Opt-in model evaluation: explicitly enabled unavailable models fail, rather than skip."""

import os
import re

import pytest

from personal_assistant.agent import Assistant
from personal_assistant.config import Settings
from personal_assistant.models import MemoryInput
from personal_assistant.provider import OllamaProvider

pytestmark = [
    pytest.mark.ollama,
    pytest.mark.skipif(
        os.getenv("RUN_OLLAMA_TESTS") != "1",
        reason="Set RUN_OLLAMA_TESTS=1 for live Ollama evaluation",
    ),
]


def test_live_scenarios_a_through_e(tmp_path):
    settings = Settings(database_path=tmp_path / "live.db")
    provider = OllamaProvider(settings)
    try:
        assistant = Assistant(settings, provider)
        assistant.chat(
            "alice",
            "one",
            "I am learning Python and I prefer explanations in Vietnamese.",
            remember=True,
        )
        assert any(m.key == "response_language" for m in assistant.store.list("alice"))
        restarted = Assistant(settings, provider)
        answer = restarted.chat("alice", "two", "Can you explain decorators?")
        assert any(hit.memory.key == "response_language" for hit in answer.retrieved_memories)
        assert re.search(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", answer.answer)
        print("Scenario A (inspect explanation correctness and Vietnamese):", answer.answer)

        restarted.memory.save(
            "alice", MemoryInput(key="programming_language_preference", content="Prefers Python")
        )
        restarted.chat(
            "alice", "three", "I used to prefer Python, but now I prefer Java.", remember=True
        )
        preference = next(
            m for m in restarted.store.list("alice") if m.key == "programming_language_preference"
        )
        assert "java" in preference.content.lower()
        assert "python" not in preference.content.lower()
        restarted.chat("alice", "four", "Forget my programming language preference.")
        assert restarted.store.get("alice", preference.id) is None
        hits = restarted.memory.search("alice", "preferred programming language")
        assert all(hit.memory.id != preference.id for hit in hits)

        restarted.chat("alice", "five", "My favorite editor is VS Code.", remember=True)
        bob = restarted.chat("bob", "five", "What is my favorite editor?")
        assert bob.retrieved_memories == []
        assert "vs code" not in bob.answer.lower()
        print("Scenario D (inspect abstention):", bob.answer)
        before = len(restarted.store.list("alice"))
        unknown = restarted.chat(
            "alice",
            "six",
            "Please answer in English: What is my favorite database?",
            remember=True,
        )
        assert len(restarted.store.list("alice")) == before
        assert not any(
            hit.memory.key == "database_preference" for hit in unknown.retrieved_memories
        )
        assert re.search(
            r"don't know|do not know|not (?:provided|shared|have|know)|"
            r"no information|unsure|haven't",
            unknown.answer,
            re.IGNORECASE,
        )
        print("Scenario E (inspect abstention):", unknown.answer)
    finally:
        provider.close()
