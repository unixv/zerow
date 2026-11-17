"""Backup behavior and data-safety regression tests."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "deploy" / "backup.py"
spec = importlib.util.spec_from_file_location("zerow_backup", MODULE)
backup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup_module)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "atrium.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_database_never_creates_empty_backup(self):
        with self.assertRaises(FileNotFoundError):
            backup_module.backup(self.db)
        self.assertFalse(self.db.exists())

    def test_backup_preserves_committed_wal_records(self):
        with sqlite3.connect(self.db) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE users (name TEXT PRIMARY KEY)")
            db.execute("INSERT INTO users VALUES ('alice')")
            db.commit()
            output = backup_module.backup(self.db)
            self.assertTrue(output.is_file())
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with sqlite3.connect(output) as snapshot:
                self.assertEqual(snapshot.execute("SELECT name FROM users").fetchone()[0], "alice")
                self.assertEqual(snapshot.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            db.execute("INSERT INTO users VALUES ('bob')")
            db.commit()
            with sqlite3.connect(output) as snapshot:
                self.assertEqual(snapshot.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_retains_only_latest_seven(self):
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE sample (value INTEGER)")
        results = [backup_module.backup(self.db) for _ in range(9)]
        kept = sorted((self.root / "backups").glob("zerow-*.sqlite3"))
        self.assertEqual(len(kept), 7)
        self.assertFalse(results[0].exists())
        self.assertFalse(results[1].exists())
        self.assertTrue(results[-1].exists())

    def test_invalid_database_does_not_publish_backup(self):
        self.db.write_bytes(b"not a sqlite database")
        with self.assertRaises(sqlite3.DatabaseError):
            backup_module.backup(self.db)
        self.assertFalse(list((self.root / "backups").glob("zerow-*.sqlite3")))


if __name__ == "__main__":
    unittest.main()
