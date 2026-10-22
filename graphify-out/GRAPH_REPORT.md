# Graph Report - presonal-ai-assistant  (2026-10-22)

## Corpus Check
- 25 files · ~13,082 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .lock 1)

## Summary
- 260 nodes · 558 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- agent.py
- test_provider.py
- test_agent.py
- MemoryStore
- Personal AI Assistant — Memory Lab
- create_app
- test_memory.py
- Personal Assistant Memory Implementation Plan
- personal-assistant-memory
- ProviderError
- test_ollama.py

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 31 edges
2. `MemoryStore` - 30 edges
3. `Assistant` - 24 edges
4. `MemoryInput` - 22 edges
5. `ProviderError` - 19 edges
6. `Settings` - 17 edges
7. `FakeProvider` - 16 edges
8. `item()` - 16 edges
9. `MemoryService` - 13 edges
10. `Memory` - 13 edges

## Surprising Connections (you probably didn't know these)
- `1. Agno memory agent: observed source` --references--> `Memory`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/models.py
- `Executed checks` --references--> `ProviderError`  [INFERRED]
  docs/EVALUATION.md → src/personal_assistant/provider.py
- `Storage and provenance` --references--> `sessions()`  [INFERRED]
  docs/MEMORY_LIFECYCLE.md → src/personal_assistant/api.py
- `Storage and provenance` --references--> `messages()`  [INFERRED]
  docs/MEMORY_LIFECYCLE.md → src/personal_assistant/api.py
- `3. Letta and LangGraph starters: observed source` --references--> `messages()`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/api.py

## Import Cycles
- None detected.

## Communities (13 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.09
Nodes (13): Assistant, TurnState, get_assistant(), extract(), forget_keys(), forget_target(), Candidate, ChatRequest (+5 more)

### Community 1 - "test_provider.py"
Cohesion: 0.22
Nodes (8): api(), provider_with(), test_invalid_provider_embeddings_raise_sanitized_error(), test_ollama_chat_and_schema_contract(), handler(), test_ollama_embedding_contract(), test_provider_connection_failure(), test_provider_errors_are_actionable_and_redacted()

### Community 2 - "test_agent.py"
Cohesion: 0.07
Nodes (19): candidate(), FakeProvider, assistant(), test_conflicting_candidates_in_one_extraction_are_not_applied(), test_consent_off_skips_extraction_but_allows_existing_recall(), test_explicit_no_storage_overrides_automatic_consent(), test_history_is_bounded_and_included(), test_malformed_extraction_skips_writing_and_returns_warning() (+11 more)

### Community 3 - "MemoryStore"
Cohesion: 0.13
Nodes (9): Task 2: Persistent memory and short-term state, is_sensitive(), MemoryService, validate_vector(), Memory, MemoryInput, RetrievedMemory, MemoryStore (+1 more)

### Community 4 - "Personal AI Assistant — Memory Lab"
Cohesion: 0.08
Nodes (21): Architecture, Boundaries, Modules and models, Read flow, Selection and alternatives, Write flow, 1. Agno memory agent: observed source, 2. Study coach: observed Memori + LangGraph source (+13 more)

### Community 5 - "create_app"
Cohesion: 0.08
Nodes (13): Deduplication and updates, Extraction and consent, Failure and concurrency, Forgetting, Identity and privacy boundary, Memory lifecycle, Semantic retrieval and context, Storage and provenance (+5 more)

### Community 6 - "test_memory.py"
Cohesion: 0.24
Nodes (15): item(), test_all_crud_operations_enforce_ownership(), test_changed_embedding_dimension_is_rejected(), test_clear_user_data_is_scoped(), test_conflicting_upsert_cannot_silently_retain_old_preference(), test_delete_removes_vector_and_all_user_history(), test_duplicate_does_not_create_new_record(), test_embedding_model_change_is_explicit() (+7 more)

### Community 7 - "Personal Assistant Memory Implementation Plan"
Cohesion: 0.22
Nodes (8): Execution notes, Global Constraints, Personal Assistant Memory Implementation Plan, Review Focus, Task 1: Research and design, Task 3: Provider and agent lifecycle, Task 4: API and UI, Task 5: Evaluation and handoff

### Community 11 - "ProviderError"
Cohesion: 0.19
Nodes (10): lifespan(), Settings, OllamaProvider, ProviderError, test_failed_answer_does_not_store_incomplete_turn(), unavailable(), test_scenario_c_forget_without_consent_or_available_model(), unavailable() (+2 more)

### Community 12 - "test_ollama.py"
Cohesion: 0.17
Nodes (9): Complete the live evaluation, Deterministic scenarios A–E, Evaluation, Executed checks, Manual demonstration, Next experiments and mentor preparation, Success criteria and limitations, requests_no_storage() (+1 more)

## Knowledge Gaps
- **36 isolated node(s):** `personal-assistant-memory`, `Features and boundaries`, `Prerequisites and installation`, `Environment configuration`, `Run the application` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 102 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `create_app` to `agent.py`, `MemoryStore`, `test_agent.py`, `ProviderError`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `lifespan()` and `ChatRequest`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `personal-assistant-memory`, `Features and boundaries`, `Prerequisites and installation` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08888888888888889 - nodes in this community are weakly interconnected._
- **Why does `MemoryStore` connect `MemoryStore` to `agent.py`, `test_memory.py`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `MemoryStore` (e.g. with `Assistant` and `MemoryService`) actually correct?**
  _`MemoryStore` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06560283687943262 - nodes in this community are weakly interconnected._