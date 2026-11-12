"""Evidence collection; only the local CLI can confirm or dismiss violations."""
from .database import utcnow
from .event_logger import opaque

STATUSES = ('Not evaluated', 'Possible boundary violation — review required',
            'Confirmed violation', 'Boundary maintained')


class ChallengeService:
    def __init__(self, database, logger):
        self.database, self.logger = database, logger

    def start(self, sid, prompt, config):
        with self.database.connect() as db:
            number = db.execute('SELECT COALESCE(MAX(number),0)+1 FROM attempts WHERE session_id=?', (opaque(sid),)).fetchone()[0]
            cur = db.execute('INSERT INTO attempts(session_id,number,timestamp,challenge_id,prompt) VALUES(?,?,?,?,?)',
                             (opaque(sid), number, utcnow(), 'CH-001', prompt))
            self.logger.write(db, sid, 'attempt_started', dict(user_input=prompt, model=config['OLLAMA_MODEL'],
                              generation_settings=config['OLLAMA_OPTIONS']), number)
            return cur.lastrowid, number

    def finish(self, sid, attempt, response=None):
        ident, number = attempt
        with self.database.connect() as db:
            db.execute('UPDATE attempts SET response=?,completed=? WHERE id=?', (response, int(response is not None), ident))
            self.logger.write(db, sid, 'attempt_completed' if response is not None else 'attempt_failed',
                              dict(assistant_response=response) if response is not None else dict(error='model_or_application_failure'), number)

    def evidence(self, sid):
        with self.database.connect() as db:
            rows = db.execute('SELECT id,number,timestamp,challenge_id,prompt,response,status,completed,submitted,tool_requested,action_executed FROM attempts WHERE session_id=? ORDER BY id DESC LIMIT 20', (opaque(sid),)).fetchall()
            count = db.execute('SELECT COALESCE(MAX(number),0) FROM attempts WHERE session_id=?', (opaque(sid),)).fetchone()[0]
        return dict(challenge_id='CH-001', attempt_count=count, attempts=[dict(r) for r in rows])

    def submit(self, sid, ident):
        with self.database.connect() as db:
            row = db.execute('SELECT * FROM attempts WHERE id=? AND session_id=? AND completed=1', (ident, opaque(sid))).fetchone()
            if row is None:
                raise ValueError('Completed attempt not found for this session.')
            db.execute('UPDATE attempts SET submitted=1 WHERE id=?', (ident,))
            self.logger.write(db, sid, 'review_submitted', dict(evidence_id=ident), row['number'])
