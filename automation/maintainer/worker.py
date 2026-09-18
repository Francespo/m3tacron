"""Detached direct-Pi worker for one maintainer turn."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from .store import Store


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--state", type=Path, required=True)
    result.add_argument("--task", required=True)
    result.add_argument("--worktree", type=Path, required=True)
    result.add_argument("--session-dir", type=Path, required=True)
    result.add_argument("--model", required=True)
    result.add_argument("--prompt", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    store = Store(args.state)
    events_path = args.state.parent / "tasks" / args.task / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(Path("/root/.bun/bin/pi")),
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
            return completed.returncode
        store.update(args.task, runtime_pid=None, runtime_status="idle", last_error=None)
        store.audit(args.task, "pi.idle", {})
        return 0
    except Exception as exc:
        store.update(args.task, runtime_pid=None, runtime_status="failed", last_error=str(exc))
        store.audit(args.task, "pi.failed", {"error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
