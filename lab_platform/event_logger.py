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

    def write(self, db, sid, kind, data=None, attempt=None):
        if kind not in EVENT_TYPES:
            raise ValueError('Unknown event type')
        payload = json.dumps(data or {}, ensure_ascii=False)
        if len(payload.encode()) > 40000:
            raise ValueError('Evidence exceeds record limit')
        db.execute('INSERT INTO events(timestamp,session_id,challenge_id,attempt,type,data) VALUES(?,?,?,?,?,?)',
                   (utcnow(), opaque(sid), 'CH-001', attempt, kind, payload))
