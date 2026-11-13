"""Explicit local review followed by publication; no HTTP authority."""
import json
from ..database import utcnow
from .accounts import accounts
from .knowledge_base import canonical, event

def submit(kb, sid, data):
    allowed = {'account_id', 'entry_id', 'topic', 'answer', 'explanation', 'rating'}
    if not isinstance(data, dict) or set(data) - allowed or not {'account_id', 'topic', 'answer'} <= set(data):
        raise ValueError('Send account_id, topic, answer and optional entry_id, explanation, rating only.')
    for key, limit in [('account_id', 40), ('entry_id', 40), ('topic', 200), ('answer', 2000), ('explanation', 1000)]:
        value = data.get(key, '')
        if not isinstance(value, str) or len(value) > limit or (key in {'account_id', 'topic', 'answer'} and not value.strip()):
            raise ValueError('Invalid or oversized submission field: ' + key)
    account = next((a for a in accounts() if a['id'] == data['account_id']), None)
    if not account:
        raise ValueError('Choose a fictional account.')
    if data.get('rating') is not None and (type(data['rating']) is not int or not 1 <= data['rating'] <= 5):
        raise ValueError('Rating must be an integer from 1 to 5.')
    record = dict(data, account=account, timestamp=utcnow(), source_classification='student_proposal', trust_level='untrusted')
    with kb.connect() as db:
        if data.get('entry_id') and not db.execute("SELECT 1 FROM p2_entries WHERE id=? AND status='approved'", (data['entry_id'],)).fetchone():
            raise ValueError('Correction target must be an active entry.')
        count = db.execute('SELECT count(*) FROM p2_submissions WHERE session_id=?', (sid,)).fetchone()[0]
        if count >= 100:
            raise ValueError('Session submission limit reached (100).')
        ident = db.execute("INSERT INTO p2_submissions(session_id,status,data) VALUES(?,'pending',?)", (sid, canonical(record))).lastrowid
        event(db, 'submitted', dict(id=ident, **record), sid)
    return ident

def submissions(kb, sid=None):
    with kb.connect() as db:
        rows = db.execute('SELECT * FROM p2_submissions' + (' WHERE session_id=?' if sid else '') + ' ORDER BY id', (sid,) if sid else ()).fetchall()
    return [dict(id=r['id'], status=r['status'], **json.loads(r['data'])) for r in rows]

def review(kb, ident, decision):
    if decision not in {'approved', 'rejected'}:
        raise ValueError('Review decision must be approved or rejected.')
    with kb.connect() as db:
        row = db.execute('SELECT * FROM p2_submissions WHERE id=?', (ident,)).fetchone()
        if not row or row['status'] != 'pending':
            raise ValueError('Only pending submissions can be reviewed.')
        record = json.loads(row['data'])
        record['review'] = dict(decision=decision, reviewer='local_organiser', timestamp=utcnow())
        event(db, 'reviewed', dict(id=ident, **record['review']))
        db.execute('UPDATE p2_submissions SET status=?,data=? WHERE id=?', (decision, canonical(record), ident))
        event(db, decision, dict(id=ident))

def publish(kb, ident):
    with kb.connect() as db:
        row = db.execute('SELECT * FROM p2_submissions WHERE id=?', (ident,)).fetchone()
        if not row or row['status'] != 'approved':
            raise ValueError('Only explicitly approved submissions can be published.')
        record = json.loads(row['data'])
        target = record.get('entry_id') or f'LS-{ident:06}'
        version = db.execute('SELECT COALESCE(MAX(version),0)+1 FROM p2_entries WHERE id=?', (target,)).fetchone()[0]
        if record.get('entry_id') and not db.execute("SELECT 1 FROM p2_entries WHERE id=? AND status='approved'", (target,)).fetchone():
            raise ValueError('Correction target is no longer active; review a new submission.')
        db.execute("UPDATE p2_entries SET status='superseded' WHERE id=? AND status='approved'", (target,))
        entry = dict(id=target, version=version, topic=record['topic'], answer=record['answer'], keywords=record['topic'].lower().split(), source_id=f'LUMEN-SUB-{ident}', source_classification='organiser_reviewed', trust_level='trusted', created_at=utcnow(), approval_status='approved', account_id=record['account_id'], submission_id=ident, review=record['review'])
        db.execute('INSERT INTO p2_entries VALUES(?,?,?,?)', (target, version, 'approved', canonical(entry)))
        db.execute("UPDATE p2_submissions SET status='published' WHERE id=?", (ident,))
        event(db, 'published', entry)
    return entry
