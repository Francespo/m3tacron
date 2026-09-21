"""Direct Pi runtime with isolated Git worktrees and persistent sessions."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .store import StateError, Store


class PiRuntimeError(RuntimeError):
    """Raised when a direct Pi runtime operation fails."""


@dataclass(frozen=True)
class PiRuntime:
    store: Store
    state_root: Path

    def task_dir(self, task_id: str) -> Path:
        return self.state_root / "tasks" / task_id

    def worktree_path(self, project: ProjectConfig, task_id: str) -> Path:
        root = Path(os.environ.get("MAINTAINER_WORKTREE_ROOT", "~/.local/state/software-maintainer/worktrees")).expanduser()
        return root / project.project_id / task_id

    @staticmethod
    def model(project: ProjectConfig) -> str:
        value = project.provider
        return value.removeprefix("pi/")

    def start(self, project: ProjectConfig, task: dict[str, Any], prompt: str, *, dry_run: bool = False) -> dict[str, Any]:
        worktree = self.worktree_path(project, task["id"])
        task_dir = self.task_dir(task["id"])
        session_dir = task_dir / "sessions"
        command = [
            sys.executable,
            "-m",
            "automation.maintainer.worker",
            "--state",
            str(self.store.path),
            "--task",
            task["id"],
            "--worktree",
            str(worktree),
            "--session-dir",
            str(session_dir),
            "--model",
            self.model(project),
            "--prompt",
            prompt,
        ]
        if task.get("session_key"):
            command.extend(["--session-key", task["session_key"]])
        if dry_run:
            return {"command": command, "worktree": str(worktree), "session_id": task["id"]}

        self._create_worktree(project, task["branch"], worktree)
        task_dir.mkdir(parents=True, exist_ok=True)
        session_dir.mkdir(parents=True, exist_ok=True)
        log = (task_dir / "worker.log").open("ab", buffering=0)
        env = os.environ.copy()
        repository_root = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = str(repository_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        process = subprocess.Popen(
            command,
            cwd=repository_root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        log.close()
        self.store.update(
            task["id"],
            runtime_kind="pi",
            runtime_session_id=task["id"],
            runtime_pid=process.pid,
            runtime_status="running",
            worktree_path=str(worktree),
            last_error=None,
        )
        self.store.audit(task["id"], "pi.started", {"pid": process.pid, "model": self.model(project)})
        return self.store.get_task(task["id"])

    def send(self, project: ProjectConfig, task: dict[str, Any], prompt: str, *, dry_run: bool = False) -> dict[str, Any]:
        if not task.get("worktree_path") or not task.get("runtime_session_id"):
            raise StateError("Task has no direct Pi session")
        if self.status(task)["status"] == "running":
            raise StateError("Pi is still running; wait for it to become idle before sending feedback")
        command = [
            sys.executable,
            "-m",
            "automation.maintainer.worker",
            "--state",
            str(self.store.path),
            "--task",
            task["id"],
            "--worktree",
            task["worktree_path"],
            "--session-dir",
            str(self.task_dir(task["id"]) / "sessions"),
            "--model",
            self.model(project),
            "--prompt",
            prompt,
        ]
        if task.get("session_key"):
            command.extend(["--session-key", task["session_key"]])
        if dry_run:
            return {"command": command, "task": task}
        log = (self.task_dir(task["id"]) / "worker.log").open("ab", buffering=0)
        env = os.environ.copy()
        repository_root = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = str(repository_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        process = subprocess.Popen(command, cwd=repository_root, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
        log.close()
        self.store.update(task["id"], runtime_pid=process.pid, runtime_status="running", last_error=None)
        self.store.audit(task["id"], "pi.feedback_started", {"pid": process.pid})
        return self.store.get_task(task["id"])

    def status(self, task: dict[str, Any]) -> dict[str, Any]:
        pid = task.get("runtime_pid")
        alive = False
        if pid:
            try:
                os.kill(int(pid), 0)
                alive = True
            except (ProcessLookupError, PermissionError):
                alive = False
        status = "running" if alive else (task.get("runtime_status") or "unknown")
        if not alive and status == "running":
            status = "interrupted"
            self.store.update(task["id"], runtime_status=status, runtime_pid=None)
        return {"status": status, "pid": pid if alive else None, "session_id": task.get("runtime_session_id")}

    def stop(self, task: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
        pid = task.get("runtime_pid")
        if dry_run:
            return {"task": task, "pid": pid, "dry_run": True}
        if pid:
            try:
                os.killpg(int(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.store.update(task["id"], runtime_pid=None, runtime_status="stopped")
        self.store.audit(task["id"], "pi.stopped", {})
        return self.store.get_task(task["id"])

    @staticmethod
    def _create_worktree(project: ProjectConfig, branch: str, path: Path) -> None:
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "fetch", "origin", project.base_branch], cwd=project.path,
                       check=True, capture_output=True, text=True)
        completed = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(path), f"origin/{project.base_branch}"],
            cwd=project.path, capture_output=True, text=True,
        )
        if completed.returncode:
            raise PiRuntimeError(completed.stderr.strip() or completed.stdout.strip())
