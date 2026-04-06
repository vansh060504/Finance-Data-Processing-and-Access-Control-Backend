from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import clear_tokens


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "finance_test.db"
    monkeypatch.setenv("FINANCE_DB_PATH", str(db_path))
    clear_tokens()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
