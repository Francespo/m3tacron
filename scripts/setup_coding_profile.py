#!/usr/bin/env python3
"""Create or update the reusable Hermes coding profile safely."""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROFILE_NAME = "coding"
MODEL = "auto-coding"
PROVIDER = "custom:manifest"
PLUGIN_NAME = "software-maintainer"
WEBHOOK_ROUTE = "maintainer-completion"
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 8644

# Rendered by the gateway into the agent prompt. Everything the completion turn needs is
# in the payload, so the agent never has to guess what finished.
WEBHOOK_PROMPT = (
    "A software-maintainer task finished.\n\n"
    "Task: {task_id}\n"
    "Project: {project}\n"
    "State: {state}\n"
    "Pull request: {pull_request_url}\n"
    "Preview: {preview_url}\n"
    "Branch: {branch}\n"
    "Head: {head_sha}\n"
    "Runtime error: {error}\n\n"
    "Report this outcome to the user in the language they are using. When a pull request "
    "exists, call maintainer_review with the argument task = {task_id} so the review card "
    "(required checks, preview reachability, shadow merge classification) is included. "
    "Never merge and never deploy to production."
)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")


def profile_home() -> Path:
    return Path.home() / ".hermes" / "profiles" / PROFILE_NAME


def remove_inherited_gateway_credentials(home: Path) -> None:
    """Let the default adapter receive messages and route them into this profile."""
    env_path = home / ".env"
    if not env_path.exists():
        return
    adapter_prefixes = ("TELEGRAM_", "MATRIX_")
    lines = env_path.read_text(encoding="utf-8").splitlines()
    filtered = [
        line
        for line in lines
        if not line.lstrip().startswith(adapter_prefixes)
    ]
    env_path.write_text("\n".join(filtered).rstrip() + "\n", encoding="utf-8")


def install_plugin(repository: Path, home: Path) -> None:
    source = repository / "automation" / "maintainer" / "hermes_plugin"
    destination = home / "plugins" / PLUGIN_NAME
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def configure_profile(repository: Path) -> Path:
    home = profile_home()
    if not home.exists():
        run(
            [
                "hermes",
                "profile",
                "create",
                PROFILE_NAME,
                "--clone-from",
                "default",
                "--description",
                "General software product and engineering interface backed by direct Pi automation",
            ]
        )
    config_path = home / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config["model"] = {"default": MODEL, "provider": PROVIDER}
    # The coding route owns failover. Do not inherit the everyday Hermes chain.
    config["fallback_providers"] = []
    plugins = config.setdefault("plugins", {})
    enabled_plugins = plugins.setdefault("enabled", [])
    if PLUGIN_NAME not in enabled_plugins:
        enabled_plugins.append(PLUGIN_NAME)
    platform_toolsets = config.setdefault("platform_toolsets", {})
    # Keep the Telegram coding surface narrow: conversation clarification plus
    # structured maintainer operations. Pi owns repository and terminal work.
    platform_toolsets["telegram"] = ["clarify", "kanban", "maintainer"]
    auxiliary = config.setdefault("auxiliary", {})
    for key in ("triage_specifier", "kanban_decomposer"):
        auxiliary.setdefault(key, {})
        auxiliary[key]["provider"] = "manifest"
        auxiliary[key]["model"] = MODEL
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    remove_inherited_gateway_credentials(home)

    skill_source = repository / "automation" / "maintainer" / "hermes" / "SKILL.md"
    skill_dir = home / "skills" / "software-maintainer"
    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill_source, skill_dir / "SKILL.md")
    return home


def configure_route(chat_id: str, thread_id: str | None = None) -> None:
    default_config_path = Path.home() / ".hermes" / "config.yaml"
    config = yaml.safe_load(default_config_path.read_text(encoding="utf-8")) or {}
    gateway = config.setdefault("gateway", {})
    gateway["multiplex_profiles"] = True
    routes = gateway.setdefault("profile_routes", [])
    route = {
        "name": "coding-channel",
        "platform": "telegram",
        "chat_id": str(chat_id),
        "profile": PROFILE_NAME,
        "enabled": True,
    }
    routes[:] = [item for item in routes if item.get("name") != "coding-channel"]
    routes.append(route)
    default_config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    configure_completion_webhook(str(chat_id), thread_id)


def configure_completion_webhook(chat_id: str, thread_id: str | None) -> None:
    """Provision the loopback webhook route that wakes the agent on task completion.

    The route binds to the coding profile and delivers the agent's reply into the Telegram
    conversation. The HMAC secret is generated once and preserved on re-runs, and the file
    stays 0600 because it holds that secret.
    """
    config_path = Path.home() / ".hermes" / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    platform = config.setdefault("platforms", {}).setdefault("webhook", {})
    platform["enabled"] = True
    extra = platform.setdefault("extra", {})
    extra["host"] = WEBHOOK_HOST
    extra["port"] = WEBHOOK_PORT
    secret = extra.get("secret") or secrets.token_urlsafe(32)
    extra["secret"] = secret
    deliver_extra = {"chat_id": str(chat_id)}
    if thread_id:
        deliver_extra["message_thread_id"] = str(thread_id)
    extra.setdefault("routes", {})[WEBHOOK_ROUTE] = {
        "profile": PROFILE_NAME,
        "description": "Wake the coding profile when a maintainer task finishes",
        "secret": secret,
        "skills": ["software-maintainer"],
        "deliver": "telegram",
        "deliver_extra": deliver_extra,
        "prompt": WEBHOOK_PROMPT,
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    config_path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat-id", help="Private Telegram group chat ID")
    parser.add_argument("--thread-id", help="Telegram forum topic ID for completion notices")
    parser.add_argument("--restart-gateway", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent

    backup_root = Path.home() / ".hermes" / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    default_config = Path.home() / ".hermes" / "config.yaml"
    if default_config.exists():
        shutil.copy2(default_config, backup_root / f"config-before-coding-{stamp}.yaml")

    home = configure_profile(repository)
    install_plugin(repository, home)
    if args.chat_id:
        configure_route(args.chat_id, args.thread_id)
        if args.restart_gateway:
            run(["hermes", "gateway", "restart"])

    print(f"Coding profile configured at {home}")
    print(f"Primary model: {PROVIDER}/{MODEL}")
    if args.chat_id:
        print(f"Telegram route configured for chat {args.chat_id}")
        print(f"Completion webhook: http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/p/{PROFILE_NAME}/webhooks/{WEBHOOK_ROUTE}")
    else:
        print("Telegram route pending. Re-run with --chat-id after creating the private group.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
