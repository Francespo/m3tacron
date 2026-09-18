"""Detached direct-Pi worker for one maintainer turn.

The worker owns exactly one Pi invocation. When Pi exits it records the runtime
outcome and queues a durable wake-up for the Hermes session that started the task,
so the conversational layer never has to poll for completion.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from .store import Store

# Resolved explicitly: the gateway sanitizes PATH before spawning plugins, so
# relying on ``pi`` being discoverable made every detached worker fail.
PI_BINARY = os.environ.get("MAINTAINER_PI_BINARY", "/root/.bun/bin/pi")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--state", type=Path, required=True)
    result.add_argument("--task", required=True)
    result.add_argument("--worktree", type=Path, required=True)
    result.add_argument("--session-dir", type=Path, required=True)
    result.add_argument("--model", required=True)
    result.add_argument("--prompt", required=True)
    result.add_argument(
        "--session-key",
        default=None,
        help="Hermes routing key to wake when this turn finishes.",
    )
    return result


def notify(store: Store, args: argparse.Namespace, reason: str, payload: dict) -> None:
    """Queue the completion wake-up. Never fail the worker over notification trouble.

    The dedupe key carries this worker's PID: one Pi turn is one worker process, so a
    later feedback turn (a new worker) still produces its own notification.
    """
    try:
        store.enqueue_notification(
            args.task,
            dedupe_key=f"{args.task}:{reason}:{os.getpid()}",
            payload={"reason": reason, **payload},
            session_key=args.session_key,
        )
    except Exception:  # pragma: no cover - defensive: the Pi outcome is what matters
        pass


def main() -> int:
    args = parser().parse_args()
    store = Store(args.state)
    events_path = args.state.parent / "tasks" / args.task / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        PI_BINARY,
        "--mode",
        "json",
        "--model",
        args.model,
        "--session-id",
        args.task,
        "--session-dir",
        str(args.session_dir),
        "--name",
        f"maintainer-{args.task}",
        "--approve",
        args.prompt,
    ]
    env = os.environ.copy()
    try:
        with events_path.open("ab", buffering=0) as events:
            completed = subprocess.run(command, cwd=args.worktree, env=env, stdout=events,
                                       stderr=subprocess.STDOUT, check=False)
        if completed.returncode:
            message = f"Pi exited with status {completed.returncode}"
            store.update(args.task, runtime_pid=None, runtime_status="failed", last_error=message)
            store.audit(args.task, "pi.failed", {"returncode": completed.returncode})
            notify(store, args, "pi.failed", {"returncode": completed.returncode})
            return completed.returncode
        store.update(args.task, runtime_pid=None, runtime_status="idle", last_error=None)
        store.audit(args.task, "pi.idle", {})
        notify(store, args, "pi.idle", {"returncode": 0})
        return 0
    except Exception as exc:
        store.update(args.task, runtime_pid=None, runtime_status="failed", last_error=str(exc))
        store.audit(args.task, "pi.failed", {"error": str(exc)})
        notify(store, args, "pi.failed", {"error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
