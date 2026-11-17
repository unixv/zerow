#!/usr/bin/env python3
"""Safely back up the live ZeroW SQLite database without stopping the game."""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def backup(db, keep=7):
    db = Path(db)
    if not db.is_file():
        raise FileNotFoundError(f"Database does not exist: {db}")
    dest = db.parent / "backups"
    dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    final = dest / f"zerow-{timestamp}.sqlite3"
    fd, tmp_name = tempfile.mkstemp(prefix=".zerow-", suffix=".tmp", dir=dest)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        # mode=ro prevents sqlite3.connect from silently creating a new empty database.
        with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=20) as source:
            with sqlite3.connect(tmp) as target:
                source.backup(target, pages=128, sleep=0.1)
                result = target.execute("PRAGMA integrity_check").fetchone()
                if not result or result[0] != "ok":
                    raise RuntimeError(f"Backup integrity check failed: {result}")
        tmp.chmod(0o600)
        os.replace(tmp, final)
        # Only prune after the new backup is fully verified and published.
        for old in sorted(dest.glob("zerow-*.sqlite3"), reverse=True)[keep:]:
            old.unlink()
        return final
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        print(backup(os.environ.get("ZEROW_DB", "/opt/zerow/data/atrium.sqlite3")))
    except (OSError, sqlite3.Error, RuntimeError) as exc:
        print(f"ZeroW backup failed: {exc}", file=sys.stderr)
        sys.exit(1)
