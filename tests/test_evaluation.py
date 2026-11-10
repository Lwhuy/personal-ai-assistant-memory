import json

from personal_assistant.config import Settings
from personal_assistant.evaluation import evaluate, load_cases
from personal_assistant.models import MemoryInput
from personal_assistant.store import MemoryStore
from tests.fakes import FakeProvider, candidate


def language_case():
    return {
        "id": "language-test",
        "split": "test",
        "turns": [
            {
                "user_id": "alice",
                "session_id": "intro",
                "message": "I prefer Vietnamese.",
                "remember": True,
            }
        ],
        "query": {"user_id": "alice", "session_id": "next", "message": "How far is the Moon?"},
        "expected_memories": {"response_language": ["Vietnamese", "tiếng Việt"]},
        "expected_context": ["response_language"],
        "must_not_persist": [],
        "answer_rubric": "Give a correct explanation in Vietnamese.",
    }


def test_evaluation_compares_paired_contexts_without_touching_user_database(tmp_path):
    settings = Settings(_env_file=None, database_path=tmp_path / "existing.db")
    provider = FakeProvider()
    provider.extractions["I prefer Vietnamese."] = [
        candidate("response_language", "Prefers Vietnamese", "I prefer Vietnamese.")
    ]
    store = MemoryStore(settings.database_path, provider.embedding_id)
    store.upsert("real-user", MemoryInput(key="name", content="Keep me"), [1, 0, 0, 0], None)
    original = settings.database_path.read_bytes()
    report = evaluate(settings, provider, [language_case()])
    assert settings.database_path.read_bytes() == original
    assert len(report["results"]) == 2
    baseline, memory = report["results"]
    assert baseline["mode"] == "history_only"
    assert baseline["supplied_keys"] == []
    assert baseline["context_recall"] == 0
    assert baseline["final_fact_precision_heuristic"] is None
    assert memory["mode"] == "memory"
    assert memory["supplied_keys"] == ["response_language"]
    assert memory["context_recall"] == 1
    assert memory["final_fact_precision_heuristic"] == 1
    assert memory["final_fact_recall_heuristic"] == 1
    assert memory["answer_grade"] is None
    assert memory["lifecycle_pass"] is None
    assert memory["answer_rubric"] == "Give a correct explanation in Vietnamese."
    assert memory["query_seconds"] >= 0
    assert any(call["kind"] == "extraction" for call in memory["calls"])
    assert not any(call["kind"] == "extraction" for call in baseline["calls"])
    assert all(call["input_characters"] > 0 for call in memory["calls"])
    assert report["summary"]["memory"]["context_recall"] == 1
    assert report["summary"]["memory"]["lifecycle_pass"] is None
    assert "existing.db" not in json.dumps(report)


def test_evaluation_reports_incorrect_fact_values_and_unsupported_extractions(tmp_path):
    settings = Settings(_env_file=None, database_path=tmp_path / "unused.db")
    provider = FakeProvider()
    provider.extractions["I prefer Vietnamese."] = [
        candidate("response_language", "Prefers French", "I prefer Vietnamese."),
        candidate("database_preference", "Prefers SQLite", "I prefer SQLite."),
    ]
    report = evaluate(settings, provider, [language_case()])
    assert len(report["results"]) == 2
    memory = report["results"][1]
    assert memory["final_fact_precision_heuristic"] == 0
    assert memory["final_fact_recall_heuristic"] == 0
    assert memory["warnings"]
    assert memory["answer_grade"] is None


def test_evaluation_checks_privacy_and_forgetting_across_restarts(tmp_path):
    provider = FakeProvider()
    provider.extractions["I prefer Vietnamese."] = [
        candidate("response_language", "Prefers Vietnamese", "I prefer Vietnamese.")
    ]
    case = language_case()
    case["turns"].extend(
        [
            {
                "user_id": "alice",
                "session_id": "intro",
                "remember": True,
                "message": "Forget my response language.",
            },
            {
                "user_id": "alice",
                "session_id": "intro",
                "remember": True,
                "message": "Don't remember this: my favorite editor is Zephyr.",
            },
        ]
    )
    case["expected_memories"] = {}
    case["expected_context"] = []
    case["must_not_persist"] = ["I prefer Vietnamese.", "Zephyr"]
    report = evaluate(
        Settings(_env_file=None, database_path=tmp_path / "unused.db"), provider, [case]
    )
    assert len(report["results"]) == 2
    for result in report["results"]:
        assert result["lifecycle_pass"]
        assert result["supplied_keys"] == []
    assert report["results"][1]["memories"] == []


def test_corpus_has_separate_english_and_vietnamese_development_and_test_cases():
    cases = load_cases()
    assert len({case["id"] for case in cases}) == len(cases)
    assert {case["split"] for case in cases} == {"dev", "test"}
    assert {case["language"] for case in cases if case["split"] == "test"} == {"en", "vi"}
    assert all(case["answer_rubric"] for case in cases)
