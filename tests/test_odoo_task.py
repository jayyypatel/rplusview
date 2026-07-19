"""Tests for Odoo task-XXXX detection and URL helpers."""

from __future__ import annotations

import pytest
from rplusview.odoo_task import (
    extract_task_id,
    is_safe_odoo_url,
    odoo_task_url,
    pr_task_id,
    pr_task_label,
    title_without_task,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("[FIX] task-12345: fix login", "12345"),
        ("task_999 done", "999"),
        ("TASK-42 uppercase", "42"),
        ("no task here", None),
        ("task-", None),
        ("mytask-12", None),
        ("prefix task-7 suffix", "7"),
        ("Closes task-300 in description", "300"),
    ],
)
def test_extract_task_id(text: str, expected: str | None) -> None:
    assert extract_task_id(text) == expected


def test_extract_task_id_first_match_wins() -> None:
    assert extract_task_id("task-1 and task-2", "task-9") == "1"


def test_pr_task_id_from_title_branch_body() -> None:
    assert pr_task_id({"title": "task-100 fix"}) == "100"
    assert pr_task_id({"title": "x", "headRefName": "task-200-branch"}) == "200"
    assert pr_task_id({"title": "x", "body": "Closes task-300"}) == "300"
    assert pr_task_id({"title": "plain"}) is None


def test_pr_task_label() -> None:
    assert pr_task_label({"title": "task-55"}) == "task-55"
    assert pr_task_label({"title": "none"}) == ""


@pytest.mark.parametrize(
    "title,expected",
    [
        ("[FIX] task-12345: fix login", "[FIX] fix login"),
        ("task-99 only", "only"),
        ("task-99", "(no title)"),
        ("plain title", "plain title"),
        ("Fix login (task_42)", "Fix login"),
    ],
)
def test_title_without_task(title: str, expected: str) -> None:
    assert title_without_task(title) == expected


def test_odoo_task_url() -> None:
    assert odoo_task_url("12345") == "https://www.odoo.com/odoo/project.task/12345"
    with pytest.raises(ValueError):
        odoo_task_url("abc")


@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://www.odoo.com/odoo/project.task/123", True),
        ("https://odoo.com/odoo/project.task/123", True),
        ("http://www.odoo.com/odoo/project.task/123", False),
        ("https://evil.com/odoo/project.task/123", False),
        ("https://www.odoo.com/web#id=123&model=project.task", False),
        ("https://www.odoo.com/odoo/res.partner/1", False),
        ("https://www.odoo.com.evil.com/odoo/project.task/1", False),
    ],
)
def test_is_safe_odoo_url(url: str, ok: bool) -> None:
    assert is_safe_odoo_url(url) is ok
