import sqlite3
import unicodedata

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


def test_keyword_search_rescues_exact_name_below_vector_threshold(memory):
    memory.provider.embed = lambda _: [1.0, 0.0]
    saved, _ = memory.save("alice", item("Project ZEPHYR-42 uses SQLite", "project"))
    memory.save("bob", item("Project ZEPHYR-42 is private", "project"))
    memory.provider.embed = lambda _: [0.0, 1.0]
    hits = memory.search("alice", "Tell me about ZEPHYR-42")
    assert [hit.memory.id for hit in hits] == [saved.id]
    assert hits[0].score == pytest.approx(0.0)
    assert hits[0].retrieval_method == "keyword"
    assert hits[0].rank_score > 0
    assert memory.search("alice", '" OR * : ( )') == []


def test_hybrid_match_is_unique_and_top_k_is_preserved(memory):
    saved, _ = memory.save("alice", item("Prefers Python"))
    hits = memory.search("alice", "Python")
    assert [hit.memory.id for hit in hits] == [saved.id]
    assert hits[0].retrieval_method == "hybrid"
    assert hits[0].score == pytest.approx(1.0)


def test_keyword_index_tracks_updates_and_all_deletion_paths(memory):
    saved, _ = memory.save("alice", item("Uses Zephyr", "project"))
    memory.save("bob", item("Uses Zephyr", "project"))
    memory.update("alice", saved.id, item("Uses Nimbus", "project"))
    assert memory.store.keyword_search("alice", "Zephyr", 4) == []
    assert memory.store.keyword_search("alice", "Nimbus", 4)[0].id == saved.id
    memory.save("alice", item("Uses Aurora", "project"))
    assert memory.store.keyword_search("alice", "Nimbus", 4) == []
    assert memory.store.keyword_search("alice", "Aurora", 4)[0].id == saved.id
    assert memory.store.delete("alice", saved.id)
    assert memory.store.keyword_search("alice", "Aurora", 4) == []
    memory.save("alice", item("Uses Zephyr", "project"))
    memory.store.forget_keys("alice", ["project"])
    assert memory.store.keyword_search("alice", "Zephyr", 4) == []
    memory.save("alice", item("Uses Zephyr", "project"))
    memory.store.delete_user_data("alice")
    assert memory.store.keyword_search("alice", "Zephyr", 4) == []
    assert len(memory.store.keyword_search("bob", "Zephyr", 4)) == 1


def test_keyword_search_accepts_vietnamese_and_escapes_fts_syntax(memory):
    saved, _ = memory.save("alice", item("Dự án SaoMai dùng SQLite", "project"))
    assert memory.store.keyword_search("alice", 'SaoMai" OR (missing*)', 4)[0].id == saved.id
    assert memory.store.keyword_search("alice", "SQLite:NEAR", 4)[0].id == saved.id


def test_keyword_search_handles_decomposed_vietnamese_query(memory):
    saved, _ = memory.save("alice", item("tiếng", "example_word"))
    for query in ("tiếng", unicodedata.normalize("NFD", "tiếng")):
        assert [hit.id for hit in memory.store.keyword_search("alice", query, 4)] == [saved.id]


@pytest.mark.parametrize(
    "mutation", ["delete", "update", "upsert", "legacy_delete", "legacy_update"]
)
def test_mutations_invalidate_other_quotes_that_may_repeat_old_facts(memory, mutation):
    quote = "I use Neovim and prefer Vietnamese."
    editor, _ = memory.save(
        "alice", item("Uses Neovim", "editor_preference"), "s", source_quote=quote
    )
    profile, _ = memory.save(
        "alice", item("Prefers Vietnamese", "response_language"), "s", source_quote=quote
    )
    bob, _ = memory.save(
        "bob", item("Prefers Vietnamese", "response_language"), "s", source_quote=quote
    )
    if mutation == "delete":
        memory.store.delete("alice", editor.id)
    elif mutation == "update":
        memory.update("alice", editor.id, item("Uses Vim", "editor_preference"))
    elif mutation == "upsert":
        memory.save(
            "alice", item("Uses Vim", "editor_preference"), "new", source_quote="I use Vim."
        )
    else:
        with memory.store.connection() as db:
            if mutation == "legacy_delete":
                db.execute("DELETE FROM memories WHERE id=?", (editor.id,))
            else:
                db.execute("UPDATE memories SET content='Uses Vim' WHERE id=?", (editor.id,))
    assert memory.store.get("alice", profile.id).source_quote is None
    assert memory.store.get("bob", bob.id).source_quote == quote


def test_legacy_database_backfills_without_changing_existing_data(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO metadata VALUES ('embedding_model', 'fixture-vectors-v1');
            CREATE TABLE memories (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, key TEXT NOT NULL,
                content TEXT NOT NULL, memory_type TEXT NOT NULL,
                source_session_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                content_hash TEXT NOT NULL, embedding TEXT NOT NULL,
                UNIQUE(user_id, key), UNIQUE(user_id, content_hash)
            );
            INSERT INTO memories VALUES ('legacy-id', 'alice', 'project', 'Uses Zephyr',
                'semantic', 'old-session', '2026-10-01T00:00:00Z',
                '2026-10-01T00:00:00Z', 'legacy-hash', '[1, 0]');
        """)
    for _ in range(2):
        store = MemoryStore(path, "fixture-vectors-v1")
        found = store.keyword_search("alice", "Zephyr", 4)
        assert len(found) == 1
        assert found[0].id == "legacy-id"
        assert found[0].source_session_id == "old-session"
        assert found[0].source_quote is None
        assert found[0].created_at.isoformat() == "2026-10-01T00:00:00+00:00"
        assert store.vectors("alice")[0][1] == [1, 0]


def test_source_quote_lifecycle_and_legacy_writers(memory):
    saved, _ = memory.save("alice", item(), "one", source_quote="I prefer Python.")
    reopened = MemoryStore(memory.store.path, "fixture-vectors-v1")
    assert reopened.get("alice", saved.id).source_quote == "I prefer Python."
    assert reopened.list("alice")[0].source_quote == "I prefer Python."
    assert reopened.vectors("alice")[0][0].source_quote == "I prefer Python."
    duplicate, action = memory.save("alice", item(), "two", source_quote="Python is my choice.")
    assert action == "unchanged"
    assert duplicate.source_quote == "I prefer Python."
    updated, _ = memory.save("alice", item("Prefers Java"), "two", source_quote="I prefer Java.")
    assert updated.source_quote == "I prefer Java."
    # Old application code updates the ten-column memories table directly.
    with reopened.connection() as db:
        db.execute("UPDATE memories SET content='Prefers Rust' WHERE id=?", (saved.id,))
    assert reopened.get("alice", saved.id).source_quote is None
    assert reopened.keyword_search("alice", "Rust", 4)[0].id == saved.id
    assert reopened.keyword_search("alice", "Java", 4) == []
    memory.save("alice", item("Prefers Go"), "three", source_quote="I prefer Go.")
    manual = memory.update("alice", saved.id, item("Prefers Ruby"))
    assert manual.source_quote is None
    assert manual.source_session_id is None
    memory.save("alice", item("Prefers C"), "four", source_quote="I prefer C.")
    memory.store.delete("alice", saved.id)
    with reopened.connection() as db:
        assert db.execute("SELECT count(*) FROM memory_evidence").fetchone()[0] == 0
