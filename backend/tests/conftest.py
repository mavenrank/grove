from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("GROVE_DATA_DIR", tempfile.mkdtemp(prefix="grove-test-"))

from fastapi.testclient import TestClient  # noqa: E402

from app import db as dbmod  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.security import reset_rate_limits  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_rate_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def fresh_db():
    """Point the Database singleton at a fresh temp file and rebuild it."""
    tmp = Path(tempfile.mkdtemp(prefix="grove-test-")) / "grove.db"
    old_path = dbmod.db.path
    dbmod.db.path = tmp
    dbmod.db.__init__(tmp)
    yield tmp
    dbmod.db.path = old_path
    dbmod.db.__init__(old_path)


@pytest.fixture()
def session_factory(client, fresh_db):
    def make(count: int = 5):
        resp = client.post("/api/test-sessions", json={"question_count": count})
        assert resp.status_code == 201, resp.text
        return resp.json()
    return make
