# Evaluation

## Memory reliability update — 2026-11-09

The update adds an always-supplied response-language profile, keyword/vector rank fusion,
retained supporting quotes, and an opt-in paired evaluation. Verified in this workspace:

| Check | Result |
|---|---|
| `uv run pytest -q` | **82 passed, 1 skipped**; external provider replaced, real store/workflow/API/UI |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed |
| `uv build` | Passed; the wheel includes the evaluation runner and JSON corpus. |
| Paired live evaluation CLI | **Blocked**: Ollama unreachable; exited with an actionable error. No live scores generated. |

New regressions cover exact-name retrieval with orthogonal query vectors, unique hybrid hits,
FTS syntax escaping/Vietnamese input, all index deletion paths, legacy database backfill,
evidence persistence/invalidation, old-writer compatibility, unrelated-question profile recall,
deduplication and current-message placement, API attribution controls, UI quote/profile inspection,
and isolated paired evaluation. The evaluator test verifies byte-for-byte preservation of an
existing configured database; it never opens that path during evaluation.

Independent review found two issues, both reproduced with failing tests before correction:
shared source quotes could retain a forgotten fact in another memory, and decomposed Vietnamese
queries lost combining marks during tokenization. Mutations now invalidate all that user's quotes
before saving any replacement evidence; queries normalize to NFC. Tests cover surviving profile
prompts, CRUD, same-key upserts, legacy SQL mutations, and preservation of another user's evidence.

### Run the paired corpus

Start Ollama and download the configured chat/embedding models, then:

```bash
uv run python -m personal_assistant.evaluation --split dev --output data/memory-dev.json
uv run python -m personal_assistant.evaluation --split test --output data/memory-test.json
```

`src/personal_assistant/eval_cases.json` contains 14 synthetic cases: 2 development and 12 test.
Use development cases for prompt/threshold changes and leave the test split fixed for comparison.
The corpus covers English/Vietnamese preference recall, unrelated questions, current-turn overrides,
correction, exact names, cross-language recall, unknown facts, user isolation, forgetting, privacy,
consent off, same-session history and misleading quotations. This is a small project-specific corpus,
not LoCoMo/LongMemEval or a statistically representative quality estimate.

Each case runs twice, history-only first and memory-enabled second. Models, system prompt, message
sequence, history bounds and generation settings match. The baseline disables extraction writes;
the memory arm respects each turn's consent. Each arm gets a fresh temporary database; an application
object restart before the query checks persistence. The configured personal database is untouched.
Most cases query a new session, so the history-only baseline cannot access the earlier conversation.
The same-session control gives it a question it should answer from bounded history.

Reports record model configuration, model digests, corpus SHA-256, per-case answers, supplied records,
warnings, generation/extraction/embedding call timings and character counts. No prompt bodies are
logged by the instrumentation; replay inputs and answers are synthetic report data. Review answers
against each `answer_rubric` and fill `answer_grade` manually. Its initial null value means ungraded.

| Metric | Interpretation and limit |
|---|---|
| `context_recall` | Fraction of expected keys supplied through profile/search; null for cases with no expected keys. Does not prove the right value or answer was used. |
| `final_fact_precision_heuristic` | Fraction of final stored facts matching an expected key and one labeled value substring; memory arm only. Wrong values/extra facts lower it. No facts with none expected scores one. |
| `final_fact_recall_heuristic` | Fraction of expected final facts matched by key/value substring; memory arm only. These final-state metrics do not measure per-extraction precision/recall or entailment. |
| `lifecycle_pass` | Forbidden synthetic substrings absent from current memories/quotes and all replayed users' bounded histories after the query; null when no assertion is specified. Not forensic erasure or output-leakage grading. |
| Query p50/p95 | Median and nearest-rank 95th-percentile wall time. Samples are few, history-only runs first, model warm-up/cache/order effects are uncontrolled. |
| Provider calls/input characters | Recorded across seeding and querying; includes embedding input and chat message bodies. Excludes schema/role overhead and is **not** a token or cost estimate. |

Summary quality-related metrics are macro averages over applicable cases. Review the per-case
records: empty-state cases can make final-fact averages look good despite failed positive recall.
No automated answer correctness, abstention, stale-answer rate or injection-resistance score is
claimed. The fake-provider tests prove runner mechanics, not learned model behavior. When Ollama
is unavailable, the command exits nonzero without replacing a completed report with fake scores.

## Original MVP evaluation — 2026-10-22

Recorded on 2026-10-22, macOS ARM64, Python 3.12.15. The reference implementations were inspected, not executed. Results below distinguish deterministic lifecycle proof, actual process startup, and live model quality.

## Executed checks

