# Graph Report - presonal-ai-assistant  (2026-11-09)

## Corpus Check
- 32 files · ~22,422 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .lock 1)

## Summary
- 327 nodes · 739 edges · 16 communities (13 shown, 3 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 111 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d8b41659`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- agent.py
- ProviderError
- test_agent.py
- MemoryStore
- AGENT_RESEARCH_2026-11-09.md
- create_app
- test_memory.py
- Personal Assistant Memory Implementation Plan
- personal-assistant-memory
- evaluation.py
- Repository Guidelines
- Memory Reliability Implementation Plan
- Memory reliability milestone
- Memory architecture research

## God Nodes (most connected - your core abstractions)
1. `MemoryStore` - 35 edges
2. `create_app()` - 31 edges
3. `Assistant` - 28 edges
4. `Settings` - 24 edges
5. `MemoryInput` - 24 edges
6. `FakeProvider` - 24 edges
7. `item()` - 23 edges
8. `ProviderError` - 21 edges
9. `candidate()` - 21 edges
10. `Memory` - 16 edges

## Surprising Connections (you probably didn't know these)
- `1. Agno memory agent: observed source` --references--> `Memory`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/models.py
- `Coding Style & Naming Conventions` --references--> `Provider`  [INFERRED]
  AGENTS.md → src/personal_assistant/provider.py
- `Testing Guidelines` --references--> `FakeProvider`  [INFERRED]
  AGENTS.md → tests/fakes.py
- `GitHub follow-up: 2026-10-27` --references--> `main()`  [INFERRED]
  docs/MEMORY_RESEARCH.md → src/personal_assistant/evaluation.py
- `Executed checks` --references--> `ProviderError`  [INFERRED]
  docs/EVALUATION.md → src/personal_assistant/provider.py

## Import Cycles
- None detected.

## Communities (16 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.09
Nodes (15): Executed checks, extract(), forget_keys(), forget_target(), is_sensitive(), MemoryService, requests_no_storage(), validate_vector() (+7 more)

### Community 1 - "ProviderError"
Cohesion: 0.13
Nodes (15): ProviderError, api(), test_failed_answer_does_not_store_incomplete_turn(), unavailable(), test_scenario_c_forget_without_consent_or_available_model(), unavailable(), test_provider_failure_is_a_service_error(), unavailable() (+7 more)

### Community 2 - "test_agent.py"
Cohesion: 0.07
Nodes (23): candidate(), FakeProvider, assistant(), test_conflicting_candidates_in_one_extraction_are_not_applied(), test_consent_off_skips_extraction_but_allows_existing_recall(), test_essential_profile_survives_unrelated_query_restart_and_forgetting(), test_explicit_no_storage_overrides_automatic_consent(), test_forgetting_removes_shared_source_quote_from_surviving_profile() (+15 more)

### Community 3 - "MemoryStore"
Cohesion: 0.21
Nodes (4): Concrete gaps in our code, Task 2: Persistent memory and short-term state, Memory, MemoryStore

### Community 4 - "AGENT_RESEARCH_2026-11-09.md"
Cohesion: 0.06
Nodes (31): Architecture, Boundaries, Modules and models, Read flow, Selection and alternatives, Write flow, Complete the live evaluation, Deterministic scenarios A–E (+23 more)

### Community 5 - "create_app"
Cohesion: 0.09
Nodes (11): Storage and provenance, 3. Letta and LangGraph starters: observed source, Assistant, TurnState, create_app(), memories(), messages(), sessions() (+3 more)

### Community 6 - "test_memory.py"
Cohesion: 0.14
Nodes (24): item(), memory(), test_all_crud_operations_enforce_ownership(), test_changed_embedding_dimension_is_rejected(), test_clear_user_data_is_scoped(), test_conflicting_upsert_cannot_silently_retain_old_preference(), test_delete_removes_vector_and_all_user_history(), test_duplicate_does_not_create_new_record() (+16 more)

### Community 7 - "Personal Assistant Memory Implementation Plan"
Cohesion: 0.22
Nodes (8): Execution notes, Global Constraints, Personal Assistant Memory Implementation Plan, Review Focus, Task 1: Research and design, Task 3: Provider and agent lifecycle, Task 4: API and UI, Task 5: Evaluation and handoff

### Community 11 - "evaluation.py"
Cohesion: 0.11
Nodes (14): lifespan(), Settings, evaluate(), load_cases(), main(), MeasuredProvider, _run_case(), OllamaProvider (+6 more)

### Community 12 - "Repository Guidelines"
Cohesion: 0.25
Nodes (7): Build, Test, and Development Commands, Coding Style & Naming Conventions, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 13 - "Memory Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Execution notes, Global constraints, Memory Reliability Implementation Plan, Review focus, Task 1: Evidence and hybrid retrieval, Task 2: Essential profile and inspection, Task 3: Repeatable evaluation and explanation

### Community 14 - "Memory reliability milestone"
Cohesion: 0.40
Nodes (4): Approaches, Behavior and scope, Memory reliability milestone, Proof and limits

### Community 15 - "Memory architecture research"
Cohesion: 0.22
Nodes (9): 1. Agno memory agent: observed source, 2. Study coach: observed Memori + LangGraph source, 4. Mem0: official docs and actual implementation, Comparison and recommendation, Concepts, GitHub follow-up: 2026-10-27, Memory architecture research, Recommended order — proposed experiments, not implemented changes (+1 more)

## Knowledge Gaps
- **52 isolated node(s):** `personal-assistant-memory`, `Project Structure & Module Organization`, `Build, Test, and Development Commands`, `Commit & Pull Request Guidelines`, `Security & Configuration Tips` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 128 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `create_app` to `agent.py`, `ProviderError`, `test_agent.py`, `MemoryStore`, `evaluation.py`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `MemoryStore` (e.g. with `Assistant` and `MemoryService`) actually correct?**
  _`MemoryStore` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `personal-assistant-memory`, `Project Structure & Module Organization`, `Build, Test, and Development Commands` to the rest of the system?**
  _52 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08928571428571429 - nodes in this community are weakly interconnected._
- **Why does `MemoryStore` connect `MemoryStore` to `agent.py`, `evaluation.py`, `create_app`, `test_memory.py`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `lifespan()` and `ChatRequest`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `ProviderError` be split into smaller, more focused modules?**
  _Cohesion score 0.1282051282051282 - nodes in this community are weakly interconnected._