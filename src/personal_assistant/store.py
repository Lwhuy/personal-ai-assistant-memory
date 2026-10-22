"""One transactional SQLite database; histories and curated memories are separate."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from personal_assistant.models import Memory, MemoryInput


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


class MemoryStore:
    def __init__(self, path: str | Path, embedding_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        new_file = not self.path.exists()
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, key TEXT NOT NULL,
                    content TEXT NOT NULL, memory_type TEXT NOT NULL,
                    source_session_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL, embedding TEXT NOT NULL,
                    UNIQUE(user_id, key), UNIQUE(user_id, content_hash)
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT NOT NULL, session_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(user_id, session_id)
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
                    FOREIGN KEY(user_id, session_id) REFERENCES sessions(user_id, session_id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS messages_session ON messages(user_id, session_id, id);
            """)
            db.execute(
                "INSERT OR IGNORE INTO metadata VALUES ('embedding_model', ?)", (embedding_id,)
            )
            model = db.execute("SELECT value FROM metadata WHERE key='embedding_model'").fetchone()
            if model[0] != embedding_id:
                raise ValueError(
                    "Changed embedding model: use a new database or re-embed memories."
                )
        if new_file:
            self.path.chmod(0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA secure_delete=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _memory(row) -> Memory:
        return Memory.model_validate({k: row[k] for k in Memory.model_fields})

    def list(self, user_id: str) -> list[Memory]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM memories WHERE user_id=? ORDER BY created_at, id", (user_id,)
            ).fetchall()
        return [self._memory(row) for row in rows]

    def get(self, user_id: str, memory_id: str) -> Memory | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM memories WHERE user_id=? AND id=?", (user_id, memory_id)
            ).fetchone()
        return self._memory(row) if row else None

    def vectors(self, user_id: str) -> list[tuple[Memory, list[float]]]:
        with self.connection() as db:
            rows = db.execute("SELECT * FROM memories WHERE user_id=?", (user_id,)).fetchall()
        return [(self._memory(row), json.loads(row["embedding"])) for row in rows]

    @staticmethod
    def _dimension(db, vector):
        dimension = str(len(vector))
        db.execute("INSERT OR IGNORE INTO metadata VALUES ('embedding_dimension', ?)", (dimension,))
        actual = db.execute("SELECT value FROM metadata WHERE key='embedding_dimension'").fetchone()
        if actual[0] != dimension:
            raise ValueError("Embedding dimension changed; re-embed with a consistent model.")

    def upsert(
        self, user_id: str, item: MemoryInput, vector: list[float], source_session_id: str | None
    ) -> tuple[Memory, str]:
        digest = hashlib.sha256(normalized(item.content).encode()).hexdigest()
        now = datetime.now(UTC).isoformat()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._dimension(db, vector)
            existing = db.execute(
                "SELECT * FROM memories WHERE user_id=? AND key=?", (user_id, item.key)
            ).fetchone()
            duplicate = db.execute(
                "SELECT * FROM memories WHERE user_id=? AND content_hash=?", (user_id, digest)
            ).fetchone()
            if duplicate:
                if existing and duplicate["id"] != existing["id"]:
                    raise ValueError(
                        "Memory content already belongs to another key; edit that record first."
                    )
                return self._memory(duplicate), "unchanged"
            memory_id = existing["id"] if existing else str(uuid4())
            if existing:
                db.execute(
                    """UPDATE memories SET content=?, memory_type=?, source_session_id=?,
                       updated_at=?, content_hash=?, embedding=? WHERE user_id=? AND id=?""",
                    (
                        item.content,
                        item.memory_type,
                        source_session_id,
                        now,
                        digest,
                        json.dumps(vector),
                        user_id,
                        memory_id,
                    ),
                )
                db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
            else:
                db.execute(
                    "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        memory_id,
                        user_id,
                        item.key,
                        item.content,
                        item.memory_type,
                        source_session_id,
                        now,
                        now,
                        digest,
                        json.dumps(vector),
                    ),
                )
            row = db.execute(
                "SELECT * FROM memories WHERE user_id=? AND id=?", (user_id, memory_id)
            ).fetchone()
        return self._memory(row), "updated" if existing else "added"

    def update(
        self, user_id: str, memory_id: str, item: MemoryInput, vector: list[float]
    ) -> Memory | None:
        digest = hashlib.sha256(normalized(item.content).encode()).hexdigest()
        try:
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT * FROM memories WHERE user_id=? AND id=?", (user_id, memory_id)
                ).fetchone()
                if row is None:
                    return None
                self._dimension(db, vector)
                db.execute(
                    """UPDATE memories SET key=?, content=?, memory_type=?, embedding=?,
                       content_hash=?, updated_at=?, source_session_id=NULL
                       WHERE user_id=? AND id=?""",
                    (
                        item.key,
                        item.content,
                        item.memory_type,
                        json.dumps(vector),
                        digest,
                        datetime.now(UTC).isoformat(),
                        user_id,
                        memory_id,
                    ),
                )
                db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
                result = db.execute(
                    "SELECT * FROM memories WHERE user_id=? AND id=?", (user_id, memory_id)
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError("Another memory already has that key or content.") from exc
        return self._memory(result)

    def delete(self, user_id: str, memory_id: str) -> bool:
        with self.connection() as db:
            deleted = db.execute(
                "DELETE FROM memories WHERE user_id=? AND id=?", (user_id, memory_id)
            ).rowcount
            if deleted:
                db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        return bool(deleted)

    def forget_keys(self, user_id: str, keys: list[str]) -> int:
        with self.connection() as db:
            count = 0
            for key in keys:
                count += db.execute(
                    "DELETE FROM memories WHERE user_id=? AND key=?", (user_id, key)
                ).rowcount
            db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        return count

    def create_session(self, user_id: str, session_id: str | None = None) -> dict:
        session_id = session_id or str(uuid4())
        with self.connection() as db:
            db.execute(
                "INSERT OR IGNORE INTO sessions VALUES (?, ?, ?)",
                (user_id, session_id, datetime.now(UTC).isoformat()),
            )
            row = db.execute(
                "SELECT * FROM sessions WHERE user_id=? AND session_id=?", (user_id, session_id)
            ).fetchone()
        return dict(row)

    def list_sessions(self, user_id: str) -> list[dict]:
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,)
                )
            ]

    def history(self, user_id: str, session_id: str) -> list[dict[str, str]]:
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    """SELECT role, content FROM messages WHERE user_id=? AND session_id=?
                   ORDER BY id""",
                    (user_id, session_id),
                )
            ]

    def save_turn(
        self, user_id: str, session_id: str, message: str, answer: str, history_turns: int
    ):
        self.create_session(user_id, session_id)
        with self.connection() as db:
            db.executemany(
                "INSERT INTO messages(user_id, session_id, role, content) VALUES (?, ?, ?, ?)",
                [
                    (user_id, session_id, "user", message),
                    (user_id, session_id, "assistant", answer),
                ],
            )
            db.execute(
                """DELETE FROM messages WHERE user_id=? AND session_id=? AND id NOT IN (
                   SELECT id FROM messages WHERE user_id=? AND session_id=?
                   ORDER BY id DESC LIMIT ?)""",
                (user_id, session_id, user_id, session_id, 2 * history_turns),
            )

    def delete_session(self, user_id: str, session_id: str) -> bool:
        with self.connection() as db:
            return bool(
                db.execute(
                    "DELETE FROM sessions WHERE user_id=? AND session_id=?", (user_id, session_id)
                ).rowcount
            )

    def delete_user_data(self, user_id: str):
        with self.connection() as db:
            db.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
