# Memory reliability milestone

The user approved the research recommendation: improve personal memory before action tools.
Keep LangGraph, Ollama, SQLite, the Provider interface, and the existing consent/forget rules.

## Approaches

- Replace the memory backend: more dependencies and an unnecessary data migration.
- Tune cosine similarity alone: cannot guarantee essential preference recall or exact-name recall.
- Extend the current store: selected approach; small profile, keyword/vector fusion, and evidence.

## Behavior and scope

- Always supply the current user's `response_language` memory as untrusted profile data,
  separately observable from top-k search. Deduplicate it in the model context. Current user
  instructions still override it. Do not load all preferences into every prompt.
- Search combines SQLite FTS5 keywords and thresholded cosine results using reciprocal rank
  fusion (constant 60), with the existing top-k bound. Scores retain their cosine meaning;
  expose retrieval method and fusion score separately. Keywords never become SQL/FTS syntax.
- Preserve each accepted extraction's supporting quote with its memory. Manual edits clear
  attribution. Unchanged duplicates retain original attribution. No retroactive invented quotes.
  Corrections and deletion invalidate all same-user quotes to prevent overlapping full-message
  evidence from retaining forgotten facts. Surviving facts and other users' quotes are preserved.
- Use additive evidence/FTS tables and transactional triggers, backfill the search index once,
  and preserve IDs, timestamps, vectors, histories, ownership and model compatibility checks.
  Old writers remain compatible; their memory updates invalidate evidence. Rollback to old
  code may leave unused added tables but requires no data deletion or embedding change.
- Add a fixed synthetic English/Vietnamese development/test corpus and opt-in evaluation CLI.
  Run both history-only and enhanced-memory arms with identical models and user messages in
  temporary databases. Report final fact correctness, expected context recall, lifecycle checks,
  latency, model digests and call/input-character counts. Save answers and grading rubrics for
  human review; no automatic claim of answer quality, token savings or benchmark superiority.
- Show profile and source quotes in existing UI inspection. Add no framework or dependency.

## Proof and limits

Tests cover unrelated-topic preference recall, current-turn precedence in context, deduplication,
ownership, deletion/restart, keyword misses rescued below the cosine threshold, FTS escaping,
updates/deletion index consistency, legacy database backfill and evidence invalidation. Exercise
the evaluation runner with a fake provider, then attempt live evaluation if Ollama is reachable.

Quotes establish provenance, not entailment. FTS is lexical, not translation. Existing bounded
history, limited privacy heuristics, serialized requests and local-only deployment limits remain.
No contextual extraction, summaries, temporal versions, action tools or model changes in this slice.
