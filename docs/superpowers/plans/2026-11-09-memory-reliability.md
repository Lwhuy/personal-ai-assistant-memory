# Memory Reliability Implementation Plan

> **For agentic workers:** Execute inline with superpowers:executing-plans and test-driven development.

**Goal:** Make essential preference recall reliable, improve exact-term retrieval, retain evidence,
and provide a reproducible local evaluation.

**Architecture:** Extend the existing SQLite store, memory service and LangGraph nodes. Additive
API fields expose profile, evidence and ranking without changing existing request bodies.

**Tech Stack:** Python 3.12, SQLite FTS5, Pydantic, LangGraph, existing Ollama provider and pytest.

**Spec:** `docs/superpowers/specs/2026-11-09-memory-reliability-design.md`

## Global constraints

- No new dependencies, embedding changes, deleted databases or modifications to pre-existing edits.
- Preserve consent, user scoping, deterministic forgetting and current-assertion precedence.
- Build in the existing feature branch; leave changes reviewable, without an automatic push.

## Review focus

- Legacy writes must not retain stale evidence or leave a stale keyword index.
- Keyword syntax, punctuation and Vietnamese input must be safe.
- Profile must not leak between users or survive forgetting.
- Evidence must survive restart but be removed by manual edits and deletion.
- Evaluation must use temporary data and distinguish canned responses from model quality.

### Task 1: Evidence and hybrid retrieval

**Files:** models.py, store.py, memory.py, agent.py; tests/test_memory.py, test_agent.py, test_api.py.
**Interfaces:** `Memory.source_quote: str | None`; `RetrievedMemory.retrieval_method` and
`rank_score`; optional keyword-only `source_quote` on save/upsert;
`MemoryStore.keyword_search(user_id, query, limit) -> list[Memory]`.

- [x] Add failing tests for evidence lifecycle, legacy backfill, lexical rescue, index sync,
  escaping and ownership; run to observe missing behavior.
- [x] Add side tables/triggers and source joins; save accepted quotes; fuse keyword and cosine
  ranks at constant 60. Keep cosine `score` unchanged.
- [x] Run memory/API/agent tests and the full deterministic suite.

### Task 2: Essential profile and inspection

**Files:** models.py, agent.py, streamlit_app.py; tests/test_agent.py, test_api.py, test_ui.py.
**Interfaces:** `ChatResult.profile_memories: list[Memory]`; only response_language is essential.

- [x] Write failing tests for unrelated-query recall, isolation, deduplication and forgetting.
- [x] Load profile in retrieval node and deduplicate model context by ID. Show profile and quote
  in existing inspection controls; rename semantic search to keyword/vector search.
- [x] Run the full suite.

### Task 3: Repeatable evaluation and explanation

**Files:** evaluation.py, eval_cases.json; tests/test_evaluation.py; README.md,
docs/EVALUATION.md, docs/MEMORY_LIFECYCLE.md, docs/ARCHITECTURE.md.
**Interfaces:** `evaluate(settings, provider, cases) -> dict`; opt-in module CLI writing JSON.

- [x] Write failing runner tests for paired arms, lifecycle scoring and isolated temporary data.
- [x] Implement fixed split corpus, paired runs, measured provider calls, fact/context metrics,
  latency summaries and human answer rubrics. Record model configuration/digests in live CLI.
- [x] Run suite, lint and format checks; attempt live execution, document actual results.
- [x] Review the full change, refresh graphify, and explain usage and remaining limitations.

## Execution notes

- Baseline: 62 passed, 1 skipped. Final suite: 82 passed, 1 skipped; lint/format/build pass.
- Live evaluation attempted; Ollama unreachable. No model quality or benchmark gains claimed.
- Independent review: shared evidence could leak forgotten facts; decomposed Vietnamese queries
  missed keywords. Both fixed with RED→GREEN regressions and a green full suite.
- Implementation choice: corrections/deletion clear all same-user evidence quotes, matching the
  existing coarse history policy. Cost: unrelated quote provenance is lost; facts remain saved.
- Worked inline on the existing feature branch and left changes uncommitted; no worktree or
  branch integration required. Pre-existing AGENTS.md and MEMORY_RESEARCH.md edits preserved.
