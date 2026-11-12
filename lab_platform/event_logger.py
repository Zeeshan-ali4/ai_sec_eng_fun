"""Only explicitly supplied lab evidence is persisted; never requests/config/tracebacks."""
import hashlib
import json
from .database import utcnow

EVENT_TYPES = {'attempt_started', 'attempt_completed', 'attempt_failed', 'tool_requested',
               'tool_completed', 'tool_rejected', 'conversation_reset', 'challenge_reset',
               'review_submitted', 'instructor_decision'}


def opaque(sid):
    return hashlib.sha256(sid.encode()).hexdigest()


class EventLogger:
    def __init__(self, database):
        self.database = database

    def write(self, db, sid, kind, data=None, attempt=None, challenge_id="CH-001", mode="vulnerable"):
        if kind not in EVENT_TYPES:
            raise ValueError('Unknown event type')
        payload = json.dumps(data or {}, ensure_ascii=False)
        if len(payload.encode()) > 40000:
            raise ValueError('Evidence exceeds record limit')
        row = db.execute('SELECT challenge_id,mode FROM attempts WHERE session_id=? AND number=?', (opaque(sid), attempt)).fetchone() if attempt else None
        db.execute('INSERT INTO events(timestamp,session_id,challenge_id,attempt,type,data,mode) VALUES(?,?,?,?,?,?,?)',
                   (utcnow(), opaque(sid), row['challenge_id'] if row else challenge_id, attempt, kind, payload, row['mode'] if row else mode))
