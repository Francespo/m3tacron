"""Command-line interface used by Hermes and operators."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .config import ConfigError, ProjectRegistry
from .controller import Controller, ControllerError
from .runtime import PiRuntime, PiRuntimeError
from .store import StateError, Store

DEFAULT_REGISTRY = Path(__file__).with_name("projects.json")
DEFAULT_STATE = Path(os.environ.get("MAINTAINER_STATE", "~/.local/state/software-maintainer/state.db")).expanduser()


def json_value(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("Value must be a JSON object")
    return parsed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Reusable software maintainer with direct Pi runtime")
    result.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    result.add_argument("--state", type=Path, default=DEFAULT_STATE)
    sub = result.add_subparsers(dest="command", required=True)

    sub.add_parser("project-list", help="List registered projects")
    task_list = sub.add_parser("task-list", help="List tasks")
    task_list.add_argument("--project")

    start = sub.add_parser("start", help="Start implementation in an isolated Git worktree with direct Pi")
    start.add_argument("--project", required=True)
    start.add_argument("--intent", required=True)
    start.add_argument("--decisions", type=json_value, default={})
    start.add_argument(
        "--request-id",
        help="Stable idempotency key supplied by the conversational client",
    )
    start.add_argument(
        "--session-key",
        help="Hermes routing key to wake when the task finishes",
    )
    start.add_argument("--dry-run", action="store_true")

    status = sub.add_parser("status", help="Show and reconcile a task")
    status.add_argument("--task", required=True)

    review = sub.add_parser("review", help="Build a concise pull-request review")
    review.add_argument("--task", required=True)

    preview = sub.add_parser("preview-deploy", help="Request a scoped Coolify PR preview")
    preview.add_argument("--task", required=True)
    preview.add_argument("--dry-run", action="store_true")

    feedback = sub.add_parser("feedback", help="Send feedback to the existing agent")
    feedback.add_argument("--task", required=True)
    feedback.add_argument("--message", required=True)
    feedback.add_argument("--attachment", action="append", default=[])
    feedback.add_argument("--dry-run", action="store_true")

    approve = sub.add_parser("approve", help="Record approval for the current PR head")
    approve.add_argument("--task", required=True)

    stop = sub.add_parser("stop", help="Stop an active task")
    stop.add_argument("--task", required=True)
    stop.add_argument("--dry-run", action="store_true")

    audit = sub.add_parser("audit", help="Show a task audit trail")
    audit.add_argument("--task", required=True)

    notifications = sub.add_parser(
        "notifications", help="Read or acknowledge pending completion wake-ups"
    )
    notifications.add_argument(
        "--pending", action="store_true", help="List wake-ups not yet delivered"
    )
    notifications.add_argument(
        "--ack",
        type=int,
        action="append",
        default=[],
        help="Mark a wake-up delivered",
    )
    notifications.add_argument(
        "--attempt",
        type=int,
        action="append",
        default=[],
        help="Record a delivery attempt without acknowledging",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        registry = ProjectRegistry.load(args.registry)
        store = Store(args.state)
        runtime = PiRuntime(store=store, state_root=args.state.parent)
        controller = Controller(registry, store, runtime)
        if args.command == "project-list":
            output = [
                {
                    "id": item.project_id,
                    "display_name": item.display_name,
                    "repository": item.repository,
                    "base_branch": item.base_branch,
                }
                for item in registry.projects.values()
            ]
        elif args.command == "task-list":
            output = store.list_tasks(args.project)
        elif args.command == "start":
            output = controller.start(
                project_id=args.project,
                intent=args.intent,
                decisions=args.decisions,
                request_id=args.request_id,
                session_key=args.session_key,
                dry_run=args.dry_run,
            )
        elif args.command == "status":
            output = controller.sync(args.task)
        elif args.command == "review":
            output = controller.review(args.task)
        elif args.command == "preview-deploy":
            output = controller.deploy_preview(args.task, dry_run=args.dry_run)
        elif args.command == "feedback":
            output = controller.feedback(
                args.task,
                args.message,
                args.attachment,
                dry_run=args.dry_run,
            )
        elif args.command == "approve":
            output = controller.approve(args.task)
        elif args.command == "stop":
            output = controller.stop(args.task, dry_run=args.dry_run)
        elif args.command == "audit":
            output = store.audit_events(args.task)
        elif args.command == "notifications":
            for notification_id in args.attempt:
                store.note_notification_attempt(notification_id)
            acknowledged = [
                notification_id
                for notification_id in args.ack
                if store.mark_notification_delivered(notification_id)
            ]
            output = {
                "acknowledged": acknowledged,
                "pending": store.pending_notifications(),
            }
        else:  # pragma: no cover
            raise AssertionError(args.command)
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ConfigError, StateError, ControllerError, PiRuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
