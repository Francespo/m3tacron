from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.maintainer.config import ProjectConfig, ProjectRegistry
from automation.maintainer.controller import Controller, validate_english_artifact
from automation.maintainer.policy import shadow_merge_decision
from automation.maintainer.prompts import implementation_prompt
from automation.maintainer.runtime import PiRuntime
from automation.maintainer.runtime import PiRuntime
from automation.maintainer.store import StateError, Store


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "state.db")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_task_lifecycle_and_audit(self) -> None:
        task = self.store.create_task("demo", "Improve search", {"surface": "home"})
        self.assertEqual(task["state"], "draft")
        self.assertEqual(task["decisions"]["surface"], "home")
        task = self.store.transition(task["id"], "running", event="test.started")
        self.assertEqual(task["state"], "running")
        events = self.store.audit_events(task["id"])
        self.assertEqual([event["event"] for event in events], ["task.created", "test.started"])

    def test_invalid_transition_is_rejected(self) -> None:
        task = self.store.create_task("demo", "Improve search")
        with self.assertRaises(StateError):
            self.store.transition(task["id"], "approved", event="invalid")

    def test_request_id_makes_creation_idempotent(self) -> None:
        first = self.store.create_task(
            "demo", "Improve search", request_id="conversation-turn-1"
        )
        second = self.store.create_task(
            "demo", "A duplicate request", request_id="conversation-turn-1"
        )
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["intent"], "Improve search")


class PromptTests(unittest.TestCase):
    def test_prompt_preserves_source_and_requires_english_artifacts(self) -> None:
        prompt = implementation_prompt(
            task_id="abc",
            project_name="Demo",
            intent="Migliora la ricerca",
            decisions={},
            repository="owner/demo",
            base_branch="main",
        )
        self.assertIn("Migliora la ricerca", prompt)
        self.assertIn("artifacts must be written in English", prompt)
        self.assertIn("Maintainer-Task: abc", prompt)

    def test_accidental_italian_artifact_heading_is_rejected(self) -> None:
        self.assertFalse(validate_english_artifact("## Riepilogo\nSomething"))
        self.assertTrue(validate_english_artifact("## Summary\nSomething"))


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "state.db")
        self.runtime = PiRuntime(store=self.store, state_root=Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _controller(self) -> Controller:
        registry_path = Path(self.temp.name) / "projects.json"
        registry_path.write_text(
            json.dumps(
                {
                    "projects": {
                        "demo": {
                            "display_name": "Demo",
                            "path": self.temp.name,
                            "repository": "owner/demo",
                            "base_branch": "main",
                            "provider": "pi/manifest/auto-coding",
                        }
                    }
                }
            )
        )
        return Controller(ProjectRegistry.load(registry_path), self.store, self.runtime)

    def test_start_is_idempotent_for_same_request_id(self) -> None:
        controller = self._controller()
        first = controller.start(
            project_id="demo",
            intent="Add a feature",
            request_id="turn-1",
            dry_run=True,
        )
        second = controller.start(
            project_id="demo",
            intent="Different intent",
            request_id="turn-1",
            dry_run=True,
        )
        self.assertEqual(first["task"]["id"], second["task"]["id"])
        self.assertFalse(second.get("reused"))

    def test_start_after_real_runtime_is_reused(self) -> None:
        controller = self._controller()

        def mark_started(_project, task, _prompt):
            return self.store.update(
                task["id"],
                runtime_pid=4242,
                runtime_status="running",
            )

        with patch.object(PiRuntime, "start", side_effect=mark_started):
            first = controller.start(
                project_id="demo", intent="Add a feature", request_id="turn-1"
            )
            second = controller.start(
                project_id="demo", intent="Again", request_id="turn-1"
            )
        self.assertNotIn("reused", first)
        self.assertTrue(second["reused"])
        self.assertEqual(first["task"]["state"], "running")
        self.assertEqual(second["task"]["id"], first["task"]["id"])

    def test_worktree_path_is_isolated_per_task(self) -> None:
        project = ProjectConfig.from_dict(
            "demo",
            {
                "display_name": "Demo",
                "path": "/tmp/demo",
                "repository": "owner/demo",
                "base_branch": "main",
                "provider": "pi/manifest/auto-coding",
            },
        )
        first = self.runtime.worktree_path(project, "abc123")
        second = self.runtime.worktree_path(project, "def456")
        self.assertNotEqual(first, second)
        self.assertTrue(str(first).endswith("demo/abc123"))

    def test_pi_command_uses_arguments_not_shell(self) -> None:
        project = ProjectConfig.from_dict(
            "demo",
            {
                "display_name": "Demo",
                "path": "/tmp/demo",
                "repository": "owner/demo",
                "base_branch": "main",
                "provider": "pi/manifest/auto-coding",
            },
        )
        task = {"id": "abc123", "branch": "agent/abc123"}
        command = self.runtime.start(project, task, "prompt; rm -rf /", dry_run=True)["command"]
        self.assertIn("automation.maintainer.worker", " ".join(command))
        self.assertIn("manifest/auto-coding", command)
        self.assertNotIn("sh -c", command)

    def test_hermes_plugin_wraps_list_payloads(self) -> None:
        from automation.maintainer import hermes_plugin

        assert hermes_plugin._invoke.__globals__["STATE"]
        task = self.store.create_task("demo", "Probe it")
        tasks = self.store.list_tasks("demo")
        self.assertTrue(any(item["id"] == task["id"] for item in tasks))

    def test_worker_resolves_pi_binary_minimally(self) -> None:
        import inspect

        from automation.maintainer import worker

        source = inspect.getsource(worker.main)
        self.assertIn("/root/.bun/bin/pi", source)

    def test_feedback_requires_session_and_idle(self) -> None:
        controller = self._controller()
        task = self.store.create_task("demo", "Add a feature")
        with self.assertRaises(StateError):
            controller.feedback(task["id"], "Change it")
        self.store.update(
            task["id"],
            runtime_session_id=task["id"],
            worktree_path="/tmp/wt",
            runtime_status="idle",
            runtime_pid=None,
        )
        self.store.transition(task["id"], "running", event="test.started", force=True)
        with patch.object(PiRuntime, "send") as send_mock:
            send_mock.return_value = self.store.get_task(task["id"])
            result = controller.feedback(task["id"], "Change it")
        self.assertEqual(result["state"], "running")

    def test_stop_marks_stopped_without_pid(self) -> None:
        controller = self._controller()
        task = self.store.create_task("demo", "Add a feature")
        self.store.update(task["id"], runtime_status="idle", runtime_pid=None)
        result = controller.stop(task["id"])
        self.assertEqual(result["state"], "stopped")

    def test_preview_command_is_scoped_to_registered_app_and_pr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "projects.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "projects": {
                            "demo": {
                                "display_name": "Demo",
                                "path": directory,
                                "repository": "owner/demo",
                                "base_branch": "main",
                                "preview_application_uuid": "app-123",
                            }
                        }
                    }
                )
            )
            store = Store(Path(directory) / "state.db")
            runtime = PiRuntime(store=store, state_root=Path(directory))
            task = store.create_task("demo", "Preview it")
            store.update(task["id"], pull_request_number=42)
            controller = Controller(ProjectRegistry.load(registry_path), store, runtime)
            with patch.object(
                controller,
                "sync",
                return_value={"task": store.get_task(task["id"]), "pull_request": {}},
            ):
                result = controller.deploy_preview(task["id"], dry_run=True)
        self.assertEqual(
            result["command"],
            [
                "coolify",
                "deploy",
                "uuid",
                "app-123",
                "--pull-request-id",
                "42",
                "--force",
            ],
        )
        self.assertNotIn("main", result["command"])


class PolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ProjectConfig.from_dict(
            "demo",
            {
                "display_name": "Demo",
                "path": "/tmp/demo",
                "repository": "owner/demo",
                "base_branch": "main",
                "required_checks": ["Tests"],
                "policy": {
                    "sensitive_paths": [".github/**"],
                    "low_risk_paths": ["docs/**", "**/*.md"],
                    "max_low_risk_files": 3,
                    "max_low_risk_lines": 50,
                },
            },
        )

    def test_docs_change_is_shadow_eligible_without_product_gate(self) -> None:
        result = shadow_merge_decision(
            self.project,
            files=[{"filename": "docs/guide.md", "additions": 5, "deletions": 1}],
            checks=[{"name": "Tests", "conclusion": "SUCCESS"}],
            is_draft=False,
            product_approval_required=False,
        )
        self.assertTrue(result["would_merge"])
        self.assertEqual(result["mode"], "shadow")

    def test_sensitive_change_is_never_eligible(self) -> None:
        result = shadow_merge_decision(
            self.project,
            files=[{"filename": ".github/workflows/ci.yml", "additions": 5, "deletions": 1}],
            checks=[{"name": "Tests", "conclusion": "SUCCESS"}],
            is_draft=False,
            product_approval_required=False,
        )
        self.assertFalse(result["would_merge"])
        self.assertIn("A sensitive path changed.", result["reasons"])


class RegistryTests(unittest.TestCase):
    def test_registry_loads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "projects.json"
            path.write_text(
                json.dumps(
                    {
                        "projects": {
                            "demo": {
                                "display_name": "Demo",
                                "path": directory,
                                "repository": "owner/demo",
                                "base_branch": "main",
                            }
                        }
                    }
                )
            )
            registry = ProjectRegistry.load(path)
            self.assertEqual(registry.get("demo").display_name, "Demo")


if __name__ == "__main__":
    unittest.main()
