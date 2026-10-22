import pytest

from personal_assistant.memory import MemoryService
from personal_assistant.models import MemoryInput
from personal_assistant.store import MemoryStore
from tests.fakes import FakeProvider


@pytest.fixture
def memory(tmp_path):
    provider = FakeProvider()
    store = MemoryStore(tmp_path / "memory.db", provider.embedding_id)
    return MemoryService(store, provider, top_k=2, min_score=0.3)


def item(content="Prefers Python", key="programming_language_preference"):
    return MemoryInput(key=key, content=content)


def test_memory_survives_reopening_and_retrieves_by_meaning(memory):
    saved, action = memory.save(
        "alice", item("Prefers Vietnamese explanations", "response_language")
    )
    reopened = MemoryService(
        MemoryStore(memory.store.path, "fixture-vectors-v1"), FakeProvider(), 2, 0.3
    )
    hits = reopened.search("alice", "Explain decorators")
    assert action == "added"
    assert hits[0].memory.id == saved.id
    assert hits[0].memory.content == "Prefers Vietnamese explanations"
    assert hits[0].score == pytest.approx(1.0)


def test_duplicate_does_not_create_new_record(memory):
    first, _ = memory.save("alice", item())
    duplicate, action = memory.save("alice", item("  PREFERS   Python  ", "another_key"))
    assert duplicate.id == first.id
    assert action == "unchanged"
    assert len(memory.store.list("alice")) == 1


def test_new_assertion_replaces_same_fact_slot(memory):
    first, _ = memory.save("alice", item())
    memory.store.save_turn("alice", "old-session", "I prefer Python", "Python it is.", 2)
    updated, action = memory.save("alice", item("Prefers Java"))
    assert updated.id == first.id
    assert updated.created_at == first.created_at
    assert updated.content == "Prefers Java"
    assert action == "updated"
    assert len(memory.store.list("alice")) == 1
    assert memory.store.history("alice", "old-session") == []
    assert memory.search("alice", "What language do I prefer?")[0].memory.content == "Prefers Java"


def test_all_crud_operations_enforce_ownership(memory):
    first, _ = memory.save("alice", item())
    assert memory.store.list("bob") == []
    assert memory.search("bob", "What language?") == []
    assert memory.update("bob", first.id, item("Prefers Java")) is None
    assert memory.store.delete("bob", first.id) is False
    assert memory.store.get("bob", first.id) is None
    assert memory.store.get("alice", first.id).content == "Prefers Python"


def test_delete_removes_vector_and_all_user_history(memory):
    first, _ = memory.save("alice", item())
    for session in ("one", "two"):
        memory.store.save_turn("alice", session, "I prefer Python", "Okay", 2)
    memory.store.save_turn("bob", "one", "Private Bob context", "Okay", 2)
    assert memory.store.delete("alice", first.id)
    assert memory.search("alice", "Python") == []
    assert memory.store.history("alice", "one") == []
    assert memory.store.history("alice", "two") == []
    assert memory.store.history("bob", "one")[0]["content"] == "Private Bob context"
    reopened = MemoryStore(memory.store.path, "fixture-vectors-v1")
    assert reopened.list("alice") == []


def test_history_is_bounded_and_session_scoped(memory):
    for number in range(5):
        memory.store.save_turn("alice", "same-id", str(number), "answer", 2)
    assert [m["content"] for m in memory.store.history("alice", "same-id")] == [
        "3",
        "answer",
        "4",
        "answer",
    ]
    assert memory.store.history("bob", "same-id") == []
    assert memory.store.history("alice", "other") == []


@pytest.mark.parametrize("vector", [[], [0, 0], [float("nan"), 1], [float("inf")], [True, 1]])
def test_invalid_vectors_cannot_replace_valid_memory(memory, vector):
    memory.save("alice", item())
    memory.provider.embed = lambda _: vector
    with pytest.raises(ValueError):
        memory.save("alice", item("Prefers Java"))
    assert memory.store.list("alice")[0].content == "Prefers Python"


def test_embedding_model_change_is_explicit(memory):
    memory.save("alice", item())
    with pytest.raises(ValueError, match="embedding"):
        MemoryStore(memory.store.path, "different-model")


def test_changed_embedding_dimension_is_rejected(memory):
    memory.save("alice", item())
    memory.provider.embed = lambda _: [1.0, 0.0]
    with pytest.raises(ValueError, match="dimension"):
        memory.search("alice", "language")


def test_threshold_and_top_k(memory):
    memory.save("alice", item())
    memory.save("alice", item("Likes Java examples", "example_language"))
    memory.save("alice", item("Uses VS Code editor", "editor_preference"))
    hits = memory.search("alice", "What language?")
    assert len(hits) == 2
    assert {hit.memory.key for hit in hits} == {
        "programming_language_preference",
        "example_language",
    }


def test_explicit_update_and_collision(memory):
    first, _ = memory.save("alice", item())
    updated = memory.update("alice", first.id, item("Prefers Java"))
    assert updated.id == first.id
    assert updated.content == "Prefers Java"
    memory.save("alice", item("VS Code editor", "editor_preference"))
    with pytest.raises(ValueError):
        memory.update("alice", first.id, item("VS Code editor", "editor_preference"))
    assert len(memory.store.list("alice")) == 2


@pytest.mark.parametrize(
    "content", ["My password is abc123", "API key sk-secret123", "My diagnosis is X"]
)
def test_sensitive_memories_are_rejected(memory, content):
    with pytest.raises(ValueError, match="sensitive"):
        memory.save("alice", item(content))
    assert memory.store.list("alice") == []


def test_clear_user_data_is_scoped(memory):
    memory.save("alice", item())
    memory.save("bob", item("Prefers Java"))
    memory.store.save_turn("alice", "s", "private", "reply", 2)
    memory.store.delete_user_data("alice")
    assert memory.store.list("alice") == []
    assert memory.store.list_sessions("alice") == []
    assert memory.store.list("bob")[0].content == "Prefers Java"


def test_sensitive_fact_key_is_rejected(memory):
    with pytest.raises(ValueError, match="sensitive"):
        memory.save("alice", item("abcd1234", "password"))
    assert memory.store.list("alice") == []


def test_conflicting_upsert_cannot_silently_retain_old_preference(memory):
    first, _ = memory.save("alice", item("Prefers Python"))
    other, _ = memory.save("alice", item("Prefers Java", "example_language"))
    with pytest.raises(ValueError, match="another key"):
        memory.save("alice", item("Prefers Java"))
    assert memory.store.get("alice", first.id).content == "Prefers Python"
    assert memory.store.get("alice", other.id).content == "Prefers Java"
