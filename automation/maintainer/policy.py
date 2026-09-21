"""Deterministic shadow auto-merge policy."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

from .config import ProjectConfig


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def shadow_merge_decision(
    project: ProjectConfig,
    *,
    files: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    is_draft: bool,
    product_approval_required: bool,
) -> dict[str, Any]:
    reasons: list[str] = []
    paths = [str(item.get("path") or item.get("filename") or "") for item in files]
    changed_lines = sum(
        int(item.get("additions", 0)) + int(item.get("deletions", 0)) for item in files
    )

    if is_draft:
        reasons.append("The pull request is still a draft.")
    if product_approval_required:
        reasons.append("Product approval is required.")
    if len(paths) > project.max_low_risk_files:
        reasons.append("The changed file count exceeds the low-risk limit.")
    if changed_lines > project.max_low_risk_lines:
        reasons.append("The changed line count exceeds the low-risk limit.")
    if any(_matches(path, project.sensitive_paths) for path in paths):
        reasons.append("A sensitive path changed.")
    if not paths:
        reasons.append("No changed files were found.")
    elif any(not _matches(path, project.low_risk_paths) for path in paths):
        reasons.append("At least one changed path is outside the low-risk allowlist.")

    check_by_name = {
        str(check.get("name", "")): str(check.get("conclusion", "")).upper()
        for check in checks
    }
    missing = [name for name in project.required_checks if name not in check_by_name]
    failed = [
        name
        for name in project.required_checks
        if check_by_name.get(name) not in {"SUCCESS", "NEUTRAL", "SKIPPED"}
    ]
    if missing:
        reasons.append(f"Required checks are missing: {', '.join(missing)}.")
    if failed:
        reasons.append(f"Required checks are not successful: {', '.join(failed)}.")

    eligible = not reasons
    return {
        "mode": "shadow",
        "eligible": eligible,
        "would_merge": eligible,
        "reasons": reasons,
        "changed_files": len(paths),
        "changed_lines": changed_lines,
    }
