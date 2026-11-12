"""Evidence collection; only the local CLI can confirm or dismiss violations."""
import json
import secrets
from pathlib import Path
from .challenges.registry import validate
from .security.evaluations import evaluate
from .database import utcnow
from .event_logger import opaque

STATUSES = ('Not evaluated', 'Possible boundary violation — review required',
            'Confirmed violation', 'Boundary maintained')


class ChallengeService:
    def __init__(self, database, logger):
        self.database, self.logger = database, logger

    def start(self, sid, prompt, config, challenge_id="CH-001", mode="vulnerable"):
        validate(challenge_id, mode)
        with self.database.connect() as db:
            number = db.execute('SELECT COALESCE(MAX(number),0)+1 FROM attempts WHERE session_id=?', (opaque(sid),)).fetchone()[0]
            cur = db.execute('INSERT INTO attempts(session_id,number,timestamp,challenge_id,prompt,mode) VALUES(?,?,?,?,?,?)',
                             (opaque(sid), number, utcnow(), challenge_id, prompt, mode))
            self.logger.write(db, sid, 'attempt_started', dict(user_input=prompt, model=config['OLLAMA_MODEL'],
                              generation_settings=config['OLLAMA_OPTIONS']), number)
            return cur.lastrowid, number

    def finish(self, sid, attempt, response=None):
        ident, number = attempt
        with self.database.connect() as db:
            db.execute('UPDATE attempts SET response=?,completed=? WHERE id=?', (response, int(response is not None), ident))
            data = dict(error='model_or_application_failure')
            if response is not None:
                result = dict(db.execute('SELECT evaluation,evaluation_reason,controls FROM attempts WHERE id=?', (ident,)).fetchone())
                # Document snapshot remains in attempts; do not duplicate it in events.
                result['controls'] = {k: v for k, v in json.loads(result['controls']).items() if k != 'document_content'}
                data = dict(assistant_response=response, evidence_id=ident,
                            expected_outcome='Student objective demonstrated', evaluation=result)
            self.logger.write(db, sid, 'attempt_completed' if response is not None else 'attempt_failed', data, number)


    def evidence(self, sid, challenge_id="CH-001", mode="vulnerable"):
        validate(challenge_id, mode)
        with self.database.connect() as db:
            rows = db.execute('SELECT id,number,timestamp,challenge_id,prompt,response,status,completed,submitted,tool_requested,action_executed,mode,evaluation,evaluation_reason,controls FROM attempts WHERE session_id=? AND challenge_id=? AND mode=? ORDER BY id DESC LIMIT 20', (opaque(sid), challenge_id, mode)).fetchall()
            count = db.execute('SELECT COALESCE(MAX(number),0) FROM attempts WHERE session_id=?', (opaque(sid),)).fetchone()[0]
        # Progress includes no response, prompt or protected state.
        with self.database.connect() as db:
            progress = [dict(r) for r in db.execute('SELECT challenge_id,mode,evaluation,COUNT(*) AS attempts FROM attempts WHERE session_id=? GROUP BY challenge_id,mode,evaluation', (opaque(sid),))]
        safe_rows = [dict(r) for r in rows]
        for row in safe_rows:
            if row['challenge_id'] in {'CH-003', 'CH-004'}:
                row['prompt'] = '[Protected challenge transcript: local instructor only]'
                row['response'] = '[Protected challenge transcript: local instructor only]' if row['completed'] else None
        return dict(challenge_id=challenge_id, mode=mode, attempt_count=count, attempts=safe_rows, progress=progress)

    def submit(self, sid, ident):
        with self.database.connect() as db:
            row = db.execute('SELECT * FROM attempts WHERE id=? AND session_id=? AND completed=1', (ident, opaque(sid))).fetchone()
            if row is None:
                raise ValueError('Completed attempt not found for this session.')
            db.execute('UPDATE attempts SET submitted=1 WHERE id=?', (ident,))
            self.logger.write(db, sid, 'review_submitted', dict(evidence_id=ident), row['number'])

    def state(self, sid, challenge_id, mode):
        validate(challenge_id, mode)
        with self.database.connect() as db:
            db.execute('INSERT OR IGNORE INTO challenge_state(session_id,challenge_id,mode,canary,document) VALUES(?,?,?,?,?)',
                       (opaque(sid), challenge_id, mode, 'TRAINING-' + secrets.token_hex(16), self.original_document()))
            return dict(db.execute('SELECT * FROM challenge_state WHERE session_id=? AND challenge_id=? AND mode=?',
                                   (opaque(sid), challenge_id, mode)).fetchone())

    @staticmethod
    def original_document():
        return (Path(__file__).parent / 'data/challenge_documents/support-001.txt').read_text(encoding='utf-8')

    def document(self, sid, mode, content=None):
        state = self.state(sid, 'CH-005', mode)
        if content is not None:
            if not isinstance(content, str) or not content.strip() or len(content) > 2000 or any(ord(c) < 32 and c not in '\n\r\t' for c in content):
                raise ValueError('Document must be nonempty plain text, at most 2000 characters.')
            with self.database.connect() as db:
                db.execute('UPDATE challenge_state SET document=?,revision=revision+1 WHERE session_id=? AND challenge_id=? AND mode=?',
                           (content, opaque(sid), 'CH-005', mode))
            state = self.state(sid, 'CH-005', mode)
        return dict(id='support-001', type='support_ticket', classification='student-controlled', content=state['document'], revision=state['revision'])

    def reset_state(self, sid, challenge_id, mode):
        with self.database.connect() as db:
            db.execute('DELETE FROM challenge_state WHERE session_id=? AND challenge_id=? AND mode=?', (opaque(sid), challenge_id, mode))

    def score(self, sid, attempt, challenge_id, prompt, response, canary, controls):
        with self.database.connect() as db:
            violations = db.execute("SELECT COUNT(*) FROM interests WHERE session_id=? AND attempt=? AND status!='unverified_interest'",
                                    (opaque(sid), attempt[1])).fetchone()[0]
        controls['unauthorised_action_records'] = violations
        result, reason, outcomes = evaluate(challenge_id, prompt, response, canary, controls)
        controls.update(outcomes)
        with self.database.connect() as db:
            db.execute('UPDATE attempts SET evaluation=?,evaluation_reason=?,controls=? WHERE id=?',
                       (result, reason, json.dumps(controls), attempt[0]))
