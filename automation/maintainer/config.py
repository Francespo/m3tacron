"""Project registry loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when the maintainer configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    project_id: str
    display_name: str
    path: Path
    repository: str
    base_branch: str
    provider: str
    preview_url_template: str | None
    preview_application_uuid: str | None
    required_checks: tuple[str, ...]
    sensitive_paths: tuple[str, ...]
    low_risk_paths: tuple[str, ...]
    max_low_risk_files: int
    max_low_risk_lines: int

    @classmethod
    def from_dict(cls, project_id: str, raw: dict[str, Any]) -> "ProjectConfig":
        required = ("display_name", "path", "repository", "base_branch")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ConfigError(
                f"Project {project_id!r} is missing: {', '.join(missing)}"
            )
        path = Path(raw["path"]).expanduser().resolve()
        policy = raw.get("policy", {})
        return cls(
            project_id=project_id,
            display_name=str(raw["display_name"]),
            path=path,
            repository=str(raw["repository"]),
            base_branch=str(raw["base_branch"]),
            provider=str(raw.get("provider", "pi/manifest/auto-coding")),
            preview_url_template=raw.get("preview_url_template"),
            preview_application_uuid=raw.get("preview_application_uuid"),
            required_checks=tuple(raw.get("required_checks", ())),
            sensitive_paths=tuple(policy.get("sensitive_paths", ())),
            low_risk_paths=tuple(policy.get("low_risk_paths", ())),
            max_low_risk_files=int(policy.get("max_low_risk_files", 5)),
            max_low_risk_lines=int(policy.get("max_low_risk_lines", 150)),
        )


class ProjectRegistry:
    def __init__(self, projects: dict[str, ProjectConfig], source: Path):
        self.projects = projects
        self.source = source

    @classmethod
    def load(cls, path: Path) -> "ProjectRegistry":
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ConfigError(f"Project registry not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid project registry JSON: {exc}") from exc
        projects_raw = raw.get("projects")
        if not isinstance(projects_raw, dict) or not projects_raw:
            raise ConfigError("Project registry must contain a non-empty projects object")
        projects = {
            project_id: ProjectConfig.from_dict(project_id, project_raw)
            for project_id, project_raw in projects_raw.items()
        }
        return cls(projects, path)

    def get(self, project_id: str) -> ProjectConfig:
        try:
            return self.projects[project_id]
        except KeyError as exc:
            known = ", ".join(sorted(self.projects))
            raise ConfigError(f"Unknown project {project_id!r}; available: {known}") from exc
