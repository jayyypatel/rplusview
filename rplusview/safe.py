"""Security helpers: validation, escaping, safe URL open, user-facing errors."""

from __future__ import annotations

import re
import webbrowser
from typing import Any
from urllib.parse import urlparse

# GitHub login rules: 1–39 chars, alphanumeric or single hyphens, no leading/trailing hyphen.
_GITHUB_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")

_ALLOWED_URL_HOSTS = frozenset(
    {
        "github.com",
        "www.github.com",
        "gist.github.com",
    }
)


class InvalidUsernameError(ValueError):
    """Raised when a GitHub username fails validation."""


def validate_github_username(username: str) -> str:
    """Return a normalized username or raise InvalidUsernameError."""
    cleaned = (username or "").strip()
    if cleaned.startswith("@"):
        cleaned = cleaned[1:].strip()
    if not cleaned:
        raise InvalidUsernameError("GitHub username is required.")
    if not _GITHUB_USERNAME_RE.fullmatch(cleaned):
        raise InvalidUsernameError(
            "Invalid GitHub username. Use 1–39 letters, numbers, or single hyphens."
        )
    return cleaned


def escape_markup(text: str) -> str:
    """Escape Rich markup so untrusted API/user text cannot inject styles."""
    return (text or "").replace("[", "\\[")


def is_safe_github_url(url: str) -> bool:
    """True only for https URLs on trusted GitHub hosts (no credentials in netloc)."""
    raw = (url or "").strip()
    if not raw:
        return False
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    if parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").lower()
    return host in _ALLOWED_URL_HOSTS


def open_github_url(url: str) -> bool:
    """Open URL in the browser only if it is a trusted GitHub https link.

    Returns True if opened, False if rejected.
    """
    if not is_safe_github_url(url):
        return False
    webbrowser.open(url.strip())
    return True


def user_facing_error(exc: BaseException) -> str:
    """Map exceptions to short messages safe to show in the TUI."""
    if isinstance(exc, InvalidUsernameError):
        return str(exc)
    if isinstance(exc, RuntimeError):
        msg = str(exc)
        lowered = msg.lower()
        if "no github token" in lowered or "token" in lowered and "found" in lowered:
            return "No GitHub token found. Set GITHUB_TOKEN or enter one in setup (u)."
        if "username" in lowered:
            return "No GitHub username configured. Press u to set one."
        if "401" in msg or "unauthorized" in lowered:
            return "GitHub rejected the token (unauthorized). Update it with u."
        if "403" in msg or "rate limit" in lowered or "abuse" in lowered:
            return "GitHub rate limit or permission error. Try again later or check token scopes."
        if "404" in msg:
            return "GitHub resource not found."
        if "github request failed" in lowered or "github 50" in lowered:
            return "GitHub is temporarily unavailable. Try refresh (r)."
        # Avoid dumping raw GraphQL error objects into the UI.
        if msg.startswith("[") or "messages" in lowered and "type" in lowered:
            return "GitHub API returned an error. Check token scopes and try again."
        if len(msg) > 160:
            return msg[:157] + "…"
        return msg
    name = type(exc).__name__
    brief = str(exc).strip()
    if not brief:
        return f"{name}. Try again or check your token."
    if len(brief) > 160:
        brief = brief[:157] + "…"
    return f"{name}: {brief}"


def safe_pr_field(pr: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Nested dict get for PR payloads without KeyError."""
    cur: Any = pr
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur if cur is not None else default
