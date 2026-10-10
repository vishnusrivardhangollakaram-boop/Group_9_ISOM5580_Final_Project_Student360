"""Shared, server-only request inbox for a single Streamlit app instance.

SQLite is intentionally local: see README for Community Cloud persistence limits.
Each browser gets only its own capability URL; school access unlocks the inbox.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import secrets
import sqlite3
import time
import uuid


class CaseStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY, public_token TEXT UNIQUE NOT NULL,
                created REAL NOT NULL, updated REAL NOT NULL,
                phase TEXT NOT NULL, payload TEXT NOT NULL,
                lease_owner TEXT NOT NULL DEFAULT '', lease_until REAL NOT NULL DEFAULT 0
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS cases_updated ON cases(updated DESC)')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path), timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, question: str, language: str, student: str) -> dict:
        now = time.time()
        case = {
            'id': uuid.uuid4().hex, 'public_token': secrets.token_urlsafe(32),
            'created': now, 'updated': now, 'phase': 'created',
            'question': question, 'report_language': language, 'student': student,
            'user': 'student360-' + uuid.uuid4().hex,
            'run_id': '', 'task_id': '', 'form_token': '', 'form': None,
            'review_kind': '', 'report': '', 'outputs': {}, 'metadata': {},
            'events': [], 'review_history': [], 'error': '', 'last_checked': 0,
            'error_status': None, 'error_code': '',
        }
        with self.connection() as db:
            db.execute('INSERT INTO cases(id,public_token,created,updated,phase,payload) VALUES(?,?,?,?,?,?)',
                       (case['id'], case['public_token'], now, now, case['phase'], json.dumps(case, ensure_ascii=False)))
        return case

    def get(self, case_id: str) -> dict | None:
        with self.connection() as db:
            row = db.execute('SELECT payload FROM cases WHERE id=?', (case_id,)).fetchone()
        return json.loads(row['payload']) if row else None

    def get_public(self, token: str) -> dict | None:
        if len(token) > 128:
            return None
        with self.connection() as db:
            row = db.execute('SELECT payload FROM cases WHERE public_token=?', (token,)).fetchone()
        return json.loads(row['payload']) if row else None

    def list(self, limit: int = 200) -> list[dict]:
        with self.connection() as db:
            rows = db.execute('SELECT payload FROM cases ORDER BY updated DESC LIMIT ?', (limit,)).fetchall()
        return [json.loads(row['payload']) for row in rows]

    def acquire(self, case_id: str, seconds: int = 600) -> str | None:
        owner = uuid.uuid4().hex
        with self.connection() as db:
            result = db.execute('UPDATE cases SET lease_owner=?,lease_until=? WHERE id=? AND lease_until<?',
                                (owner, time.time() + seconds, case_id, time.time()))
        return owner if result.rowcount == 1 else None

    def save(self, case: dict, owner: str) -> bool:
        case['updated'] = time.time()
        with self.connection() as db:
            result = db.execute('UPDATE cases SET payload=?,phase=?,updated=?,lease_until=? WHERE id=? AND lease_owner=?',
                                (json.dumps(case, ensure_ascii=False), case['phase'], case['updated'],
                                 time.time() + 600, case['id'], owner))
        return result.rowcount == 1

    def release(self, case_id: str, owner: str):
        with self.connection() as db:
            db.execute("UPDATE cases SET lease_owner='',lease_until=0 WHERE id=? AND lease_owner=?", (case_id, owner))

    def busy(self, case_id: str) -> bool:
        with self.connection() as db:
            row = db.execute('SELECT lease_until FROM cases WHERE id=?', (case_id,)).fetchone()
        return bool(row and row['lease_until'] > time.time())
