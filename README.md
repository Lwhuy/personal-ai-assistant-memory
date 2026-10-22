# Personal AI Assistant — Memory Lab

A local research MVP for remembering selected user facts across conversations and restarts. The focus is **agent memory**: extraction, consent, persistence, semantic retrieval, correction, forgetting, isolation, and evaluation.

Python + FastAPI + LangGraph + Ollama + SQLite + Streamlit. SQLite stores structured memories and their embeddings together; cosine search avoids a second database for a small local profile. No cloud account or API key is required.

## Features and boundaries

- Multiple conversation sessions with bounded, persistent recent history.
- Opt-in extraction of useful facts/preferences/goals from the latest user message.
- Persistent memories with user ownership, keys, types, source session, and timestamps.
- Semantic retrieval with configurable threshold/top k and inspectable records/scores/events.
- View/add/edit/delete memory, exact deduplication, key-based updates, explicit forget commands.
- Separate local user namespaces, basic sensitivity checks, no-storage requests, and data deletion.
- Model-independent tests and a separate opt-in live Ollama evaluation.

**Local prototype:** selecting a user ID is impersonation, not authentication. Bind services to loopback and run one backend worker. Updating/deleting a memory clears that user's chat histories so stale facts cannot return through old context.

## Prerequisites and installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Ollama](https://ollama.com/download). The project selects Python 3.12; uv provisions it if needed. Project metadata supports Python 3.11–3.13.

From the repository root:

```bash
uv sync --locked
cp .env.example .env
```

Start the Ollama desktop app, or run this in another terminal:

```bash
ollama serve
```

If already serving, use that process. Pull the configured defaults:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
curl http://localhost:11434/api/tags
```

Allow disk/RAM for the selected models. The default chat model download is approximately 1.9 GB; review its license before broader use. [Model details](https://ollama.com/library/qwen2.5:3b).

Ollama is not required for default tests, listing/deleting memories, or supported forget commands. Chat, extraction, and new embeddings require it. The implementation environment had no Ollama executable/service, so **live response quality remains unverified**.

## Environment configuration

Environment variables override `.env`. `.env` and local data are ignored by Git; no secrets are hardcoded.

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Chat/embedding server; inputs are sent here. |
| `CHAT_MODEL` | `qwen2.5:3b` | Chat and structured extraction. |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Semantic embeddings. |
| `DATABASE_PATH` | `data/assistant.sqlite3` | Persistent memory/history file, relative to working directory. |
| `HISTORY_TURNS` | `6` | Retained complete turns, range 1–20. |
| `MEMORY_TOP_K` | `4` | Maximum retrieved records, range 1–10. |
| `MEMORY_MIN_SCORE` | `0.25` | Cosine cutoff; requires real-data calibration. |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Timeout per Ollama request, >0–600 seconds. |
| `BACKEND_URL` | `http://127.0.0.1:8000` | API URL used by Streamlit. |

Changing chat models is independent of memory. Changing embedding models requires a **new database path** or a reviewed re-embedding migration; mixed vector spaces are rejected. Do not delete existing data to resolve configuration errors. Mutable model tags do not pin weights: record model digests for reproducible research.

## Run the application

Backend:

```bash
uv run uvicorn personal_assistant.api:app --host 127.0.0.1 --port 8000 --no-access-log
```

Frontend, in another terminal at the same repository root:

```bash
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open `http://127.0.0.1:8501`; API docs are at `http://127.0.0.1:8000/docs`. `/health` indicates process health, not model readiness. Use one Uvicorn worker.

The backend command disables access logs so memory-search query strings and user IDs are not logged. Do not enable request-body or provider debug logging with private data.

Select a local user ID. Enable **Allow automatic memory saving** before providing facts to retain. Explicit memory-manager additions work without that checkbox. Normal short-term history is stored separately; a recognized sensitive input or "Don't remember this" excludes the current turn from storage, while still sending it to the model for a response.

For 503 errors, check the service/models/timeout. Writes precede response generation, so inspect saved memory before retrying. Malformed extraction can produce an answer with a warning and no successful memory event. Treat stored records/events as evidence, not an assistant's verbal claim to have remembered.

## Tests

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Tests use real SQLite, LangGraph, FastAPI, and Streamlit with a deterministic replacement for the external provider. They prove lifecycle behavior independently from model quality. The live model test is skipped by default.

After setting up Ollama:

```bash
RUN_OLLAMA_TESTS=1 uv run pytest -m ollama -v -s
```

This opt-in test exercises A–E with real extraction/embeddings and prints answers for inspection. Language/abstention assertions are basic heuristics; manually judge correctness. When explicitly enabled, unavailable models fail instead of skipping.

Run only the deterministic scenarios:

```bash
uv run pytest tests/test_agent.py -k scenario -v
```

Actual results, the full manual demo, limitations, and research questions are in [EVALUATION.md](docs/EVALUATION.md).

## Example conversations

With automatic saving enabled:

1. `alice`, conversation 1: "I am learning Python and I prefer explanations in Vietnamese."
2. Inspect `response_language` and `learning_goal`. Start a new conversation or restart the backend with the same database.
3. "Can you explain decorators?" Inspect the retrieved Vietnamese preference; the expected live answer is in Vietnamese.
4. "I used to prefer Python, but now I prefer Java." Inspect `programming_language_preference`; future recall should use Java.
5. "Forget my programming language preference." Its record/vector disappear and all Alice's chat histories clear. The distinct `learning_goal=Learning Python` may remain.
6. Alice: "My favorite editor is VS Code." Switch to `bob`: "What is my favorite editor?" No Alice memory should be retrieved.
7. "What is my favorite database?" Without such a fact, the expected answer admits it is unknown.

Forgetting supports a documented English vocabulary and exact existing keys; use the memory manager for other targets. "Forget all my memories" clears memory/history; **Delete all my data** also removes session records. **Delete this conversation** leaves cross-session memories intact.

## Project map and documentation

```text
src/personal_assistant/
  api.py          HTTP endpoints and application lifecycle
  agent.py        LangGraph write/read/respond/save workflow
  provider.py     Ollama chat, schema extraction, embeddings
  config.py       Environment settings
  models.py       Memory/extraction/chat schemas
  extraction.py   Evidence checks and explicit forget targets
  memory.py       Sensitivity checks and semantic retrieval
  store.py        SQLite CRUD, transactions, bounded histories
streamlit_app.py  Chat, sessions, memory editor, retrieval debugger
tests/            Independent lifecycle tests and opt-in live evaluation
docs/             Research, architecture, lifecycle, evaluation, plan
```

Read [research](docs/MEMORY_RESEARCH.md) → [architecture](docs/ARCHITECTURE.md) → [memory lifecycle](docs/MEMORY_LIFECYCLE.md) → [evaluation](docs/EVALUATION.md). These explain how the implementation works and why it was selected.

## Before production

Add authenticated principals and authorization, encryption/backup/retention policy, stronger consent/DLP, model-based extraction/retrieval/conflict benchmarks, prompt-injection testing, token-aware context budgets, cross-process coordination, and recovery/idempotency. Introduce an indexed vector backend when profile size/latency measurements justify it.

This MVP has no OpenAI provider, autonomous action tools, summarizer, automatic expiry, or semantic conflict merger. Counts/content lengths prevent unbounded application context, but a model can still truncate large prompts at its own context window. Prompt separation and regex filtering are limited defenses.
