"""Global pytest fixtures and test environment configuration."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Ensure local test services bypass proxies
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"

# Ensure XDG paths point to a writable temporary directory in sandboxed/CI environments
if "XDG_STATE_HOME" not in os.environ or os.environ["XDG_STATE_HOME"].startswith(
    "/home"
):
    _default_temp = tempfile.gettempdir()
    os.environ["XDG_STATE_HOME"] = os.path.join(_default_temp, "shusha_test_state")
    os.environ["XDG_CONFIG_HOME"] = os.path.join(_default_temp, "shusha_test_config")
    os.environ["XDG_DATA_HOME"] = os.path.join(_default_temp, "shusha_test_data")
    os.environ["XDG_CACHE_HOME"] = os.path.join(_default_temp, "shusha_test_cache")


@pytest.fixture(autouse=True)
def ensure_clean_test_environment(tmp_path: Path) -> Generator[None]:
    """Ensure test runs in an isolated temporary environment."""
    old_state = os.environ.get("XDG_STATE_HOME")
    old_config = os.environ.get("XDG_CONFIG_HOME")
    old_data = os.environ.get("XDG_DATA_HOME")
    old_cache = os.environ.get("XDG_CACHE_HOME")

    state_dir = tmp_path / "state"
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    cache_dir = tmp_path / "cache"

    state_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    os.environ["XDG_STATE_HOME"] = str(state_dir)
    os.environ["XDG_CONFIG_HOME"] = str(config_dir)
    os.environ["XDG_DATA_HOME"] = str(data_dir)
    os.environ["XDG_CACHE_HOME"] = str(cache_dir)

    yield

    if old_state is not None:
        os.environ["XDG_STATE_HOME"] = old_state
    if old_config is not None:
        os.environ["XDG_CONFIG_HOME"] = old_config
    if old_data is not None:
        os.environ["XDG_DATA_HOME"] = old_data
    if old_cache is not None:
        os.environ["XDG_CACHE_HOME"] = old_cache


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Provide a dedicated temporary workspace path."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace
