"""Opt-in paired evaluation; synthetic inputs and temporary databases only."""

import argparse
import hashlib
import json
import math
import platform
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from statistics import mean, median
from tempfile import TemporaryDirectory
from time import perf_counter

import httpx

from personal_assistant.agent import Assistant
from personal_assistant.config import Settings
from personal_assistant.provider import OllamaProvider, Provider, ProviderError
from personal_assistant.store import normalized


def load_cases() -> list[dict]:
    return json.loads(files("personal_assistant").joinpath("eval_cases.json").read_text("utf-8"))


class MeasuredProvider:
    """Measure the external boundary without changing prompts or estimating tokens."""

    def __init__(self, provider: Provider):
        self.provider = provider
        self.embedding_id = provider.embedding_id
        self.calls: list[dict] = []

    def chat(self, messages: list[dict[str, str]], *, schema: dict | None = None) -> str:
        started = perf_counter()
        answer = self.provider.chat(messages, schema=schema)
        self.calls.append(
            {
                "kind": "extraction" if schema is not None else "generation",
                "seconds": perf_counter() - started,
                "input_characters": sum(len(message["content"]) for message in messages),
                "output_characters": len(answer),
            }
        )
        return answer

    def embed(self, text: str) -> list[float]:
        started = perf_counter()
        vector = self.provider.embed(text)
        self.calls.append(
            {
                "kind": "embedding",
                "seconds": perf_counter() - started,
                "input_characters": len(text),
                "output_characters": 0,
            }
        )
        return vector


def _run_case(settings: Settings, provider: Provider, case: dict, mode: str) -> dict:
    measured = MeasuredProvider(provider)
    with TemporaryDirectory(prefix="assistant-eval-") as directory:
        local = settings.model_copy(update={"database_path": Path(directory) / "memory.db"})
        assistant = Assistant(local, measured)
        started = perf_counter()
        warnings = []
        for turn in case["turns"]:
            result = assistant.chat(
                turn["user_id"],
                turn["session_id"],
                turn["message"],
                remember=mode == "memory" and turn["remember"],
            )
            warnings.extend(result.warnings)
        seed_seconds = perf_counter() - started
        # Restart the application object while retaining only its temporary SQLite state.
        assistant = Assistant(local, measured)
        started = perf_counter()
        result = assistant.chat(**case["query"])
        query_seconds = perf_counter() - started
        warnings.extend(result.warnings)
        memories = assistant.store.list(case["query"]["user_id"])
        supplied = sorted(
            {m.key for m in result.profile_memories}
            | {hit.memory.key for hit in result.retrieved_memories}
        )
        expected = case["expected_memories"]
        correct = sum(
            any(normalized(value) in normalized(memory.content) for value in expected[memory.key])
            for memory in memories
            if memory.key in expected
        )
        expected_context = set(case["expected_context"])
        # Include every replayed user's data, not just the query user's namespace.
        users = {turn["user_id"] for turn in case["turns"]} | {case["query"]["user_id"]}
        persisted = []
        for user in users:
            persisted.extend(m.model_dump(mode="json") for m in assistant.store.list(user))
            for session in assistant.store.list_sessions(user):
                persisted.extend(assistant.store.history(user, session["session_id"]))
        serialized = normalized(json.dumps(persisted, ensure_ascii=False))
        return {
            "case_id": case["id"],
            "split": case["split"],
            "mode": mode,
            "query": case["query"],
            "answer": result.answer,
            "answer_rubric": case["answer_rubric"],
            "answer_grade": None,
            "memories": [m.model_dump(mode="json") for m in memories],
            "expected_memories": expected,
            "supplied_keys": supplied,
            "expected_context": sorted(expected_context),
            "context_recall": (
                len(expected_context.intersection(supplied)) / len(expected_context)
                if expected_context
                else None
            ),
            "final_fact_precision_heuristic": (
                correct / len(memories) if memories else float(not expected)
            )
            if mode == "memory"
            else None,
            "final_fact_recall_heuristic": (correct / len(expected) if expected else 1.0)
            if mode == "memory"
            else None,
            "lifecycle_pass": not any(
                normalized(text) in serialized for text in case["must_not_persist"]
            )
            if case["must_not_persist"]
            else None,
            "profile_memories": [m.model_dump(mode="json") for m in result.profile_memories],
            "retrieved_memories": [
                hit.model_dump(mode="json") for hit in result.retrieved_memories
            ],
            "warnings": warnings,
            "seed_seconds": seed_seconds,
            "query_seconds": query_seconds,
            "calls": measured.calls,
        }


def evaluate(settings: Settings, provider: Provider, cases: list[dict]) -> dict:
    results = [
        _run_case(settings, provider, case, mode)
        for case in cases
        for mode in ("history_only", "memory")
    ]
    summary = {}
    for mode in ("history_only", "memory"):
        rows = [row for row in results if row["mode"] == mode]
        if not rows:
            continue
        latency = sorted(row["query_seconds"] for row in rows)
        metrics = {}
        for name in (
            "context_recall",
            "final_fact_precision_heuristic",
            "final_fact_recall_heuristic",
            "lifecycle_pass",
        ):
            values = [row[name] for row in rows if row[name] is not None]
            metrics[name] = mean(values) if values else None
        summary[mode] = {
            "cases": len(rows),
            **metrics,
            "query_p50_seconds": median(latency),
            "query_p95_seconds": latency[math.ceil(0.95 * len(latency)) - 1],
            "seed_seconds": sum(row["seed_seconds"] for row in rows),
            "provider_calls": sum(len(row["calls"]) for row in rows),
            "input_characters": sum(
                call["input_characters"] for row in rows for call in row["calls"]
            ),
        }
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "python_version": platform.python_version(),
        "configuration": settings.model_dump(mode="json", exclude={"database_path", "backend_url"}),
        "embedding_id": provider.embedding_id,
        "limitations": (
            "Synthetic corpus; final fact values use substring heuristics. Context recall measures "
            "supplied keys, not correct answers. answer_grade is pending human review. "
            "Character counts are not tokens. Latencies include warm-up/order effects; "
            "history_only always runs first. No quality claim follows from fake-provider runs."
        ),
        "summary": summary,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "test", "all"), default="test")
    parser.add_argument("--output", type=Path, default=Path("data/memory-evaluation.json"))
    args = parser.parse_args()
    settings = Settings()
    provider = OllamaProvider(settings)
    try:
        response = provider.client.get("/api/tags")
        response.raise_for_status()
        models = response.json()["models"]
        digests = {}
        for configured in (settings.chat_model, settings.embedding_model):
            name = configured if ":" in configured else configured + ":latest"
            digests[configured] = next(model["digest"] for model in models if model["name"] == name)
        cases = [
            case for case in load_cases() if args.split == "all" or case["split"] == args.split
        ]
        report = evaluate(settings, provider, cases)
        report["model_digests"] = digests
        report["corpus_sha256"] = hashlib.sha256(
            files("personal_assistant").joinpath("eval_cases.json").read_bytes()
        ).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf-8")
        print(json.dumps(report["summary"], indent=2))
        print(f"Saved {args.output}; answer grades require human review.")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, StopIteration, ProviderError) as exc:
        raise SystemExit(
            "Evaluation failed: start Ollama and check the configured models."
        ) from exc
    finally:
        provider.close()


if __name__ == "__main__":
    main()
