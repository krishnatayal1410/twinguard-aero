import importlib.util
import sqlite3
from pathlib import Path

import pytest


def test_backup_restores_rows_and_refuses_overwrite(tmp_path):
    path = Path(__file__).resolve().parents[2] / "scripts/backup_database.py"
    spec = importlib.util.spec_from_file_location("backup_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = tmp_path / "source.db"
    target = tmp_path / "backup.db"
    with sqlite3.connect(original) as db:
        db.execute("CREATE TABLE evidence (value TEXT)")
        db.execute("INSERT INTO evidence VALUES ('recorded sample')")
    module.backup(f"sqlite:///{original}", target)
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT value FROM evidence").fetchone()[0] == "recorded sample"
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(FileExistsError):
        module.backup(f"sqlite:///{original}", target)