| Check | Result | Meaning |
|---|---|---|
| `uv sync --locked` | Passed, 77 packages resolved / 73 installed environment packages checked | Locked dependency installation compatible with this environment. |
| `uv run pytest -q` | **62 passed, 1 skipped** | Independent lifecycle/API/UI tests pass; live Ollama evaluation is skipped by default. |
| `uv run ruff check .` | Passed | Static checks, including imports and common Python errors. |
| `uv run ruff format --check .` | Passed | Formatting check. |
| `uv build` | Passed | Source distribution and wheel built. |
| Real Uvicorn subprocesses + HTTP requests | Passed | Startup, namespace isolation, restart persistence across two distinct server processes, deletion, missing-model 503. Synthetic memory/vector seeded without a model. |
| Real Streamlit process + HTTP health/HTML | Passed | Frontend server starts and serves locally. Interactive UI logic is separately covered by Streamlit AppTest against the real API with an external-provider fake. |
| `RUN_OLLAMA_TESTS=1 uv run pytest -m ollama -q --tb=short` | **Blocked: 1 failed, 62 deselected** | `test_live_scenarios_a_through_e` fails with connection refused / actionable `ProviderError`; no Ollama executable/service/models were available. No live quality result is claimed. |
| `graphify update .` | Passed | Ancestor repository instruction: AST-only project graph refreshed, no LLM calls. |

Resolved versions include LangGraph 1.2.16, FastAPI 0.159.1, Streamlit 1.66.1, Pydantic 2.14.1, pydantic-settings 2.16.1, HTTPX 0.28.1, pytest 9.1.1, and Uvicorn 0.54.0. `uv.lock` is the exact machine-readable set. Other Python versions/platforms were not tested.

## Deterministic scenarios A–E

`tests/test_agent.py` uses the real workflow, memory service, and temporary on-disk SQLite. Only the external chat/extraction/embedder boundary is replaced. Hand-chosen orthogonal vectors exercise ranking and isolation; they do not measure natural-language semantic similarity. Canned extraction output exercises validation and storage, not extraction quality. Answer construction tests inspect what the real application injects into the model.

| Scenario | Automated proof | Result / limit |
|---|---|---|
| A: persistent preference | Save Vietnamese preference/learning goal, construct a fresh assistant on the same database, start another session, retrieve and inspect the injected preference | Passed. Vietnamese generated explanation requires live-model/manual grading. |
| B: changed preference | Replace Python with Java at the same key/ID; remove old histories; check later retrieval | Passed. Canonical-key extraction quality remains model-dependent. |
| C: forget | Delete programming preference before any LLM call, clear history, reopen database, verify missing record/vector | Passed, including disabled saving/unavailable model. |
| D: isolation | Same session string for Alice/Bob; verify no Alice memory or conversation data in Bob's prompt | Passed. This is namespace isolation, not authenticated access control. |
| E: unknown | Unknown database question creates no record, retrieves no database fact, and receives a fixed instruction to admit unknown information | Passed. Deterministic answer fixtures cannot prove real model abstention. |

Additional tests cover exact duplicates, same-key upserts, cross-key collision rollback, explicit CRUD ownership, history pruning, finite/nonzero embedding vectors, dimension/model changes, extraction schema/evidence failures, repeated conflicting keys, consent off, privacy requests, sensitive input/output retention, untrusted memory placement, sanitized provider failures, and failed-answer history exclusion. API tests use FastAPI TestClient; UI tests use Streamlit AppTest. New-conversation selection, submitting into the new session, memory addition, and draft clearing on user switch are tested.

Independent review reproduced two issues that were fixed with failing-then-passing regression tests: silent duplicate-content collisions suppressing an update, and a new-session button retaining the old selection. Cross-key collisions now fail visibly; the UI selects the newly created session.

## Complete the live evaluation

Install/start Ollama, then from the project root:

```bash
ollama serve
```

