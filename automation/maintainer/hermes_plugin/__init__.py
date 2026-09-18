"""Hermes plugin exposing the maintainer controller as structured tools.

The plugin runs inside Hermes processes (CLI, TUI, gateway). It shells out to
the controller CLI with argument arrays only — the model never receives a
generic terminal for maintainer work.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY_ROOT = Path("/root/projects/m3tacron")

REPOSITORY = Path(os.environ.get("MAINTAINER_REPOSITORY", DEFAULT_REPOSITORY_ROOT))
STATE = Path(os.environ.get("MAINTAINER_STATE", "~/.local/state/software-maintainer/state.db")).expanduser()
WORKTREE_ROOT = Path(
    os.environ.get("MAINTAINER_WORKTREE_ROOT", "~/.local/state/software-maintainer/worktrees")
).expanduser()


def _check_available() -> bool:
    return (REPOSITORY / "scripts" / "maintainer").exists()


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
    if process.returncode:
        detail = process.stderr.strip() or stdout
        return {"ok": False, "error": detail, "exit_code": process.returncode, **parsed}
    return {"ok": True, **parsed}


def handle_project_list(_args: dict[str, Any], **_kw) -> str:
    return json.dumps(_invoke("project-list", {}), ensure_ascii=False)


def handle_task_list(args: dict[str, Any], **_kw) -> str:
    arguments = {"project": args.get("project")} if args.get("project") else {}
    return json.dumps(_invoke("task-list", arguments), ensure_ascii=False)


def handle_start(args: dict[str, Any], **_kw) -> str:
    arguments = {
        "project": args["project"],
        "intent": args["intent"],
        "request_id": args.get("request_id"),
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
    "the work runs asynchronously. Use maintainer_status for updates. Call exactly once per "
    "conversation turn with the same request_id.",
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
    "and pull request information.",
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
