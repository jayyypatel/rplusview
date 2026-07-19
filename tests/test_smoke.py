"""Smoke tests — keep CI green without live GitHub API calls."""

from __future__ import annotations

import rplusview


def test_version_exposed() -> None:
    assert isinstance(rplusview.__version__, str)
    assert rplusview.__version__


def test_package_importable() -> None:
    import rplusview.app  # noqa: F401
    import rplusview.config  # noqa: F401
    import rplusview.github_client  # noqa: F401
    import rplusview.safe  # noqa: F401
