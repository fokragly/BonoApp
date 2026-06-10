import pytest
from pathlib import Path


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    import app.config as config
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    from app.database import init_db
    init_db()
    return tmp_path / "test.db"
