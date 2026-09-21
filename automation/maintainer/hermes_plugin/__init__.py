"""Hermes plugin exposing the maintainer controller as structured tools.

The plugin runs inside Hermes processes (CLI, TUI, gateway). It shells out to
the controller CLI with argument arrays only — the model never receives a
generic terminal for maintainer work.

It also owns completion wake-ups. A detached Pi worker records its outcome in the
controller's SQLite outbox; the notifier thread started here posts that outcome to
the local Hermes webhook route, which turns it into a real agent turn delivered to
the conversation. Nothing polls the model, and a wake-up is acknowledged only after
the gateway accepts it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY_ROOT = Path("/root/projects/m3tacron")

REPOSITORY = Path(os.environ.get("MAINTAINER_REPOSITORY", DEFAULT_REPOSITORY_ROOT))
STATE = Path(os.environ.get("MAINTAINER_STATE", "~/.local/state/software-maintainer/state.db")).expanduser()
WORKTREE_ROOT = Path(
    os.environ.get("MAINTAINER_WORKTREE_ROOT", "~/.local/state/software-maintainer/worktrees")
).expanduser()

# Cadence of the completion poll. This runs on a daemon thread inside Hermes, costs no
# model tokens, and only reads a local SQLite file.
NOTIFIER_INTERVAL_SECONDS = 5.0
WEBHOOK_ROUTE = "maintainer-completion"
WEBHOOK_PROFILE = "coding"
WEBHOOK_TIMEOUT_SECONDS = 20.0
_notifier_lock = threading.Lock()
_notifier_thread: threading.Thread | None = None


def _check_available() -> bool:
    return (REPOSITORY / "scripts" / "maintainer").exists()


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home())
    except Exception:
        configured = os.environ.get("HERMES_HOME")
        return Path(configured).expanduser() if configured else Path("~/.hermes").expanduser()


def _str(description: str) -> dict[str, Any]:
    return {"type": "string", "description": description}


def _schema(name: str, description: str, properties: dict[str, Any], required=None) -> dict[str, Any]:
    parameters: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        parameters["required"] = required
    parameters["additionalProperties"] = False
    return {"name": name, "description": description, "parameters": parameters}


def _invoke(command: str, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = ["--state", str(STATE), command]
    for key, value in arguments.items():
        if value is None or value is False:
            continue
        flag = f"--{key.replace('_', '-')}"
        if value is True:
            payload.append(flag)
        elif isinstance(value, list):
            for item in value:
                payload.extend([flag, str(item)])
        else:
            payload.extend([flag, str(value)])
    process = subprocess.run(
        ["scripts/maintainer", *payload],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "MAINTAINER_WORKTREE_ROOT": str(WORKTREE_ROOT)},
    )
    stdout = process.stdout.strip()
    try:
        parsed = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        parsed = {"raw": stdout}
    if isinstance(parsed, list):
        parsed = {"items": parsed}
    if process.returncode:
        detail = process.stderr.strip() or stdout
        return {"ok": False, "error": detail, "exit_code": process.returncode, **parsed}
    return {"ok": True, **parsed}


# ── Routing: which Hermes session owns a tool call ──────────────────────────


def resolve_session_key(session_id: str | None) -> str | None:
    """Hermes session id -> gateway routing key, read from the profile session store.

    Tool handlers receive the agent's internal session id, not the routing key. The
    gateway persists both on every turn, which is the only reliable mapping.
    """
    if not session_id:
        return None
    database = _hermes_home() / "state.db"
    if not database.exists():
        return None
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5)
        try:
            row = connection.execute(
                "SELECT session_key FROM sessions WHERE id = ?", (str(session_id),)
            ).fetchone()
        finally:
            connection.close()
    except Exception:
        return None
    return row[0] if row and row[0] else None


# ── Webhook wake-ups ────────────────────────────────────────────────────────


def webhook_settings() -> dict[str, Any] | None:
    """Read the maintainer webhook route from the Hermes configuration.

    One source of truth: the same file the gateway loads, so the HMAC secret and the
    route can never drift apart.
    """
    try:
        import yaml

        config = yaml.safe_load((_hermes_home() / "config.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    platform = ((config.get("platforms") or {}).get("webhook") or {})
    if not platform.get("enabled"):
        return None
    extra = platform.get("extra") or {}
    route = (extra.get("routes") or {}).get(WEBHOOK_ROUTE) or {}
    secret = route.get("secret") or extra.get("secret")
    if not secret:
        return None
    host = extra.get("host") or "127.0.0.1"
    port = extra.get("port") or 8644
    return {
        "url": f"http://{host}:{port}/p/{WEBHOOK_PROFILE}/webhooks/{WEBHOOK_ROUTE}",
        "secret": str(secret),
    }


def post_wakeup(payload: dict[str, Any]) -> bool:
    """POST one signed wake-up to the local Hermes webhook route.

    True only on a 2xx response: the gateway accepted the event and will run the turn,
    which is what makes acknowledging the outbox row safe. The signature is HMAC-SHA256
    over ``<timestamp>.<body>`` (Hermes' replay-resistant V2 scheme).
    """
    settings = webhook_settings()
    if settings is None:
        return False
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        settings["secret"].encode("utf-8"),
        timestamp.encode("ascii") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    request = urllib.request.Request(
        settings["url"],
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": timestamp,
            "X-Webhook-Signature-V2": signature,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=WEBHOOK_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def pending_notifications() -> list[dict[str, Any]]:
    """Read the controller outbox without mutating it (the CLI owns all writes)."""
    if not STATE.exists():
        return []
    try:
        connection = sqlite3.connect(f"file:{STATE}?mode=ro", uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT id, task_id, session_key, payload_json, attempts, created_at "
                "FROM notifications WHERE delivered_at IS NULL ORDER BY id"
            ).fetchall()
        finally:
            connection.close()
    except Exception:
        return []
    result = []
    for row in rows:
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        result.append(item)
    return result


def build_wakeup_payload(notification: dict[str, Any]) -> dict[str, Any] | None:
    """Reconcile one outbox row into the flat payload the webhook prompt renders."""
    task_id = str(notification.get("task_id") or "")
    reconciled = _invoke("status", {"task": task_id})
    if not reconciled.get("ok", False):
        return None
    task = reconciled.get("task") or {}
    reason = (notification.get("payload") or {}).get("reason")
    error = ""
    if reason == "pi.failed":
        error = str(
            task.get("last_error") or (notification.get("payload") or {}).get("error") or "unknown"
        )
    return {
        "task_id": task_id,
        "project": str(task.get("project_id") or ""),
        "state": str(task.get("state") or ""),
        "pull_request_url": str(task.get("pull_request_url") or "none"),
        "preview_url": str(task.get("preview_url") or "none"),
        "branch": str(task.get("branch") or ""),
        "head_sha": str(task.get("worktree_head_sha") or ""),
        "error": error or "none",
        "intent": str(task.get("intent") or ""),
    }


def _notifier_loop() -> None:  # pragma: no cover - needs a running gateway
    while True:
        time.sleep(NOTIFIER_INTERVAL_SECONDS)
        try:
            for notification in pending_notifications():
                payload = build_wakeup_payload(notification)
                if payload is not None and post_wakeup(payload):
                    _invoke("notifications", {"ack": [notification["id"]]})
                else:
                    _invoke("notifications", {"attempt": [notification["id"]]})
        except Exception:
            continue


def start_notifier() -> None:
    global _notifier_thread
    with _notifier_lock:
        if _notifier_thread is not None and _notifier_thread.is_alive():
            return
        _notifier_thread = threading.Thread(
            target=_notifier_loop, name="maintainer-notifier", daemon=True
        )
        _notifier_thread.start()


# ── Tool handlers ───────────────────────────────────────────────────────────


def handle_project_list(_args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("project-list", {}), ensure_ascii=False)


def handle_task_list(args: dict[str, Any], **_kw) -> str:
    arguments = {"project": args.get("project")} if args.get("project") else {}
    return json.dumps(_invoke("task-list", arguments), ensure_ascii=False)


def handle_start(args: dict[str, Any], **kw) -> str:
    arguments = {
        "project": args["project"],
        "intent": args["intent"],
        "request_id": args.get("request_id"),
        "session_key": resolve_session_key(kw.get("session_id")),
    }
    decisions = args.get("decisions")
    if decisions:
        if not isinstance(decisions, dict):
            return json.dumps({"ok": False, "error": "decisions must be a JSON object"}, ensure_ascii=False)
        arguments["decisions"] = json.dumps(decisions, ensure_ascii=False)
    return json.dumps(_invoke("start", arguments), ensure_ascii=False)


def handle_status(args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("status", {"task": args["task"]}), ensure_ascii=False)


def handle_review(args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("review", {"task": args["task"]}), ensure_ascii=False)


def handle_feedback(args: dict[str, Any], **_kw) -> str:
    arguments = {"task": args["task"], "message": args["message"]}
    if args.get("attachment"):
        arguments["attachment"] = args["attachment"]
    return json.dumps(_invoke("feedback", arguments), ensure_ascii=False)


def handle_approve(args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("approve", {"task": args["task"]}), ensure_ascii=False)


def handle_stop(args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("stop", {"task": args["task"]}), ensure_ascii=False)


PROJECT_LIST_SCHEMA = _schema(
    "maintainer_project_list",
    "List the software projects registered with the maintainer controller.",
    {},
)

TASK_LIST_SCHEMA = _schema(
    "maintainer_task_list",
    "List maintainer tasks, optionally filtered by project id.",
    {"project": _str("Optional project id filter.")},
)

START_SCHEMA = _schema(
    "maintainer_start",
    "Start an authorized implementation task. Creates an isolated git worktree, a dedicated "
    "branch agent/<task-id>, and a detached direct-Pi session. Returns the task id immediately; "
    "the work runs asynchronously and a completion event arrives on its own, so never poll for "
    "it. Call exactly once per conversation turn with the same request_id.",
    {
        "project": _str("Registered project id."),
        "intent": _str(
            "Expected product outcome in English, including verification expectations. "
            "The user's original wording may be quoted inside it."
        ),
        "decisions": {
            "type": "object",
            "description": "Explicitly confirmed product decisions only (English values).",
            "additionalProperties": {"type": "string"},
        },
        "request_id": _str(
            "Stable idempotency key derived from the conversation turn, e.g. "
            "telegram:<chat_id>:<thread_id>:<message_id>."
        ),
    },
    required=["project", "intent", "request_id"],
)

STATUS_SCHEMA = _schema(
    "maintainer_status",
    "Reconcile and report one maintainer task: state, direct-Pi runtime status, worktree head, "
    "and pull request information. Use it when the user asks for an update, never in a loop.",
    {"task": _str("Task id returned by maintainer_start.")},
    required=["task"],
)

REVIEW_SCHEMA = _schema(
    "maintainer_review",
    "Build the review card for a task: pull request, required checks, preview reachability, "
    "what to evaluate, and the shadow auto-merge classification.",
    {"task": _str("Task id.")},
    required=["task"],
)

FEEDBACK_SCHEMA = _schema(
    "maintainer_feedback",
    "Send product feedback to the task's direct-Pi session. The session must be idle. Feedback "
    "is applied in the existing branch and pull request.",
    {
        "task": _str("Task id."),
        "message": _str("Feedback translated into English, preserving confirmed decisions."),
        "attachment": {"type": "array", "items": {"type": "string"}, "description": "Optional attachment paths."},
    },
    required=["task", "message"],
)

APPROVE_SCHEMA = _schema(
    "maintainer_approve",
    "Record product approval bound to the current pull request head. This never merges or deploys.",
    {"task": _str("Task id.")},
    required=["task"],
)

STOP_SCHEMA = _schema(
    "maintainer_stop",
    "Stop the direct-Pi session and mark the task stopped.",
    {"task": _str("Task id.")},
    required=["task"],
)


_TOOLS = (
    ("maintainer_project_list", PROJECT_LIST_SCHEMA, handle_project_list, "🗂️"),
    ("maintainer_task_list", TASK_LIST_SCHEMA, handle_task_list, "📋"),
    ("maintainer_start", START_SCHEMA, handle_start, "🚀"),
    ("maintainer_status", STATUS_SCHEMA, handle_status, "📡"),
    ("maintainer_review", REVIEW_SCHEMA, handle_review, "🔍"),
    ("maintainer_feedback", FEEDBACK_SCHEMA, handle_feedback, "💬"),
    ("maintainer_approve", APPROVE_SCHEMA, handle_approve, "✅"),
    ("maintainer_stop", STOP_SCHEMA, handle_stop, "🛑"),
)


def register(ctx) -> None:  # pragma: no cover — executed inside Hermes
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="maintainer",
            schema=schema,
            handler=handler,
            check_fn=_check_available,
            emoji=emoji,
        )
    start_notifier()
