from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYDRAFETCH_API_KEY", "test-key")
