"""Persistent user config for RPlusView."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from rplusview.safe import validate_github_username


def config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    path = base / "rplusview"
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
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
    """Merge updates into config.json (mode 0600). Token is stored plaintext by design;

    the file is user-readable only (0600). Prefer OS keychain in a future release if needed.
    """
    data = load_config()
    data.update({k: v for k, v in updates.items() if v is not None})
    path = config_path()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass
    return data


def get_saved_username() -> str | None:
    username = (load_config().get("username") or "").strip()
    if not username:
        return None
    try:
        return validate_github_username(username)
    except ValueError:
        return None


def set_saved_username(username: str) -> None:
    save_config({"username": validate_github_username(username)})


def set_saved_token(token: str) -> None:
    """Persist token to config (takes precedence over env on next read)."""
    cleaned = token.strip()
    if not cleaned:
        raise ValueError("Token cannot be empty.")
    save_config({"token": cleaned})
