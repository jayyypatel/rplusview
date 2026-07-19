"""GitHub GraphQL client for RPlusView."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any, Literal

import requests

from rplusview.safe import InvalidUsernameError, validate_github_username

API_URL = "https://api.github.com/graphql"

PR_StateFilter = Literal["open", "closed", "all"]

LIST_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: ISSUE, first: 100, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
        number
        title
        url
        body
        additions
        deletions
        changedFiles
        state
        merged
        isDraft
        mergeable
        reviewDecision
        createdAt
        updatedAt
        headRefName
        author {
          login
        }
        comments {
          totalCount
        }
        reviewThreads(first: 100) {
          totalCount
          nodes {
            comments {
              totalCount
            }
          }
        }
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                state
                contexts(first: 40) {
                  nodes {
                    ... on CheckRun {
                      status
                      conclusion
                    }
                    ... on StatusContext {
                      state
                    }
                  }
                }
              }
            }
          }
        }
        repository {
          nameWithOwner
          url
        }
      }
    }
  }
}
"""

DETAIL_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      number
      title
      url
      body
      additions
      deletions
      changedFiles
      state
      merged
      isDraft
      createdAt
      updatedAt
      baseRefName
      headRefName
      author {
        login
      }
      labels(first: 20) {
        nodes {
          name
        }
      }
      commits {
        totalCount
      }
      comments(first: 40) {
        totalCount
        nodes {
          author {
            login
          }
          body
          createdAt
        }
      }
      reviewThreads(first: 100) {
        totalCount
        nodes {
          isResolved
          comments(first: 30) {
            totalCount
            nodes {
              author {
                login
              }
              body
              createdAt
              path
              line
            }
          }
        }
      }
      reviews(first: 30) {
        totalCount
        nodes {
          author {
            login
          }
          body
          state
          createdAt
        }
      }
      repository {
        nameWithOwner
        url
      }
    }
  }
}
"""

# Inbox panel keys in GitHub Pulls-style order
INBOX_SECTIONS = (
    ("needs_review", "Needs your review"),
    ("needs_team_review", "Needs your teams' review"),
    ("drafts", "Your drafts"),
    ("waiting", "Waiting for review or checks"),
    ("needs_action", "Needs action"),
    ("ready", "Ready to merge"),
)


def _load_dotenv() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for env_path in candidates:
        if not env_path.is_file():
            continue
        with env_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
        break


def get_token() -> str | None:
    """Resolve GitHub token: saved config first (UI-updated), then env / .env."""
    from rplusview.config import load_config

    saved = (load_config().get("token") or "").strip()
    if saved:
        return saved
    _load_dotenv()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return token.strip() if token else None


def has_token() -> bool:
    return bool(get_token())


def get_username() -> str | None:
    """Resolve tracked GitHub username from saved config (preferred) or env."""
    from rplusview.config import get_saved_username

    saved = get_saved_username()
    if saved:
        return saved
    _load_dotenv()
    env_user = os.environ.get("GITHUB_USERNAME") or os.environ.get("GH_USER")
    raw = (env_user or "").strip()
    if not raw:
        return None
    try:
        return validate_github_username(raw)
    except InvalidUsernameError:
        return None


def require_token() -> str:
    token = get_token()
    if not token:
        raise RuntimeError("No GitHub token found. Set GITHUB_TOKEN or enter one in setup.")
    return token


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "rplusview",
    }


def _graphql_error_message(errors: Any) -> str:
    """Collapse GraphQL error payloads into a short RuntimeError message."""
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            msg = str(first.get("message") or "GraphQL error")
            return f"GitHub API error: {msg[:120]}"
        return f"GitHub API error: {str(first)[:120]}"
    return "GitHub API returned an error."


def _post_graphql(headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            if response.status_code in {502, 503, 504}:
                last_error = RuntimeError(f"GitHub {response.status_code}")
                continue
            if response.status_code == 401:
                raise RuntimeError("GitHub 401 unauthorized")
            if response.status_code == 403:
                raise RuntimeError("GitHub 403 rate limit or permission denied")
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise RuntimeError(_graphql_error_message(data["errors"]))
            return data
        except requests.RequestException as exc:
            last_error = exc
    raise RuntimeError(f"GitHub request failed: {last_error}")


def _search_query(username: str, state: PR_StateFilter) -> str:
    safe_user = validate_github_username(username)
    base = f"author:{safe_user} type:pr"
    if state == "open":
        return f"{base} is:open"
    if state == "closed":
        return f"{base} is:closed"
    return base


def _search_prs(search_query: str) -> list[dict[str, Any]]:
    token = require_token()
    headers = _headers(token)
    prs: list[dict[str, Any]] = []
    cursor = None

    while True:
        data = _post_graphql(
            headers,
            {
                "query": LIST_QUERY,
                "variables": {
                    "query": search_query,
                    "cursor": cursor,
                },
            },
        )
        search = data["data"]["search"]
        prs.extend(node for node in search["nodes"] if node)

        if not search["pageInfo"]["hasNextPage"]:
            break
        cursor = search["pageInfo"]["endCursor"]

    return prs


def get_prs(
    author: str | None = None,
    *,
    state: PR_StateFilter = "open",
) -> list[dict[str, Any]]:
    """Fetch PRs for an author. Defaults to open-only for faster first load."""
    username = author or get_username()
    if not username:
        raise RuntimeError("No GitHub username configured.")
    username = validate_github_username(username)
    return _search_prs(_search_query(username, state))


def get_inbox(
    author: str | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Fetch and categorize PRs into a GitHub Pulls-style inbox.

    Returns ``(sections, warnings)``. Warnings are user-facing strings when
    optional inbox slices (e.g. review requests) fail.
    """
    username = author or get_username()
    if not username:
        raise RuntimeError("No GitHub username configured.")
    username = validate_github_username(username)
    warnings: list[str] = []

    authored_open = _search_prs(f"author:{username} type:pr is:open")
    try:
        review_requested = _search_prs(f"review-requested:{username} type:pr is:open")
    except (RuntimeError, requests.RequestException):
        review_requested = []
        warnings.append("Could not load review requests — check token scopes or rate limits.")

    sections = categorize_inbox(authored_open, review_requested, username=username)
    return sections, warnings


