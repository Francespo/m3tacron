"""Paseo and GitHub orchestration for maintainer tasks."""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any

from .config import ProjectConfig, ProjectRegistry
from .policy import shadow_merge_decision
from .prompts import feedback_prompt, implementation_prompt
from .store import StateError, Store


class ControllerError(RuntimeError):
    """Raised when an external maintainer operation fails."""


@dataclass
class CommandResult:
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


def run_command(command: list[str], *, cwd: str | None = None) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    result = CommandResult(command, completed.stdout, completed.stderr, completed.returncode)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ControllerError(f"Command failed ({completed.returncode}): {detail}")
    return result


class Controller:
    def __init__(self, registry: ProjectRegistry, store: Store):
        self.registry = registry
        self.store = store

    def start(
        self,
        *,
        project_id: str,
        intent: str,
        decisions: dict[str, Any] | None = None,
        request_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        project = self.registry.get(project_id)
        task = self.store.create_task(project_id, intent, decisions, request_id=request_id)
        if task.get("paseo_agent_id") or task["state"] != "draft":
            return {"task": task, "reused": True}
        prompt = implementation_prompt(
            task_id=task["id"],
            project_name=project.display_name,
            intent=intent,
            decisions=decisions or {},
            repository=project.repository,
            base_branch=project.base_branch,
        )
        command = self._paseo_start_command(project, task, prompt)
        if dry_run:
            return {"task": task, "command": command, "prompt": prompt, "dry_run": True}
        try:
            result = run_command(command, cwd=str(project.path))
            payload = json.loads(result.stdout)
            agent_id = payload.get("id") or payload.get("agentId")
            workspace_id = payload.get("workspaceId")
            if not agent_id:
                raise ControllerError("Paseo did not return an agent ID")
            self.store.update(
                task["id"],
                paseo_agent_id=str(agent_id),
                paseo_workspace_id=str(workspace_id) if workspace_id else None,
            )
            return self.store.transition(
                task["id"],
                "running",
                event="paseo.started",
                payload={"agent_id": agent_id},
            )
        except Exception as exc:
            self.store.update(task["id"], last_error=str(exc))
            self.store.transition(
                task["id"], "failed", event="paseo.start_failed", payload={"error": str(exc)}
            )
            raise

    @staticmethod
    def _paseo_start_command(
        project: ProjectConfig, task: dict[str, Any], prompt: str
    ) -> list[str]:
        return [
            "paseo",
            "run",
            "--background",
            "--provider",
            project.provider,
            "--new-workspace",
            "worktree",
            "--worktree-mode",
            "branch-off",
            "--worktree-slug",
            f"maintainer-{task['id']}",
            "--new-branch",
            task["branch"],
            "--base",
            f"origin/{project.base_branch}",
            "--label",
            f"maintainer_task={task['id']}",
            "--label",
            f"project={project.project_id}",
            "--title",
            f"{project.display_name}: {task['intent'][:72]}",
            "--json",
            prompt,
        ]

    def feedback(
        self,
        task_id: str,
        feedback: str,
        attachments: list[str] | None = None,
        *,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task["state"] not in {"running", "review", "blocked", "failed"}:
            raise StateError(f"Feedback is not valid while task is {task['state']}")
        if not task.get("paseo_agent_id"):
            raise StateError("Task has no Paseo agent")
        prompt = feedback_prompt(task_id, feedback, attachments or [])
        command = ["paseo", "send", task["paseo_agent_id"], prompt]
        if dry_run:
            return {"task": task, "command": command, "prompt": prompt, "dry_run": True}
        run_command(command)
        self.store.transition(
            task_id,
            "running",
            event="feedback.sent",
            payload={"attachments": attachments or []},
            force=True,
        )
        return self.store.get_task(task_id)

    def stop(self, task_id: str, *, dry_run: bool = False) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        command = ["paseo", "stop", task["paseo_agent_id"]] if task.get("paseo_agent_id") else []
        if dry_run:
            return {"task": task, "command": command, "dry_run": True}
        if command:
            run_command(command)
        return self.store.transition(task_id, "stopped", event="task.stopped", force=True)

    def sync(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        project = self.registry.get(task["project_id"])
        updates: dict[str, Any] = {}
        agent_status = None
        if task.get("paseo_agent_id"):
            try:
                raw = run_command(
                    ["paseo", "inspect", task["paseo_agent_id"], "--json"]
                ).stdout
                details = json.loads(raw)
                agent_status = details.get("status") or details.get("Status")
            except (ControllerError, json.JSONDecodeError):
                agent_status = "unknown"

        pr = self._find_pull_request(project, task["branch"])
        if pr:
            updates.update(
                pull_request_number=pr["number"],
                pull_request_url=pr["url"],
                head_sha=pr.get("headRefOid"),
                preview_url=self._preview_url(project, pr["number"]),
            )
            if task.get("approved_sha") and task["approved_sha"] != pr.get("headRefOid"):
                updates["approved_sha"] = None
        if updates:
            task = self.store.update(task_id, **updates)

        if pr and task["state"] in {"running", "blocked", "failed", "changes_requested"}:
            task = self.store.transition(
                task_id,
                "review",
                event="pull_request.discovered",
                payload={"number": pr["number"]},
                force=True,
            )
        return {"task": task, "agent_status": agent_status, "pull_request": pr}

    def review(self, task_id: str) -> dict[str, Any]:
        synced = self.sync(task_id)
        task = synced["task"]
        project = self.registry.get(task["project_id"])
        pr = synced["pull_request"]
        if not pr:
            return {
                **synced,
                "ready": False,
                "message": "No pull request has been discovered for this task.",
            }
        files = self._gh_json(
            [
                "api",
                f"repos/{project.repository}/pulls/{pr['number']}/files",
                "--paginate",
            ]
        )
        checks = self._normalize_checks(pr.get("statusCheckRollup") or [])
        changed_paths = [
            str(item.get("path") or item.get("filename") or "") for item in files
        ]
        docs_only = bool(changed_paths) and all(
            any(fnmatch(path, pattern) for pattern in project.low_risk_paths)
            for path in changed_paths
        )
        policy = shadow_merge_decision(
            project,
            files=files,
            checks=checks,
            is_draft=bool(pr.get("isDraft")),
            product_approval_required=not docs_only,
        )
        preview = self._probe_preview(task.get("preview_url"))
        return {
            **synced,
            "ready": True,
            "preview_url": task.get("preview_url"),
            "preview": preview,
            "checks": checks,
            "shadow_auto_merge": policy,
            "what_to_evaluate": [
                "Confirm that the result matches the expected product outcome.",
                "Exercise the affected flow in the preview environment.",
                "For UI changes, inspect both desktop and mobile behavior.",
            ],
        }

    def deploy_preview(self, task_id: str, *, dry_run: bool = False) -> dict[str, Any]:
        synced = self.sync(task_id)
        task = synced["task"]
        project = self.registry.get(task["project_id"])
        if not task.get("pull_request_number"):
            raise StateError("A discovered pull request is required before preview deployment")
        if not project.preview_application_uuid:
            raise StateError("This project has no preview application configured")
        command = [
            "coolify",
            "deploy",
            "uuid",
            project.preview_application_uuid,
            "--pull-request-id",
            str(task["pull_request_number"]),
            "--force",
        ]
        if dry_run:
            return {"task": task, "command": command, "dry_run": True}
        result = run_command(command)
        self.store.audit(
            task_id,
            "preview.deploy_requested",
            {"pull_request_number": task["pull_request_number"]},
        )
        return {"task": task, "requested": True, "output": result.stdout.strip()}

    def approve(self, task_id: str) -> dict[str, Any]:
        synced = self.sync(task_id)
        task = synced["task"]
        if task["state"] != "review" or not task.get("head_sha"):
            raise StateError("A discovered pull request head is required before approval")
        self.store.update(task_id, approved_sha=task["head_sha"])
        return self.store.transition(
            task_id,
            "approved",
            event="product.approved",
            payload={"head_sha": task["head_sha"]},
        )

    def _find_pull_request(self, project: ProjectConfig, branch: str) -> dict[str, Any] | None:
        rows = self._gh_json(
            [
                "pr",
                "list",
                "-R",
                project.repository,
                "--head",
                branch,
                "--state",
                "all",
                "--limit",
                "1",
                "--json",
                "number,url,isDraft,headRefOid,statusCheckRollup,title,body",
            ]
        )
        return rows[0] if rows else None

    @staticmethod
    def _preview_url(project: ProjectConfig, pr_number: int) -> str | None:
        if not project.preview_url_template:
            return None
        return project.preview_url_template.format(pr=pr_number)

    @staticmethod
    def _probe_preview(url: str | None) -> dict[str, Any]:
        if not url:
            return {"status": "not_configured"}
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "software-maintainer/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return {"status": "reachable", "http_status": response.status}
        except urllib.error.HTTPError as exc:
            return {"status": "http_error", "http_status": exc.code}
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"status": "unreachable", "detail": str(exc.reason if hasattr(exc, "reason") else exc)}

    @staticmethod
    def _normalize_checks(rollup: list[dict[str, Any]]) -> list[dict[str, str]]:
        checks = []
        for item in rollup:
            name = item.get("name") or item.get("context") or "unknown"
            conclusion = item.get("conclusion") or item.get("state") or item.get("status") or ""
            checks.append({"name": str(name), "conclusion": str(conclusion)})
        return checks

    @staticmethod
    def _gh_json(args: list[str]) -> Any:
        output = run_command(["gh", *args]).stdout
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise ControllerError("GitHub CLI returned invalid JSON") from exc


def validate_english_artifact(text: str) -> bool:
    """Reject common accidental Italian headings in generated artifacts.

    This is a narrow guard, not language detection; prompts remain the primary policy.
    """

    forbidden = re.compile(
        r"(?im)^\s*(?:#{1,6}\s*)?"
        r"(riepilogo|verifica|modifiche|rischio|descrizione|obiettivo)\s*:?\s*$"
    )
    return forbidden.search(text) is None
