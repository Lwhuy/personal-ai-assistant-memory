# Graph Report - presonal-ai-assistant  (2026-10-22)

## Corpus Check
- 24 files · ~11,417 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .lock 1)

## Summary
- 252 nodes · 548 edges · 11 communities (8 shown, 3 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 76 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- agent.py
- ProviderError
- test_agent.py
- MemoryStore
- Personal AI Assistant — Memory Lab
- create_app
- test_memory.py
- Personal Assistant Memory Implementation Plan
- personal-assistant-memory

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 31 edges
2. `MemoryStore` - 30 edges
3. `Assistant` - 24 edges
4. `MemoryInput` - 22 edges
5. `ProviderError` - 18 edges
6. `Settings` - 17 edges
7. `FakeProvider` - 16 edges
8. `item()` - 16 edges
9. `MemoryService` - 13 edges
10. `Memory` - 13 edges

## Surprising Connections (you probably didn't know these)
- `1. Agno memory agent: observed source` --references--> `Memory`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/models.py
- `Storage and provenance` --references--> `sessions()`  [INFERRED]
  docs/MEMORY_LIFECYCLE.md → src/personal_assistant/api.py
- `Storage and provenance` --references--> `messages()`  [INFERRED]
  docs/MEMORY_LIFECYCLE.md → src/personal_assistant/api.py
- `3. Letta and LangGraph starters: observed source` --references--> `messages()`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/api.py
- `Storage and provenance` --references--> `memories()`  [INFERRED]
  docs/MEMORY_LIFECYCLE.md → src/personal_assistant/api.py

## Import Cycles
- None detected.

## Communities (11 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.09
Nodes (14): Assistant, TurnState, get_assistant(), extract(), forget_keys(), forget_target(), is_sensitive(), requests_no_storage() (+6 more)

### Community 1 - "ProviderError"
Cohesion: 0.08
Nodes (16): lifespan(), Settings, OllamaProvider, ProviderError, api(), test_provider_failure_is_a_service_error(), unavailable(), test_live_scenarios_a_through_e() (+8 more)

### Community 2 - "test_agent.py"
Cohesion: 0.07
Nodes (22): candidate(), FakeProvider, assistant(), test_conflicting_candidates_in_one_extraction_are_not_applied(), test_consent_off_skips_extraction_but_allows_existing_recall(), test_explicit_no_storage_overrides_automatic_consent(), test_failed_answer_does_not_store_incomplete_turn(), unavailable() (+14 more)

### Community 3 - "MemoryStore"
Cohesion: 0.14
Nodes (9): Task 2: Persistent memory and short-term state, MemoryService, validate_vector(), Candidate, Memory, MemoryInput, RetrievedMemory, MemoryStore (+1 more)

### Community 4 - "Personal AI Assistant — Memory Lab"
Cohesion: 0.06
Nodes (28): Architecture, Boundaries, Modules and models, Read flow, Selection and alternatives, Write flow, Deduplication and updates, Extraction and consent (+20 more)

### Community 5 - "create_app"
Cohesion: 0.11
Nodes (6): Storage and provenance, 3. Letta and LangGraph starters: observed source, create_app(), memories(), messages(), sessions()

### Community 6 - "test_memory.py"
Cohesion: 0.24
Nodes (15): item(), test_all_crud_operations_enforce_ownership(), test_changed_embedding_dimension_is_rejected(), test_clear_user_data_is_scoped(), test_conflicting_upsert_cannot_silently_retain_old_preference(), test_delete_removes_vector_and_all_user_history(), test_duplicate_does_not_create_new_record(), test_embedding_model_change_is_explicit() (+7 more)

### Community 7 - "Personal Assistant Memory Implementation Plan"
Cohesion: 0.22
Nodes (8): Execution notes, Global Constraints, Personal Assistant Memory Implementation Plan, Review Focus, Task 1: Research and design, Task 3: Provider and agent lifecycle, Task 4: API and UI, Task 5: Evaluation and handoff

## Knowledge Gaps
- **31 isolated node(s):** `personal-assistant-memory`, `Features and boundaries`, `Prerequisites and installation`, `Environment configuration`, `Run the application` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 97 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `create_app` to `agent.py`, `ProviderError`, `test_agent.py`, `MemoryStore`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `lifespan()` and `ChatRequest`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `personal-assistant-memory`, `Features and boundaries`, `Prerequisites and installation` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09178743961352658 - nodes in this community are weakly interconnected._
- **Why does `Memory` connect `MemoryStore` to `agent.py`, `Personal AI Assistant — Memory Lab`, `create_app`?**
  _High betweenness centrality (0.164) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `MemoryStore` (e.g. with `Assistant` and `MemoryService`) actually correct?**
  _`MemoryStore` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `ProviderError` be split into smaller, more focused modules?**
  _Cohesion score 0.08181818181818182 - nodes in this community are weakly interconnected._