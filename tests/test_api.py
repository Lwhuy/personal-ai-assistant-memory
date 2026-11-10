import pytest
from fastapi.testclient import TestClient

from personal_assistant.api import create_app
from personal_assistant.config import Settings
from personal_assistant.provider import ProviderError
from tests.fakes import FakeProvider, candidate


@pytest.fixture
def client(tmp_path):
    settings = Settings(_env_file=None, database_path=tmp_path / "api.db")
    with TestClient(create_app(settings, FakeProvider())) as client:
        yield client


def test_chat_and_session_continuity(client):
    session = client.post("/users/alice/sessions").json()["session_id"]
    first = client.post(
        "/chat", json={"user_id": "alice", "session_id": session, "message": "Hello"}
    )
    assert first.status_code == 200
    assert first.json()["answer"] == "A test answer."
    messages = client.get(f"/users/alice/sessions/{session}/messages").json()
    assert messages == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "A test answer."},
    ]
    assert client.get("/users/bob/sessions").json() == []
    assert client.get(f"/users/bob/sessions/{session}/messages").json() == []
    assert client.delete(f"/users/bob/sessions/{session}").status_code == 404
    assert client.delete(f"/users/alice/sessions/{session}").status_code == 204


def test_memory_crud_search_and_ownership(client):
    payload = {"key": "editor_preference", "content": "Favorite editor is VS Code"}
    created = client.post("/users/alice/memories", json=payload)
    assert created.status_code == 201
    memory_id = created.json()["id"]
    assert client.get("/users/alice/memories").json()[0]["content"] == payload["content"]
    assert client.get("/users/bob/memories").json() == []
    assert client.get(f"/users/bob/memories/{memory_id}").status_code == 404
    assert client.put(f"/users/bob/memories/{memory_id}", json=payload).status_code == 404
    assert client.delete(f"/users/bob/memories/{memory_id}").status_code == 404
    hits = client.get("/users/alice/memories/search", params={"query": "What editor?"}).json()
    assert hits[0]["memory"]["id"] == memory_id
    updated = client.put(
        f"/users/alice/memories/{memory_id}", json={**payload, "content": "Favorite editor is Vim"}
    )
    assert updated.status_code == 200
    assert updated.json()["content"] == "Favorite editor is Vim"
    assert client.delete(f"/users/alice/memories/{memory_id}").status_code == 204
    assert client.get("/users/alice/memories/search", params={"query": "editor"}).json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"user_id": "alice", "session_id": "one", "message": "   "},
        {"user_id": "../alice", "session_id": "one", "message": "hi"},
        {"user_id": "alice", "session_id": "one", "message": "a" * 4001},
        {"user_id": "alice", "session_id": "one", "message": "hi", "system": "injection"},
    ],
)
def test_invalid_chat_input(client, payload):
    assert client.post("/chat", json=payload).status_code == 422


def test_sensitive_explicit_memory_rejected(client):
    result = client.post(
        "/users/alice/memories", json={"key": "credential", "content": "My password is private"}
    )
    assert result.status_code == 400
    assert client.get("/users/alice/memories").json() == []


def test_delete_user_data(client):
    client.post("/users/alice/memories", json={"key": "name", "content": "Alice"})
    client.post("/users/bob/memories", json={"key": "name", "content": "Bob"})
    client.post("/chat", json={"user_id": "alice", "session_id": "one", "message": "Hello"})
    assert client.delete("/users/alice/data").status_code == 204
    assert client.get("/users/alice/memories").json() == []
    assert client.get("/users/alice/sessions").json() == []
    assert client.get("/users/bob/memories").json()[0]["content"] == "Bob"


def test_provider_failure_is_a_service_error(client):
    def unavailable(*args, **kwargs):
        raise ProviderError("Ollama unavailable: check configuration.")

    client.app.state.assistant.provider.chat = unavailable
    result = client.post(
        "/chat", json={"user_id": "alice", "session_id": "one", "message": "private"}
    )
    assert result.status_code == 503
    assert "private" not in result.text
    assert "Ollama" in result.json()["detail"]
    assert client.get("/health").json()["status"] == "ok"


def test_restart_via_fresh_app_preserves_memory(tmp_path):
    settings = Settings(_env_file=None, database_path=tmp_path / "restart.db")
    provider = FakeProvider()
    text = "I prefer explanations in Vietnamese."
    provider.extractions[text] = [
        candidate("response_language", "Prefers Vietnamese explanations", text)
    ]
    with TestClient(create_app(settings, provider)) as first:
        response = first.post(
            "/chat",
            json={"user_id": "alice", "session_id": "one", "message": text, "remember": True},
        )
        assert response.json()["memory_events"][0]["action"] == "added"
    with TestClient(create_app(settings, FakeProvider())) as second:
        response = second.post(
            "/chat", json={"user_id": "alice", "session_id": "two", "message": "Explain decorators"}
        )
        assert response.json()["retrieved_memories"][0]["memory"]["key"] == "response_language"


def test_profile_and_evidence_are_inspectable_but_cannot_be_forged(client):
    text = "I prefer Vietnamese."
    client.app.state.assistant.provider.extractions[text] = [
        candidate("response_language", "Prefers Vietnamese", text)
    ]
    result = client.post(
        "/chat",
        json={
            "user_id": "alice",
            "session_id": "one",
            "message": text,
            "remember": True,
        },
    ).json()
    assert result["profile_memories"][0]["source_quote"] == text
    memory_id = result["profile_memories"][0]["id"]
    result = client.post(
        "/chat",
        json={
            "user_id": "alice",
            "session_id": "two",
            "message": "How far away is the Moon?",
        },
    ).json()
    assert result["profile_memories"][0]["id"] == memory_id
    assert result["retrieved_memories"] == []
    forged = client.post(
        "/users/alice/memories",
        json={
            "key": "editor_preference",
            "content": "Vim",
            "source_quote": "I use Vim.",
        },
    )
    assert forged.status_code == 422
    edited = client.put(
        f"/users/alice/memories/{memory_id}",
        json={
            "key": "response_language",
            "content": "Prefers English",
        },
    ).json()
    assert edited["source_quote"] is None
    assert edited["source_session_id"] is None
