import sqlite3
from pathlib import Path
from platformdirs import user_data_dir

DB_PATH = Path(user_data_dir("BugFinder", "BugFinder")) / "bugfinder.sqlite3"

class Database:
    def __init__(self, path=None):
        self.path = Path(path) if path else DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS scans ("
                "id INTEGER PRIMARY KEY, project_path TEXT NOT NULL, "
                "scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "finding_count INTEGER NOT NULL, findings_json TEXT NOT NULL)"
            )

    def connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def save_scan(self, project_path, findings):
        import json
        with self.connect() as db:
            cur = db.execute(
                "INSERT INTO scans(project_path, finding_count, findings_json) VALUES (?, ?, ?)",
                (project_path, len(findings), json.dumps(findings, ensure_ascii=False)),
            )
            return cur.lastrowid

    def recent_scans(self, limit=20):
        with self.connect() as db:
            return db.execute(
                "SELECT id, project_path, scanned_at, finding_count "
                "FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
