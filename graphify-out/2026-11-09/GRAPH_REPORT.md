# Graph Report - presonal-ai-assistant  (2026-11-09)

## Corpus Check
- 32 files · ~21,886 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .lock 1)

## Summary
- 322 nodes · 725 edges · 15 communities (12 shown, 3 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 110 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d8b41659`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- agent.py
- test_provider.py
- test_agent.py
- MemoryStore
- Evaluation
- create_app
- test_memory.py
- Personal Assistant Memory Implementation Plan
- personal-assistant-memory
- evaluation.py
- Provider
- Review focus
- Memory reliability milestone

## God Nodes (most connected - your core abstractions)
1. `MemoryStore` - 35 edges
2. `create_app()` - 31 edges
3. `Assistant` - 27 edges
4. `Settings` - 24 edges
5. `MemoryInput` - 24 edges
6. `FakeProvider` - 23 edges
7. `ProviderError` - 21 edges
8. `item()` - 21 edges
9. `candidate()` - 20 edges
10. `Memory` - 16 edges

## Surprising Connections (you probably didn't know these)
- `1. Agno memory agent: observed source` --references--> `Memory`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/models.py
- `Testing Guidelines` --references--> `FakeProvider`  [INFERRED]
  AGENTS.md → tests/fakes.py
- `GitHub follow-up: 2026-10-27` --references--> `main()`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/evaluation.py
- `Executed checks` --references--> `ProviderError`  [INFERRED]
  docs/EVALUATION.md → src/personal_assistant/provider.py
- `Coding Style & Naming Conventions` --references--> `Provider`  [INFERRED]
  AGENTS.md → src/personal_assistant/provider.py

## Import Cycles
- None detected.

## Communities (15 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.09
Nodes (15): Assistant, TurnState, lifespan(), get_assistant(), Settings, extract(), forget_keys(), forget_target() (+7 more)

### Community 1 - "test_provider.py"
Cohesion: 0.22
Nodes (8): api(), provider_with(), test_invalid_provider_embeddings_raise_sanitized_error(), test_ollama_chat_and_schema_contract(), handler(), test_ollama_embedding_contract(), test_provider_connection_failure(), test_provider_errors_are_actionable_and_redacted()

### Community 2 - "test_agent.py"
Cohesion: 0.07
Nodes (27): evaluate(), candidate(), FakeProvider, assistant(), test_conflicting_candidates_in_one_extraction_are_not_applied(), test_consent_off_skips_extraction_but_allows_existing_recall(), test_essential_profile_survives_unrelated_query_restart_and_forgetting(), test_explicit_no_storage_overrides_automatic_consent() (+19 more)

### Community 3 - "MemoryStore"
Cohesion: 0.12
Nodes (11): Concrete gaps in our code, Task 2: Persistent memory and short-term state, is_sensitive(), MemoryService, validate_vector(), Candidate, Memory, MemoryInput (+3 more)

### Community 4 - "Evaluation"
Cohesion: 0.06
Nodes (32): Architecture, Boundaries, Modules and models, Read flow, Selection and alternatives, Write flow, Complete the live evaluation, Deterministic scenarios A–E (+24 more)

### Community 5 - "create_app"
Cohesion: 0.07
Nodes (15): Storage and provenance, 1. Agno memory agent: observed source, 2. Study coach: observed Memori + LangGraph source, 3. Letta and LangGraph starters: observed source, 4. Mem0: official docs and actual implementation, Comparison and recommendation, Concepts, GitHub follow-up: 2026-10-27 (+7 more)

### Community 6 - "test_memory.py"
Cohesion: 0.17
Nodes (21): item(), test_all_crud_operations_enforce_ownership(), test_changed_embedding_dimension_is_rejected(), test_clear_user_data_is_scoped(), test_conflicting_upsert_cannot_silently_retain_old_preference(), test_delete_removes_vector_and_all_user_history(), test_duplicate_does_not_create_new_record(), test_embedding_model_change_is_explicit() (+13 more)

### Community 7 - "Personal Assistant Memory Implementation Plan"
Cohesion: 0.22
Nodes (8): Execution notes, Global Constraints, Personal Assistant Memory Implementation Plan, Review Focus, Task 1: Research and design, Task 3: Provider and agent lifecycle, Task 4: API and UI, Task 5: Evaluation and handoff

### Community 11 - "evaluation.py"
Cohesion: 0.12
Nodes (11): load_cases(), main(), OllamaProvider, ProviderError, test_failed_answer_does_not_store_incomplete_turn(), unavailable(), test_scenario_c_forget_without_consent_or_available_model(), unavailable() (+3 more)

### Community 12 - "Provider"
Cohesion: 0.12
Nodes (10): Build, Test, and Development Commands, Coding Style & Naming Conventions, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines, MeasuredProvider (+2 more)

### Community 13 - "Review focus"
Cohesion: 0.29
Nodes (6): Global constraints, Memory Reliability Implementation Plan, Review focus, Task 1: Evidence and hybrid retrieval, Task 2: Essential profile and inspection, Task 3: Repeatable evaluation and explanation

### Community 14 - "Memory reliability milestone"
Cohesion: 0.40
Nodes (4): Approaches, Behavior and scope, Memory reliability milestone, Proof and limits

## Knowledge Gaps
- **51 isolated node(s):** `personal-assistant-memory`, `Project Structure & Module Organization`, `Build, Test, and Development Commands`, `Commit & Pull Request Guidelines`, `Security & Configuration Tips` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 127 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `create_app` to `agent.py`, `test_agent.py`, `MemoryStore`, `evaluation.py`, `Provider`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `MemoryStore` (e.g. with `Assistant` and `MemoryService`) actually correct?**
  _`MemoryStore` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `personal-assistant-memory`, `Project Structure & Module Organization`, `Build, Test, and Development Commands` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08979591836734693 - nodes in this community are weakly interconnected._
- **Why does `MemoryStore` connect `MemoryStore` to `agent.py`, `test_agent.py`, `test_memory.py`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `lifespan()` and `ChatRequest`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07184325108853411 - nodes in this community are weakly interconnected._