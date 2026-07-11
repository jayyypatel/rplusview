"""GitHub GraphQL client for RPlusView."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.github.com/graphql"

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
        additions
        deletions
        changedFiles
        state
        merged
        createdAt
        updatedAt
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
      createdAt
      updatedAt
      mergedAt
      closedAt
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
          url
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
              url
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
    """Resolve GitHub token from env, .env, or saved config."""
    _load_dotenv()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    from rplusview.config import load_config

    saved = (load_config().get("token") or "").strip()
    return saved or None


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
    return (env_user or "").strip() or None


def require_token() -> str:
    token = get_token()
    if not token:
        raise RuntimeError(
            "No GitHub token found. Set GITHUB_TOKEN or enter one in setup."
        )
    return token


def get_credentials() -> tuple[str, str]:
    username = get_username()
    token = require_token()
    if not username:
        raise RuntimeError("No GitHub username configured. Complete setup first.")
    return username, token


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _post_graphql(headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            if response.status_code in {502, 503, 504}:
                last_error = RuntimeError(f"GitHub {response.status_code}")
                continue
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise RuntimeError(data["errors"])
            return data
        except requests.RequestException as exc:
            last_error = exc
    raise RuntimeError(f"GitHub request failed: {last_error}")


def get_prs(author: str | None = None) -> list[dict[str, Any]]:
    username = author or get_username()
    if not username:
        raise RuntimeError("No GitHub username configured.")
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
                    "query": f"author:{username} type:pr",
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
    # Fallback when only thread count is available
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
        if st == "Open":
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
        bucket[st.lower()] += 1
        bucket["loc"] += pr_loc(pr)
    return sorted(buckets.values(), key=lambda r: r["total"], reverse=True)
