# Memory architecture research

Research performed 2026-10-22. Actual reference source was cloned and inspected at Awesome AI Apps commit [`e5065fd86b79fd48f52c0b3261b5256ae71f6eb6`](https://github.com/Arindam200/awesome-ai-apps/tree/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6). The examples were read, not executed against their external services. This document distinguishes observed application code from framework documentation and our design decisions.

## Concepts

**Short-term memory** is working context for one conversation: recent turns, current task state, perhaps a rolling summary. **Long-term memory** is selected durable information reusable across conversations. Persisting a transcript alone does not give an agent selective recall or a trustworthy user profile.

**Semantic memory** represents facts and preferences ("prefers Vietnamese explanations"). **Episodic memory** represents events with provenance/time ("studied decorators on Tuesday"). **Procedural memory** represents how to do something, such as a learned workflow. These cognitive categories differ from semantic *search*, which retrieves by meaning regardless of memory type. Our MVP focuses on semantic facts; the schema also labels explicitly added events/procedures without executing them.

**Conversation history** preserves dialogue order and speaker roles. **Persistent memory** distills useful assertions, tracks ownership and provenance, and supports correction/deletion. Summaries compress a dialogue but can lose evidence or perpetuate earlier mistakes. We select bounded complete turns rather than untested summarization.

Extraction may run during a turn (immediately visible but slower) or asynchronously (lower response latency but eventual consistency). A validated structured candidate should describe one current fact, use a stable topic key, and cite user-provided evidence. The LLM proposes; deterministic code controls ownership, consent, writes, and deletion. An evidence substring prevents wholly unsupported inserts, but is not a semantic truth verifier.

Embeddings map text to dense vectors. Cosine similarity ranks related meanings; it does not establish truth, ownership, freshness, or consent. Filter by user **before** ranking; apply thresholds and top-k limits. Record embedding identity, inspect actual retrieved records, and evaluate irrelevant as well as relevant queries.

Deduplication can use normalized exact content and stable fact keys; semantic merging risks combining unrelated facts. Conflicts require an explicit policy: newest direct assertion, confirmation, or temporal versions. Forgetting must cover vectors, records, chat histories, cached prompts, exports, and backups; deleting only one index entry is insufficient. Privacy controls need consent, data minimization, source separation, and access control. Evaluation must separate extraction accuracy, retrieval precision/recall, update/deletion correctness, isolation, and generated answer quality.

See [LangGraph's memory overview](https://docs.langchain.com/oss/python/langgraph/memory) for memory categories and write timing, and its [persistence guide](https://docs.langchain.com/oss/python/langgraph/persistence) for the distinction between thread checkpoints and cross-thread stores.

## 1. Agno memory agent: observed source

Sources: [`main.py`](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/memory_agents/agno_memory_agent/main.py), [`pyproject.toml`](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/memory_agents/agno_memory_agent/pyproject.toml).

- Stack: Agno v1-era `Memory`, Nebius DeepSeek chat, `SqliteMemoryDb` and separate `SqliteStorage` tables in `tmp/agent.db`.
- Extraction: configured memory model; `enable_agentic_memory` and `enable_user_memories` both enabled, delegating decisions to Agno.
- Retrieval/injection: framework-managed user memories plus `add_history_to_messages=True` and `num_history_runs=3`.
- Persistence/update/delete: SQLite tables and `user_id`; agentic updating enabled. The script also calls `memory.clear()` before demo turns, which defeats restart recall for this demo. No individual CRUD UI or isolation tests appear here.
- Strength: tiny application surface. Limit: behavior depends heavily on library version, and identity is hardcoded. Complexity is low for a demonstration, higher when adding inspectable governance.

Current [Agno documentation](https://docs.agno.com/memory/overview) uses `SqliteDb` and `update_memory_on_run`, unlike this older example. We do not assume the old imports work with a current unconstrained install or infer a vector index from SQLite alone.

## 2. Study coach: observed Memori + LangGraph source

Sources: [`memory_utils.py`](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/memory_agents/study_coach_agent/memory_utils.py), [`study_graph.py`](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/memory_agents/study_coach_agent/study_graph.py).

- Stack: Streamlit, OpenAI, Memori (a different product from Mem0), SQLAlchemy/CockroachDB, LangGraph.
- Extraction: a registered OpenAI client intercepts calls; helpers submit profile JSON and session-summary prompts.
- Persistence/retrieval: Memori attribution uses `entity_id`/`process_id`. A `STUDY_COACH_PROFILE` tag is searched and parsed; answering relies on registered-client integration. The app source does not expose the internals of Memori ranking or prompt injection.
- Updates/delete: profile writes and best-effort adapter commits are shown; explicit conflict resolution or individual forgetting is not implemented in these helpers.
- Strength: demonstrates structured profiles and episodic study summaries. Limits: external database/key requirements, swallowed commit failures, default shared identity, no visible lifecycle proof. LangGraph orchestrates quiz generation/evaluation rather than implementing memory storage.
- Complexity: medium/high for our local-only objective. We reuse explicit graph stages and structured profile ideas, not its infrastructure.

## 3. Letta and LangGraph starters: observed source

Sources: [Letta starter](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/starter_ai_agents/letta_starter/main.py), [LangGraph starter](https://github.com/Arindam200/awesome-ai-apps/blob/e5065fd86b79fd48f52c0b3261b5256ae71f6eb6/starter_ai_agents/langgraph_starter/main.py).

Letta's starter requires a server, reuses an agent by name, initializes `human`/`persona` blocks, and submits messages to the server. Memory extraction, persistence, context compilation, and editing are delegated to that server; the script does not demonstrate deletion or authenticated user isolation. It configures a chat and embedding model, but does not demonstrate archival retrieval itself. Agent reuse helps continuity; name-based global lookup is insufficient for per-user ownership. Complexity is medium because a server must also be operated. [Letta's stateful-agent documentation](https://docs.letta.com/v1-sdk/concepts/stateful-agents) explains framework-managed state; server durability still needs suitable deployment storage.

The LangGraph starter uses a ReAct agent with clock/word-count tools and an in-process `messages` list. It adds neither a persistent store nor checkpointer, and grows history without trimming. It is an orchestration example, not proof of cross-process memory. Our implementation uses `StateGraph` with explicit storage rather than copying this loop.

## 4. Mem0: official docs and actual implementation

No Mem0 example was found in the inspected reference tree; we researched it separately rather than attributing one to that repository. Sources: [OSS quickstart](https://docs.mem0.ai/open-source/python-quickstart), [add semantics](https://docs.mem0.ai/core-concepts/memory-operations/add), and [current Python source](https://github.com/mem0ai/mem0/blob/main/mem0/memory/main.py).

Mem0 provides extraction, embeddings, vector search, user scoping, and CRUD behind a compact API. OSS defaults in the inspected docs use OpenAI, on-disk Qdrant, and a separate SQLite history database. These are configurable; SQLite history is not the vector store. `infer=False` can store raw content and bypass extraction. The current documentation explicitly describes additive `add` behavior: do not assume it resolves contradictions automatically. Use deliberate update/delete operations and verify the installed version. Search must supply the correct user filter; an identifier is not authentication.

Strength: fast integration and provider choices. Limit: more hidden policy and multi-store deletion to understand; managed and OSS behavior can differ. Complexity is low for basic recall, medium for provable conflicts/privacy. Old tutorials may describe different add/update behavior.

## Comparison and recommendation

| Approach | Extraction / control | Persistence | Update/deletion burden | MVP fit |
|---|---|---|---|---|
| Agno | Framework memory manager and agent tools | SQLite supported | Inspect version/flags; add consent and CRUD | Very fast demo, less explicit experiment |
| Letta | Server-managed state and memory tools | Server storage | Agent/server lifecycle and per-user mapping | Useful advanced research, extra service |
| Mem0 | Library/managed extraction and vector retrieval | Configured vector backend + history | Explicit current-version update/delete policy | Good later comparative baseline |
| LangGraph + our SQLite service | Explicit schema extraction and validation nodes | One transaction domain | Stable keys, exact dedup, atomic delete, history invalidation | **Selected: observable and locally understandable** |

LangGraph supplies orchestration, not a ready-made memory policy. Its in-memory store is not durable, and checkpointers store thread state rather than a curated user profile. We intentionally implement a small application store rather than claiming it is LangGraph Store. SQLite cosine search replaces Chroma for small profiles; scale and retrieval benchmarks should decide when to introduce an indexed vector backend. The main tradeoff is that extraction/canonicalization quality is ours to evaluate, rather than delegated to a mature framework.

The full design is in [ARCHITECTURE.md](ARCHITECTURE.md). Research claims about source behavior are observations; expected MVP benefits are design judgments, not benchmark results.
