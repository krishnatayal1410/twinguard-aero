"""Create and verify a SQLite backup, or a PostgreSQL custom-format dump.

Never overwrites an existing file. Restore verification uses a separate target.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url


def backup(database_url: str, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    url = make_url(database_url)
    try:
        if url.drivername.startswith("sqlite"):
            source = Path(url.database).resolve()
            if not source.is_file():
                raise ValueError("Source database does not exist")
            with (
                sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True) as src,
                sqlite3.connect(output) as dst,
            ):
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Backup integrity check failed")
        else:
            environment = dict(
                os.environ,
                PGPASSWORD=url.password or "",
                PGHOST=url.host or "localhost",
                PGPORT=str(url.port or 5432),
                PGUSER=url.username or "",
                PGDATABASE=url.database or "",
                PGSSLMODE=url.query.get("sslmode", "require"),
            )
            subprocess.run(
                ["pg_dump", "--format=custom", "--file", str(output)],
                env=environment,
                check=True,
                capture_output=True,
            )
            subprocess.run(["pg_restore", "--list", str(output)], check=True, capture_output=True)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    backup(os.environ["DATABASE_URL"], args.output)
    print(f"Verified backup written to {args.output}")
