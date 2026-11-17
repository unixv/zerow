#!/usr/bin/env python3
"""Consistent online backup, keeping 7 daily snapshots on the Pi."""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

db = Path(os.environ.get("ZEROW_DB", "/opt/zerow/data/atrium.sqlite3"))
dest = db.parent / "backups"
dest.mkdir(parents=True, exist_ok=True)
path = dest / ("zerow-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".sqlite3")
with sqlite3.connect(db) as source, sqlite3.connect(path) as target:
    source.backup(target)
path.chmod(0o600)
for old in sorted(dest.glob("zerow-*.sqlite3"), reverse=True)[7:]:
    old.unlink()
print(path)
