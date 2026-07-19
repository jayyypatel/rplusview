"""Detect task-XXXX in PR text and open the matching Odoo project.task."""

from __future__ import annotations

import re
import webbrowser
from typing import Any

from rplusview.safe import is_https_host_url

# Matches task-12345 or task_12345 (case-insensitive, word-boundary).
_TASK_RE = re.compile(r"(?i)\btask[-_](\d+)\b")
_ODOO_HOSTS = frozenset({"odoo.com", "www.odoo.com"})
_ODOO_TASK_PATH = re.compile(r"/odoo/project\.task/\d+")


def extract_task_id(*texts: str | None) -> str | None:
    """Return the first numeric task id found in any text, or None."""
    for text in texts:
        if not text:
            continue
        match = _TASK_RE.search(text)
        if match:
            return match.group(1)
    return None


def pr_task_id(pr: dict[str, Any]) -> str | None:
    """Extract task id from PR title, branch name, or description body."""
    return extract_task_id(
        pr.get("title"),
        pr.get("headRefName"),
        pr.get("body"),
    )


def pr_task_label(pr: dict[str, Any]) -> str:
    """Display label like ``task-12345``, or empty string if none."""
    task_id = pr_task_id(pr)
    return f"task-{task_id}" if task_id else ""


def title_without_task(title: str | None) -> str:
    """Title for the PR table — task ids live in the Task column only."""
    raw = (title or "").strip() or "(no title)"
    cleaned = _TASK_RE.sub(" ", raw)
    # Drop empty wrappers left behind, e.g. "( )" or "[ ]".
    cleaned = re.sub(r"[(\[{]\s*[)\]}]", " ", cleaned)
    cleaned = re.sub(r"\s*[-–—|·:]\s*", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -–—|·:")
    return cleaned or "(no title)"


def odoo_task_url(task_id: str) -> str:
    """Build ``https://www.odoo.com/odoo/project.task/<id>``."""
    clean = str(task_id).strip()
    if not clean.isdigit():
        raise ValueError("Task id must be numeric.")
    return f"https://www.odoo.com/odoo/project.task/{clean}"


def is_safe_odoo_url(url: str) -> bool:
    """True only for https Odoo project.task record URLs."""
    return is_https_host_url(url, _ODOO_HOSTS, path_pattern=_ODOO_TASK_PATH)


def open_odoo_task(task_id: str) -> bool:
    """Open the Odoo task in the browser. Returns True if opened."""
    try:
        url = odoo_task_url(task_id)
    except ValueError:
        return False
    if not is_safe_odoo_url(url):
        return False
    webbrowser.open(url)
    return True