def categorize_inbox(
    authored_open: list[dict[str, Any]],
    review_requested: list[dict[str, Any]],
    *,
    username: str,
) -> dict[str, list[dict[str, Any]]]:
    """Split open PRs into inbox panels (mutually exclusive for authored)."""
    username = validate_github_username(username)
    drafts: list[dict[str, Any]] = []
    waiting: list[dict[str, Any]] = []
    needs_action: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []

    for pr in authored_open:
        if pr.get("isDraft"):
            drafts.append(pr)
            continue
        decision = pr.get("reviewDecision")
        mergeable = pr.get("mergeable")
        if mergeable == "CONFLICTING" or decision == "CHANGES_REQUESTED":
            needs_action.append(pr)
        elif decision == "APPROVED":
            ready.append(pr)
        else:
            waiting.append(pr)

    user_l = username.lower()
    needs_review = [
        pr
        for pr in review_requested
        if ((pr.get("author") or {}).get("login") or "").lower() != user_l
    ]

    return {
        "needs_review": needs_review,
        "needs_team_review": [],  # needs org/team membership; reserved for UI parity
        "drafts": drafts,
        "waiting": waiting,
        "needs_action": needs_action,
        "ready": ready,
    }


def inbox_action_label(pr: dict[str, Any], *, section: str) -> str:
    """Short status label like GitHub's Pulls inbox."""
    if section == "drafts" or pr.get("isDraft"):
        return "Not ready"
    if pr.get("mergeable") == "CONFLICTING":
        return "Merge conflicts"
    decision = pr.get("reviewDecision")
    if decision == "CHANGES_REQUESTED":
        return "Changes requested"
    if decision == "APPROVED":
        return "Approved"
    if decision == "REVIEW_REQUIRED":
        return "Review required"
    if section == "needs_review":
        return "Review requested"
    if section == "waiting":
        return "Waiting"
    if section == "ready":
        return "Ready to merge"
    return pr_status(pr)


def check_summary(pr: dict[str, Any]) -> tuple[str, str]:
    """Return (display, style) for CI checks, e.g. ('9/9', 'green')."""
    commits = (pr.get("commits") or {}).get("nodes") or []
    if not commits:
        return ("—", "#8b9bb0")
    rollup = ((commits[0].get("commit") or {}).get("statusCheckRollup")) or {}
    raw_contexts = rollup.get("contexts") or {}
    if isinstance(raw_contexts, dict):
        contexts = raw_contexts.get("nodes") or []
    else:
        contexts = raw_contexts or []
    if not contexts:
        state = rollup.get("state") or ""
        labels = {
            "SUCCESS": ("✓", "#3dd68c"),
            "FAILURE": ("✗", "#f85149"),
            "PENDING": ("…", "#d29922"),
            "EXPECTED": ("…", "#d29922"),
            "ERROR": ("✗", "#f85149"),
        }
        return labels.get(state, ("—", "#8b9bb0"))

    total = len(contexts)
    passed = 0
    failed = 0
    for ctx in contexts:
        conclusion = ctx.get("conclusion")
        state = ctx.get("state")
        if conclusion in {"SUCCESS", "NEUTRAL", "SKIPPED"} or state == "SUCCESS":
            passed += 1
        elif conclusion in {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"} or state in {
            "FAILURE",
            "ERROR",
        }:
            failed += 1
    text = f"{passed}/{total}"
    if failed:
        return (text, "#f85149")
    if passed == total and total > 0:
        return (text, "#3dd68c")
    return (text, "#d29922")


def get_pr_detail(pr: dict[str, Any]) -> dict[str, Any]:
    """Fetch full PR details; falls back to the list payload on failure."""
    repo = pr.get("repository", {}).get("nameWithOwner") or ""
    if "/" not in repo:
        return pr
    owner, name = repo.split("/", 1)
    try:
        data = _post_graphql(
            _headers(require_token()),
            {
                "query": DETAIL_QUERY,
                "variables": {
                    "owner": owner,
                    "name": name,
                    "number": int(pr["number"]),
                },
            },
        )
        detail = data["data"]["repository"]["pullRequest"]
        return detail or pr
    except Exception:  # noqa: BLE001
        return pr


