"""Versioned SQLite knowledge and append-only local evidence."""
import hashlib
import json
from pathlib import Path
from ..database import Database, utcnow

DATA = Path(__file__).parent / 'data'

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))

def fixture(path=None):
    try:
        data = json.loads((Path(path) if path else DATA / 'trusted_knowledge.json').read_text(encoding='utf-8'))
        required = {'id', 'topic', 'answer', 'source_id', 'source_classification', 'trust_level', 'version', 'created_at', 'approval_status', 'keywords', 'account_id', 'submission_id'}
        entries = data['entries']
        assert isinstance(data['dataset_version'], str) and data['dataset_version']
        assert isinstance(entries, list) and entries
        assert len({e['id'] for e in entries}) == len(entries)
        assert len({e['source_id'] for e in entries}) == len(entries)
        for e in entries:
            assert set(e) == required
            assert all(isinstance(e[k], str) and e[k].strip() for k in required - {'keywords', 'version', 'submission_id'})
            assert type(e['version']) is int and e['version'] > 0
            assert isinstance(e['keywords'], list) and e['keywords'] and all(isinstance(k, str) and k for k in e['keywords'])
            assert e['approval_status'] == 'approved' and e['trust_level'] == 'trusted'
            assert len(e['topic']) <= 200 and len(e['answer']) <= 2000
        return data
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        raise ValueError('Missing or malformed trusted knowledge fixture.') from exc

def event(db, kind, payload, sid='organiser'):
    db.execute('INSERT INTO p2_events(timestamp,session_id,type,data) VALUES(?,?,?,?)',
               (utcnow(), sid, kind, canonical(payload)))

class KnowledgeBase(Database):
    # Reuse transactional/quota handling, without creating Proposal 1 tables.
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        seed = fixture()  # Validate before mutating the database.
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS p2_entries(id TEXT,version INTEGER,status TEXT,data TEXT NOT NULL,PRIMARY KEY(id,version));
            CREATE TABLE IF NOT EXISTS p2_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS p2_submissions(id INTEGER PRIMARY KEY,session_id TEXT NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS p2_events(id INTEGER PRIMARY KEY,timestamp TEXT NOT NULL,session_id TEXT NOT NULL,type TEXT NOT NULL,data TEXT NOT NULL);
            ''')
            if not db.execute("SELECT 1 FROM p2_meta WHERE key='dataset_version'").fetchone():
                self._seed(db, seed)
        self.path and Path(self.path).chmod(0o600)

    def _seed(self, db, seed):
        db.execute('DELETE FROM p2_entries')
        for e in seed['entries']:
            db.execute('INSERT INTO p2_entries VALUES(?,?,?,?)', (e['id'], e['version'], 'approved', canonical(e)))
        db.execute("INSERT OR REPLACE INTO p2_meta VALUES('dataset_version',?)", (seed['dataset_version'],))

    def entries(self, approved=True):
        with self.connect() as db:
            rows = db.execute('SELECT data,status FROM p2_entries ORDER BY id,version').fetchall()
        return [dict(json.loads(r['data']), approval_status=r['status']) for r in rows if not approved or r['status'] == 'approved']

    def info(self):
        entries = self.entries()
        digest = hashlib.sha256(canonical(entries).encode()).hexdigest()
        seed = fixture()
        clean = entries == sorted(seed['entries'], key=lambda e: (e['id'], e['version']))
        return dict(dataset_version=seed['dataset_version'], checksum=digest, trusted_entries=len(entries), state='clean' if clean else 'modified')

    def reset(self):
        # Stop Flask first. Retain all evidence and original submissions; remove active changes.
        seed = fixture()
        with self.connect() as db:
            event(db, 'reset', dict(policy='Evidence retained; submissions archived; active knowledge restored'))
            db.execute("UPDATE p2_submissions SET status='archived'")
            self._seed(db, seed)
