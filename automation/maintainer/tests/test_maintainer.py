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
    def test_paseo_command_uses_arguments_not_shell(self) -> None:
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
        task = {"id": "abc123", "branch": "agent/abc123", "intent": "Add a feature"}
        command = Controller._paseo_start_command(project, task, "prompt; rm -rf /")
        self.assertEqual(command[0:2], ["paseo", "run"])
        self.assertIn("pi/manifest/auto-coding", command)
        self.assertEqual(command[-1], "prompt; rm -rf /")
        self.assertNotIn("sh", command)

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
            task = store.create_task("demo", "Preview it")
            store.update(task["id"], pull_request_number=42)
            controller = Controller(ProjectRegistry.load(registry_path), store)
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
