"""Unit tests for security helpers (phase 1)."""

from __future__ import annotations

import pytest
from rplusview.safe import (
    InvalidUsernameError,
    escape_markup,
    is_safe_github_url,
    user_facing_error,
    validate_github_username,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("octocat", "octocat"),
        ("@octocat", "octocat"),
        ("  Jayyypatel  ", "Jayyypatel"),
        ("a", "a"),
        ("a-b-c", "a-b-c"),
        ("user-name123", "user-name123"),
    ],
)
def test_validate_github_username_accepts(raw: str, expected: str) -> None:
    assert validate_github_username(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "bad user",
        "org/repo",
        "octocat OR evil",
        "octocat%20",
        "-leading",
        "trailing-",
        "double--hyphen",
        "a" * 40,
        "user;rm",
        'octocat"',
    ],
)
def test_validate_github_username_rejects(raw: str) -> None:
    with pytest.raises(InvalidUsernameError):
        validate_github_username(raw)


def test_escape_markup_neutralizes_brackets() -> None:
    # Every '[' is escaped, including those that open closing tags.
    assert escape_markup("hello [bold]world[/]") == r"hello \[bold]world\[/]"
    assert escape_markup("") == ""
    assert escape_markup("no markup") == "no markup"


@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://github.com/octocat/Hello-World/pull/1", True),
        ("https://www.github.com/octocat/Hello-World", True),
        ("https://gist.github.com/octocat/abc", True),
        ("http://github.com/octocat/x", False),
        ("https://evil.com/github.com", False),
        ("https://github.com.evil.com/x", False),
        ("https://user:pass@github.com/x", False),
        ("javascript:alert(1)", False),
        ("", False),
        ("not-a-url", False),
    ],
)
def test_is_safe_github_url(url: str, ok: bool) -> None:
    assert is_safe_github_url(url) is ok


def test_user_facing_error_hides_graphql_payload() -> None:
    raw = RuntimeError([{"message": "secret internals", "type": "X"}])
    msg = user_facing_error(raw)
    assert "secret internals" not in msg
    assert "GitHub" in msg or "error" in msg.lower()


def test_user_facing_error_maps_auth() -> None:
    assert "token" in user_facing_error(RuntimeError("GitHub 401 unauthorized")).lower()
    assert "rate" in user_facing_error(RuntimeError("GitHub 403 rate limit")).lower()


def test_user_facing_error_invalid_username() -> None:
    msg = user_facing_error(InvalidUsernameError("Invalid GitHub username."))
    assert "Invalid" in msg
