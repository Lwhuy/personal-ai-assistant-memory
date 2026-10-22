# Memory lifecycle

## Extraction and consent

Automatic saving defaults off (`remember=false`; unchecked UI control). Opting in allows at most five facts from the **latest user message only**. Extraction never reads assistant answers or old transcripts, preventing those sources from creating or recreating a fact.

Ollama receives a fixed extraction prompt and a Pydantic JSON schema. Candidates have a stable key, concise content, memory type, and supporting quote. The prompt distinguishes current preferences from past values and learning goals: learning Python does not mean preferring Python.

Validation rejects malformed JSON, extra fields, oversized candidates, unsupported quotes, quotes containing question marks, and repeated keys within one extraction. A normalized quote must occur in the latest user message. This is evidence, **not a semantic entailment proof**; incorrect summarization/canonicalization remains possible and requires real-model evaluation.

Sensitive input and English privacy phrases such as "don't remember this", "do not save", or "off the record" override automatic consent and skip both extraction and retention of that turn. Sensitive generated answers are also not retained. Explicit CRUD checks both key and content for sensitive information. The heuristic covers common credential/medical labels, card-like numbers, and some Vietnamese terms; it can miss obfuscation or reject benign text. It is not comprehensive DLP. The current input still goes to the configured model for its response.

Disabling automatic saving stops new automatic writes, not retrieval of existing memories or ordinary session-history storage. Explicit add/edit is consent for that operation. Use deletion to remove existing records.

## Storage and provenance

`memories` stores UUID, user ID, canonical key, content, type, optional source session ID, UTC creation/update times, content hash, and embedding JSON in the same row. Supporting quotes are validated but not persisted as a second copy of personal data. Explicit edits clear prior source-session attribution.

`metadata` records embedding model identity and vector dimension. A changed model/dimension fails visibly; choose a new database or implement a re-embedding migration. A mutable Ollama tag does not pin model weights: record digests during experiments.

`sessions` and `messages` are separate from curated memory. Only successful complete turns are retained, with older turns removed beyond `HISTORY_TURNS`. Sensitive/private turns are excluded. There are no durable graph checkpoints, prompt archives, or application content logs. Restarting uses the same SQLite path and retains the remaining records and bounded histories.

Connections close after each operation. Parameterized SQL and user predicates protect query boundaries. New database files use owner-only permissions on this platform. SQLite `secure_delete` is enabled, but backups, filesystem snapshots, SSD behavior, and external-provider retention prevent any claim of forensic erasure. Storage is not encrypted.

## Semantic retrieval and context

1. Select vectors with `WHERE user_id=?` before ranking; an empty profile avoids an embedding call.
2. Embed the question using the configured model. Validate finite numeric, nonempty, nonzero vectors, reject booleans, normalize, and check dimensions.
3. Compute cosine similarity, filter by `MEMORY_MIN_SCORE`, and return at most `MEMORY_TOP_K` records.
4. Add JSON memory data as a separate **user-context message**, following a fixed system instruction. Include only bounded history and the current user message.
5. Return the exact injected records/scores, lifecycle events, and warnings for inspection.

In a live run this uses dense embeddings, not keyword matching. The fake vectors in tests verify ranking mechanics, not embedding quality. Linear search costs O(n × d) per user's profile. Scores measure similarity, not truth/confidence. The default threshold is uncalibrated; multilingual retrieval needs measurement.

The system prompt tells the model to treat memory as untrusted data, prioritize current direct assertions, honor relevant preferences, and admit unknown personal information. A procedural memory is descriptive, never executable. Prompt separation reduces authority but does not guarantee injection resistance. The MVP has no external action tools.

`retrieved_memories` means **supplied to the model**, not proof of causal use. `memory_events` describes `added`, `updated`, `unchanged`, or `deleted` operations. Traces are response data, not a retained audit copy; the UI does not cache them across reruns.

## Deduplication and updates

Case folding and whitespace collapsing produce an exact-content SHA-256 hash. For a new key, an identical existing fact returns the old row without duplication. A changed value for the same `(user_id, key)` replaces content/vector, preserves ID/creation time, and advances the update timestamp. The newest accepted direct assertion wins.

If an existing slot's proposed new content belongs to another record, saving fails explicitly rather than reporting success and silently keeping the stale fact. Explicit PUT similarly rejects conflicting key/content collisions and rolls back. Resolve those cases through the memory manager. Different semantic keys are not automatically merged; wrong canonicalization can still leave contradictions.

Whenever an existing memory is updated or deleted, **all that user's chat messages are cleared**, keeping session IDs. This coarse policy prevents old facts from returning through conversation context. New insertions and unchanged duplicates leave histories intact. Semantic near-duplicate clustering, temporal versions, confidence fusion, and automatic expiry are outside the MVP.

## Forgetting

Deletion requires both memory ID and user ID. The vector disappears in the same transaction as the memory record and that user's messages. There is no second vector index to leave stale.

Explicit forgetting is handled deterministically before any model call, even with saving disabled or Ollama unavailable. Supported commands include:

- `Forget my programming language preference.`
- `Forget my editor preference.`
- `Forget my database preference.`
- `Forget my response language.`
- `Forget my learning goal.`
- `Forget my name.`
- `Forget <exact_existing_key>.`
- `Forget all my memories.`

Unrecognized/ambiguous targets delete nothing and direct the user to CRUD. A recognized target clears history even without a matching memory, covering facts held only in short-term context. Forget requests themselves are not stored. Forget-all removes curated memory and messages; **Delete all my data** additionally removes sessions. **Delete this conversation** leaves cross-session memory intact.

After forgetting a programming preference, `learning_goal=Learning Python` may remain: that is a different fact. The prompt must not infer a preference from it. A new explicit statement can save a forgotten fact again when consent is enabled; there are no permanent suppression tombstones.

## Failure and concurrency

Invalid extraction skips writes and exposes a warning. Candidates commit individually, so a later failure can leave earlier candidates saved; inspect events and CRUD. Failed embedding before an upsert preserves the previous record. Retrieval/chat failures return an actionable error rather than a fabricated response; incomplete turns are not retained.

Memory writes precede response generation. Therefore a 503 or interrupted graph can leave a successful memory write without a completed answer. Inspect records before retrying; same-content writes are idempotent. The graph is not a distributed transaction.

Chat and API CRUD share a process lock to prevent a concurrent turn from restoring just-cleared history. Run **one backend worker**. Other processes writing the same file are unsupported until cross-process lifecycle coordination is implemented.

## Identity and privacy boundary

User IDs demonstrate namespace isolation, not authentication. Any caller who reaches this API can select another ID intentionally. Bind both services to loopback and use synthetic training data. Production requires authenticated principals, per-operation authorization, encryption, backup/retention policy, stronger DLP/consent, abuse controls, and concurrent tenant-isolation tests.

UI form drafts clear when switching local users. Already displayed browser output, screenshots, exports, backups, and configured remote model servers are outside application deletion control. No application logger intentionally records conversation content. The documented server command disables access logs so search-query strings and user IDs are not recorded; avoid body/provider debug logging as well.
