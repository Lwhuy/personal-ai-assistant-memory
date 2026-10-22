# Personal Assistant Memory Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task. The user explicitly requested continuous implementation, tests, and documentation.

**Goal:** A locally runnable assistant whose consent-based memory survives sessions and restarts and can be inspected, corrected, and forgotten.

**Architecture:** FastAPI calls a small LangGraph workflow; SQLite owns separate bounded session histories and structured user memories, including embedding vectors. Ollama performs structured extraction, embeddings, and chat; deterministic test doubles replace only that external boundary.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, SQLite/stdlib cosine search, HTTPX, Ollama, Streamlit, pytest; exact dependencies in `uv.lock`.

**Spec:** The user's detailed requirements and `docs/ARCHITECTURE.md`.

## Global Constraints

- Keep chat history separate from persistent memory; never extract assistant claims.
- Default automatic memory writes off; explicit memory management is consent.
- Filter every database operation by user; identity selection is local impersonation, not authentication.
- No API keys, message bodies, or model error payloads in logs.
- No model required for the default test suite; live model evaluation must be reported separately.
- Work in this initially empty checkout on `codex/memory-mvp`; a linked worktree cannot be based on an unborn HEAD. No push or publish.

## Review Focus

- Deleted or superseded memories must not survive in old session histories.
- Failed extraction or embedding must not delete a valid previous memory.
- Prompt injection and sensitive data must not gain instruction authority or automatic persistence.
- Reused session and memory IDs must never expose another user's records.
- Invalid vectors, changed embedding models, and malformed structured output must fail visibly.

## Task 1: Research and design

Files: `docs/MEMORY_RESEARCH.md`, `docs/ARCHITECTURE.md`, this plan.

- [x] Inspect the empty repository and applicable ancestor instructions.
- [x] Inspect actual Agno, study coach/Memori/LangGraph, Letta, and LangGraph starter sources at reference commit `e5065fd86b79fd48f52c0b3261b5256ae71f6eb6`; compare with official docs.
- [x] Select explicit SQLite memory instead of adding Mem0/Chroma or claiming an in-memory LangGraph Store is durable.
- [x] Record interfaces, privacy boundaries, and tradeoffs in the design.

## Task 2: Persistent memory and short-term state

Files: `src/personal_assistant/{models,store,memory}.py`, `tests/test_memory.py`.

Interfaces: `MemoryStore(path, embedding_id)`, `MemoryService(store, provider, top_k, min_score)`; user-scoped `list`, `save`, `update`, `delete`, `search`; bounded `save_turn` and `history`.

- [x] Write and run failing tests for persistence across reopening, semantic ranking, duplicate upsert, current preference replacement, CRUD isolation, invalid vectors, history pruning, and deletion removing stale history.
- [x] Implement SQLite tables, transactions, structured models, embedding validation, consent/sensitivity checks, and cosine ranking.
- [x] Run `uv run pytest tests/test_memory.py -q` to green.

## Task 3: Provider and agent lifecycle

Files: `src/personal_assistant/{config,provider,extraction,agent}.py`, `tests/{fakes,test_agent,test_provider}.py`.

Interfaces: provider `chat(messages, schema=None)` and `embed(text)`; `Assistant.chat(user_id, session_id, message, remember=False)` returns answer, retrieved records, lifecycle events, warnings.

- [x] Write and run failing tests for scenarios A–E, consent, unsupported forget requests, malformed/unsubstantiated extraction, provider errors, injection placement, and sensitive message retention.
- [x] Implement schema-based extraction of latest user assertions, grounded candidate validation, deterministic explicit forgetting, and graph nodes for memory write, retrieval, response, and bounded history.
- [x] Run memory, agent, and provider tests to green.

## Task 4: API and UI

Files: `src/personal_assistant/api.py`, `streamlit_app.py`, `tests/{test_api,test_ui}.py`.

Interfaces: `create_app(settings=None, provider=None)`; `/users/{user_id}/sessions`, `/chat`, `/users/{user_id}/memories`, individual CRUD, search, and user-data deletion.

- [x] Write and run failing API tests for chat, session continuity, validation, CRUD ownership, deletion, and sanitized unavailable-provider errors.
- [x] Implement API routes, local-only identity notice, opt-in memory controls, session selector, memory editor, retrieval debugger, and clear-data controls.
- [x] Run complete default suite and a Streamlit AppTest.

## Task 5: Evaluation and handoff

Files: `README.md`, `docs/{MEMORY_LIFECYCLE,EVALUATION}.md`, `tests/test_ollama.py`, `uv.lock`.

- [x] Document exact setup, configuration, demo A–E, data lifecycle, failure semantics, limitations, and mentor study topics.
- [x] Run `uv sync --locked`, `uv run pytest -q`, `uv run ruff check .`, build/import and HTTP startup checks; record actual outcomes.
- [x] Attempt optional Ollama evaluation if service/models exist; otherwise record precise setup commands and unverified quality.
- [x] Review the complete implementation against acceptance criteria; fix relevant failures and stop.

## Execution notes

- Research: Ollama executable and service are absent in the initial environment. No live model result is assumed.
- Ruling: User authorized selecting and implementing the stack without an approval pause. Work in the supplied empty workspace on a feature branch.
- Ruling: Use one transactional SQLite store rather than two synchronized databases. Linear vector search is appropriate for a small local profile and makes forgetting provable.
- Ruling: On any changed/deleted memory, clear that user's bounded histories across sessions. This sacrifices conversational continuity to prevent stale or deleted facts returning through chat context.
- Ruling: Default tests prove lifecycle behavior and prompt construction, not real model quality; an opt-in live test measures the latter separately.
- Independent review: fixed cross-key content dedup silently retaining a stale preference, and new-session creation failing to select the created session. Both have regression tests that failed before the fix and passed after it.
- Final independent checks: 62 passed / 1 skipped; lint/format, locked sync, distribution build, real server startup, HTTP isolation/deletion, and restart persistence passed. Explicit live evaluation attempted: connection refused, 1 environment-dependent failure; exact model setup and rerun commands recorded in `docs/EVALUATION.md`.
- Runtime skip: no model downloads or unrelated production infrastructure. No commit, push, deployment, or merge requested or performed.