def pr_status(pr: dict[str, Any]) -> str:
    if pr.get("merged"):
        return "Merged"
    if pr.get("isDraft") and pr.get("state") == "OPEN":
        return "Draft"
    if pr.get("state") == "OPEN":
        return "Open"
    return "Closed"


def pr_loc(pr: dict[str, Any]) -> int:
    return int(pr.get("additions", 0)) + int(pr.get("deletions", 0))


def pr_issue_comments(pr: dict[str, Any]) -> int:
    comments = pr.get("comments")
    if isinstance(comments, dict):
        return int(comments.get("totalCount") or 0)
    return int(comments or 0)


def pr_review_comments(pr: dict[str, Any]) -> int:
    """Inline review comments (code comments), via review threads."""
    threads = pr.get("reviewThreads")
    if not isinstance(threads, dict):
        return 0
    nodes = threads.get("nodes")
    if nodes:
        total = 0
        for thread in nodes:
            comments = (thread or {}).get("comments") or {}
            total += int(comments.get("totalCount") or 0)
        return total
    return int(threads.get("totalCount") or 0)


def pr_comments(pr: dict[str, Any]) -> int:
    """Total comments matching GitHub UI: conversation + inline review."""
    return pr_issue_comments(pr) + pr_review_comments(pr)


def iter_review_comments(pr: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten inline review-thread comments for the details page."""
    out: list[dict[str, Any]] = []
    threads = (pr.get("reviewThreads") or {}).get("nodes") or []
    for thread in threads:
        resolved = bool((thread or {}).get("isResolved"))
        for node in ((thread or {}).get("comments") or {}).get("nodes") or []:
            item = dict(node)
            item["_resolved"] = resolved
            out.append(item)
    return out


def search_prs(prs: list[dict[str, Any]], query: str = "") -> list[dict[str, Any]]:
    needle = query.strip().lower()
    if not needle:
        return list(prs)
    out: list[dict[str, Any]] = []
    for pr in prs:
        st = pr_status(pr)
        hay = " ".join(
            [
                str(pr.get("number", "")),
                pr.get("title") or "",
                pr.get("repository", {}).get("nameWithOwner") or "",
                st,
                (pr.get("author") or {}).get("login") or "",
                pr.get("headRefName") or "",
                pr.get("body") or "",
            ]
        ).lower()
        if needle in hay:
            out.append(pr)
    return out


SORT_MODES = ("loc", "date", "title", "repo", "files", "number")


def sort_prs(prs: list[dict[str, Any]], mode: str, *, reverse: bool = True) -> list[dict[str, Any]]:
    key_map = {
        "loc": pr_loc,
        "date": lambda p: p.get("createdAt") or "",
        "title": lambda p: (p.get("title") or "").lower(),
        "repo": lambda p: (p.get("repository", {}).get("nameWithOwner") or "").lower(),
        "files": lambda p: int(p.get("changedFiles") or 0),
        "number": lambda p: int(p.get("number") or 0),
    }
    key = key_map.get(mode, pr_loc)
    if mode in {"title", "repo"}:
        reverse = False
    return sorted(prs, key=key, reverse=reverse)


def compute_stats(prs: list[dict[str, Any]]) -> dict[str, Any]:
    open_n = merged_n = closed_n = 0
    additions = deletions = files = 0
    repos: Counter[str] = Counter()
    for pr in prs:
        st = pr_status(pr)
        if st in {"Open", "Draft"}:
            open_n += 1
        elif st == "Merged":
            merged_n += 1
        else:
            closed_n += 1
        additions += int(pr.get("additions") or 0)
        deletions += int(pr.get("deletions") or 0)
        files += int(pr.get("changedFiles") or 0)
        repos[pr.get("repository", {}).get("nameWithOwner") or "?"] += 1

    return {
        "total": len(prs),
        "open": open_n,
        "merged": merged_n,
        "closed": closed_n,
        "additions": additions,
        "deletions": deletions,
        "files": files,
        "loc": additions + deletions,
        "repos": repos,
        "top_repos": repos.most_common(15),
        "largest": sorted(prs, key=pr_loc, reverse=True)[:10],
    }


def group_by_repo(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for pr in prs:
        name = pr.get("repository", {}).get("nameWithOwner") or "?"
        url = pr.get("repository", {}).get("url") or f"https://github.com/{name}"
        bucket = buckets.setdefault(
            name,
            {
                "name": name,
                "url": url,
                "total": 0,
                "open": 0,
                "merged": 0,
                "closed": 0,
                "loc": 0,
            },
        )
        bucket["total"] += 1
        st = pr_status(pr)
        if st in {"Open", "Draft"}:
            bucket["open"] += 1
        elif st == "Merged":
            bucket["merged"] += 1
        else:
            bucket["closed"] += 1
        bucket["loc"] += pr_loc(pr)
    return sorted(buckets.values(), key=lambda r: r["total"], reverse=True)
