"""Local transactional store. Hard page quota fails closed; no silent evidence eviction."""
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, session_id TEXT NOT NULL,
                    challenge_id TEXT NOT NULL, attempt INTEGER, type TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL, challenge_id TEXT NOT NULL, prompt TEXT NOT NULL,
                    response TEXT, status TEXT NOT NULL DEFAULT 'Not evaluated',
                    completed INTEGER NOT NULL DEFAULT 0, submitted INTEGER NOT NULL DEFAULT 0,
                    tool_requested INTEGER NOT NULL DEFAULT 0, action_executed INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS interests (
                    reference TEXT PRIMARY KEY, timestamp TEXT NOT NULL, session_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL, customer_alias TEXT NOT NULL, contact_preference TEXT NOT NULL,
                    vehicle_id TEXT NOT NULL, enquiry TEXT NOT NULL, status TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS session_attempts ON attempts(session_id, id);
            ''')

            # Additive, idempotent migration preserves all Milestone 2 evidence.
            for table, name, definition in [
                ('attempts', 'mode', "TEXT NOT NULL DEFAULT 'vulnerable'"),
                ('attempts', 'evaluation', "TEXT NOT NULL DEFAULT 'Not evaluated'"),
                ('attempts', 'evaluation_reason', "TEXT NOT NULL DEFAULT ''"),
                ('attempts', 'controls', "TEXT NOT NULL DEFAULT '{}'"),
                ('events', 'mode', "TEXT NOT NULL DEFAULT 'vulnerable'")]:
                columns = {row['name'] for row in db.execute(f'PRAGMA table_info({table})')}
                if name not in columns:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
            db.executescript("""
                CREATE TABLE IF NOT EXISTS challenge_state (
                    session_id TEXT NOT NULL, challenge_id TEXT NOT NULL, mode TEXT NOT NULL,
                    canary TEXT NOT NULL, document TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(session_id, challenge_id, mode));
                PRAGMA user_version=3;
            """)

        os.chmod(self.path, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA max_page_count=16384')  # ~64 MiB at default page size
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