Use the running desktop service instead if already active. In another terminal:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
curl http://localhost:11434/api/tags
RUN_OLLAMA_TESTS=1 uv run pytest -m ollama -v -s
```

The opt-in test uses its own temporary database, real extraction, and real embeddings. It checks storage transitions, Vietnamese characters in A, absence of Alice's editor in Bob's answer, and basic English abstention wording in E. These are coarse heuristics: inspect printed answers for actual correctness. A good answer can fail a wording heuristic; a weak answer can pass one. The live benchmark is not represented as complete until executed successfully and reviewed.

## Manual demonstration

Start backend/frontend using README commands. Use synthetic identities/data and keep the same `DATABASE_PATH` during the restart test. Enable **Allow automatic memory saving** for statements to retain. Inspect the per-turn retrieval/events and the memory-manager records rather than trusting verbal saving claims.

1. **A — cross-session recall:** choose `alice`; say "I am learning Python and I prefer explanations in Vietnamese." Verify separate `learning_goal` and `response_language` records. Start a new conversation; ask "Can you explain decorators?" Confirm a relevant preference is retrieved and the explanation is correct and in Vietnamese. Stop/restart the backend with the same database and repeat in another conversation. Record the retrieved IDs and response language.
2. **B — update:** first say "I prefer Python as my programming language" and verify `programming_language_preference`. Say "I used to prefer Python, but now I prefer Java." Verify the same ID now describes Java, no second current programming-preference record exists, and old chat histories cleared. In another session ask for the current preference. A learning goal about Python may remain and must not be treated as the current preference.
3. **C — forget:** say "Forget my programming language preference." Verify `deleted` events, absent record, and cleared histories. Search for the preference and restart; the deleted ID must not return. The answer should not infer a current preference from a remaining learning goal. The deterministic command also works with Ollama stopped.
4. **D — isolation:** Alice says "My favorite editor is VS Code." Switch to `bob`; saving defaults off for a new local user. Ask "What is my favorite editor?" Confirm empty Bob memory/relevant-history context and an unknown-information response. Switch back to Alice and check that her record remains.
5. **E — abstention:** on a user who never supplied a database preference, ask "What is my favorite database?" Confirm no new database record appears and the model admits uncertainty without selecting a database.
6. **CRUD/privacy:** explicitly add a record, edit it while retaining ID, delete it, and verify searches/history. Try "Don't remember this: I prefer Java"; neither that turn nor its extracted fact should persist. Delete all user data and confirm memory/session records are gone; the UI may immediately create a fresh empty session for chatting.

Record model tag **and digest**, configuration, example inputs, memory IDs/keys, retrieved scores, generated answers, and pass/fail reasons. Avoid real personal information in the report.

## Success criteria and limitations

The implemented deterministic guarantees are restart-safe storage, bounded context, explicit user scoping, exact deduplication, key-based updates, controllable deletion, privacy gates, and observable context construction. Real-model multilingual recall, extraction accuracy, response correctness, abstention, and injection resistance have **not been measured** here.

Known failure cases:

- A valid supporting substring does not prove the content follows from it; false extraction is possible.
- Different keys can encode the same topic and retain contradictions. Identical content for a different existing slot is an explicit collision, not automatically merged.
- Cosine similarity can retrieve irrelevant facts or miss preferences; the update guarantees context availability only for `response_language` and adds lexical rescue. Threshold/top k/fusion and multilingual quality remain unmeasured.
- Fact correction/deletion clears every history for that user. This is intentionally coarse and sacrifices conversational continuity.
- Input/output sensitivity and English privacy/forget phrases use limited heuristics. Unrecognized forget targets delete nothing; use CRUD.
- Turning saving off does not disable recall or ordinary history retention. Provider-side retention and backups are outside local deletion.
- A failed answer can follow a committed memory write. Multiple extraction candidates are separate transactions.
- One process serializes requests. Multiple workers/direct database writers, production authentication, encryption, automatic expiry, temporal history, and permanent do-not-remember tombstones are not implemented.
- Message counts and lengths bound growth, not exact tokens; model-side context truncation can still occur.
- A stored injection is kept outside the system role but can still manipulate a weak model; there are no action tools to execute it.

## Next experiments and mentor preparation

Build a small labeled multi-session corpus with paraphrases, contradictions, questions, negation, unrelated facts, multilingual queries, and privacy attacks. Report extraction precision/recall, canonical-key consistency, retrieval precision@k/recall@k, answer correctness/abstention, stale-memory rate, deletion leakage, isolation failures, and p50/p95 latency. Use separate development/test sets; compare no-memory, bounded-history-only, our explicit store, and a version-pinned Mem0/Agno baseline under equal models and budgets. No such benchmark scores are invented in this MVP.

Study these concepts to explain the system confidently:

- Working context vs persistent user memory; semantic/episodic/procedural categories.
- RAG retrieves evidence; memory additionally selects, updates, reconciles, and forgets information over time.
- Embedding spaces, cosine similarity, threshold calibration, hybrid retrieval, reranking, and retrieval failure analysis.
- Structured extraction, provenance, canonical fact slots, entailment vs substring validation, and temporal conflicts.
- LangGraph state/nodes/edges vs checkpointers vs stores; why an in-memory store is not durable.
- ACID transactions, idempotency, multi-step failure recovery, and index/database consistency.
- Consent, minimization, tenant authorization, memory prompt injection, deletion scope, and backups.
- Evaluation leakage, deterministic component testing vs probabilistic model evaluation, and human grading rubrics.
