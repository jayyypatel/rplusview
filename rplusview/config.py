"""Persistent user config for RPlusView."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    path = base / "rplusview"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(updates: dict[str, Any]) -> dict[str, Any]:
    data = load_config()
    data.update({k: v for k, v in updates.items() if v is not None})
    path = config_path()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return data


def get_saved_username() -> str | None:
    username = (load_config().get("username") or "").strip()
    return username or None


def set_saved_username(username: str) -> None:
    save_config({"username": username.strip()})
