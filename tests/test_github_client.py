"""GitHub client safety tests (phase 1, no network)."""

from __future__ import annotations

import pytest
from rplusview.github_client import _graphql_error_message, _search_query, categorize_inbox
from rplusview.safe import InvalidUsernameError


def test_search_query_rejects_injection() -> None:
    with pytest.raises(InvalidUsernameError):
        _search_query("octocat OR evil", "open")


def test_search_query_builds_safe_string() -> None:
    assert _search_query("octocat", "open") == "author:octocat type:pr is:open"
    assert _search_query("@octocat", "closed") == "author:octocat type:pr is:closed"


def test_graphql_error_message_is_short() -> None:
    msg = _graphql_error_message([{"message": "x" * 300, "type": "X"}])
    assert len(msg) < 200
    assert "GitHub API error" in msg


def test_categorize_inbox_basic() -> None:
    authored = [
        {"isDraft": True, "title": "d", "author": {"login": "octocat"}},
        {
            "isDraft": False,
            "reviewDecision": "APPROVED",
            "mergeable": "MERGEABLE",
            "author": {"login": "octocat"},
        },
        {
            "isDraft": False,
            "reviewDecision": "CHANGES_REQUESTED",
            "mergeable": "MERGEABLE",
            "author": {"login": "octocat"},
        },
    ]
    reviews = [
        {"author": {"login": "other"}, "title": "needs me"},
        {"author": {"login": "octocat"}, "title": "self"},
    ]
    out = categorize_inbox(authored, reviews, username="octocat")
    assert len(out["drafts"]) == 1
    assert len(out["ready"]) == 1
    assert len(out["needs_action"]) == 1
    assert len(out["needs_review"]) == 1
