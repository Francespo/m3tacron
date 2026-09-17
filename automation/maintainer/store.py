"""Durable SQLite state for maintainer tasks and audit events."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

TERMINAL_STATES = frozenset({"approved", "stopped", "failed"})
VALID_STATES = frozenset(
    {
        "draft",
        "running",
        "review",
        "changes_requested",
        "approved",
        "blocked",
        "stopped",
        "failed",
    }
)

ALLOWED_TRANSITIONS = {
    "draft": {"running", "stopped", "failed"},
    "running": {"review", "blocked", "stopped", "failed"},
    "review": {"changes_requested", "approved", "blocked", "stopped", "failed"},
    "changes_requested": {"running", "blocked", "stopped", "failed"},
    "blocked": {"running", "stopped", "failed"},
    "approved": set(),
    "stopped": set(),
    "failed": {"running"},
}


class StateError(ValueError):
    """Raised for invalid task state changes."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    request_id TEXT,
                    intent TEXT NOT NULL,
                    decisions_json TEXT NOT NULL DEFAULT '{}',
                    state TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    paseo_agent_id TEXT,
                    paseo_workspace_id TEXT,
                    pull_request_number INTEGER,
                    pull_request_url TEXT,
                    preview_url TEXT,
                    head_sha TEXT,
                    approved_sha TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS tasks_active_branch
                    ON tasks(branch) WHERE state NOT IN ('approved', 'stopped');
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                """
            )
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "request_id" not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN request_id TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS tasks_request_id "
                "ON tasks(project_id, request_id) WHERE request_id IS NOT NULL"
            )

    def create_task(
        self,
        project_id: str,
        intent: str,
        decisions: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        intent = intent.strip()
        if not intent:
            raise StateError("Expected outcome cannot be empty")
        request_id = request_id.strip() if request_id else None
        if request_id:
            with self.connect() as conn:
                existing = conn.execute(
                    "SELECT * FROM tasks WHERE project_id = ? AND request_id = ?",
                    (project_id, request_id),
                ).fetchone()
            if existing is not None:
                return self._decode(existing)
        task_id = uuid.uuid4().hex[:12]
        branch = f"agent/{task_id}"
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, project_id, request_id, intent, decisions_json, state, branch,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                """,
                (
                    task_id,
                    project_id,
                    request_id,
                    intent,
                    json.dumps(decisions or {}, ensure_ascii=False, sort_keys=True),
                    branch,
                    now,
                    now,
                ),
            )
            self._audit(conn, task_id, "task.created", {"project_id": project_id})
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise StateError(f"Unknown task: {task_id}")
        return self._decode(row)

    def list_tasks(self, project_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM tasks"
        params: tuple[Any, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._decode(row) for row in rows]

    def transition(
        self,
        task_id: str,
        state: str,
        *,
        event: str,
        payload: dict[str, Any] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        if state not in VALID_STATES:
            raise StateError(f"Invalid task state: {state}")
        with self.connect() as conn:
            row = conn.execute("SELECT state FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise StateError(f"Unknown task: {task_id}")
            current = row["state"]
            if not force and state != current and state not in ALLOWED_TRANSITIONS[current]:
                raise StateError(f"Invalid transition: {current} -> {state}")
            conn.execute(
                "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?",
                (state, utc_now(), task_id),
            )
            self._audit(conn, task_id, event, payload or {})
        return self.get_task(task_id)

    def update(self, task_id: str, **fields: Any) -> dict[str, Any]:
        allowed = {
            "paseo_agent_id",
            "paseo_workspace_id",
            "pull_request_number",
            "pull_request_url",
            "preview_url",
            "head_sha",
            "approved_sha",
            "last_error",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise StateError(f"Unsupported task fields: {', '.join(sorted(unknown))}")
        if not fields:
            return self.get_task(task_id)
        fields["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = [fields[key] for key in fields]
        with self.connect() as conn:
            cursor = conn.execute(
                f"UPDATE tasks SET {assignments} WHERE id = ?",
                (*values, task_id),
            )
            if cursor.rowcount != 1:
                raise StateError(f"Unknown task: {task_id}")
            self._audit(conn, task_id, "task.updated", {"fields": sorted(fields)})
        return self.get_task(task_id)

    def audit(
        self, task_id: str, event: str, payload: dict[str, Any] | None = None
    ) -> None:
        with self.connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if exists is None:
                raise StateError(f"Unknown task: {task_id}")
            self._audit(conn, task_id, event, payload or {})

    def audit_events(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT event, payload_json, created_at FROM audit_events "
                "WHERE task_id = ? ORDER BY id",
                (task_id,),
            ).fetchall()
        return [
            {
                "event": row["event"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    @staticmethod
    def _audit(
        conn: sqlite3.Connection,
        task_id: str,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            "INSERT INTO audit_events (task_id, event, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (task_id, event, json.dumps(payload, ensure_ascii=False, sort_keys=True), utc_now()),
        )

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["decisions"] = json.loads(result.pop("decisions_json"))
        return result
