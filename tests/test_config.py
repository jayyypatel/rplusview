"""Config persistence security tests (phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rplusview import config as config_mod


@pytest.fixture()
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # Clear any cached paths by ensuring functions re-resolve env each call
    yield tmp_path


def test_config_dir_is_private(isolated_config: Path) -> None:
    path = config_mod.config_dir()
    assert path.is_dir()
    mode = path.stat().st_mode & 0o777
    assert mode == 0o700


def test_save_config_file_is_private(isolated_config: Path) -> None:
    config_mod.save_config({"username": "octocat", "token": "ghp_test_token_not_real"})
    path = config_mod.config_path()
    assert path.is_file()
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["username"] == "octocat"
    assert data["token"] == "ghp_test_token_not_real"


def test_set_saved_username_validates(isolated_config: Path) -> None:
    with pytest.raises(ValueError):
        config_mod.set_saved_username("bad user")
    config_mod.set_saved_username("@octocat")
    assert config_mod.get_saved_username() == "octocat"


def test_get_saved_username_ignores_corrupt_value(isolated_config: Path) -> None:
    path = config_mod.config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"username": "evil OR x"}), encoding="utf-8")
    assert config_mod.get_saved_username() is None
