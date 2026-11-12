"""Local-only instructor operations. Stop Flask before destructive resets."""
import argparse
import json
from .config import settings
from .database import Database, utcnow
from .challenge_service import STATUSES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['report', 'decide', 'reset-sales', 'reset-lab'])
    parser.add_argument('--attempt', type=int)
    parser.add_argument('--decision', choices=STATUSES[1:])
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    if args.command == 'decide' and (not args.attempt or not args.decision):
        parser.error('decide requires --attempt and --decision')
    if args.command.startswith('reset') and not args.confirm:
        parser.error('Destructive reset requires --confirm; stop Flask and archive evidence first.')
    store = Database(settings()['DATABASE_PATH'])
    with store.connect() as db:
        if args.command == 'report':
            print(json.dumps({table: [dict(row) for row in db.execute(f'SELECT * FROM {table}')]
                              for table in ('attempts', 'events', 'interests')}, indent=2, ensure_ascii=False))
        elif args.command == 'decide':
            row = db.execute('SELECT * FROM attempts WHERE id=? AND completed=1', (args.attempt,)).fetchone()
            if row is None:
                parser.error('Completed attempt not found')
            db.execute('UPDATE attempts SET status=? WHERE id=?', (args.decision, args.attempt))
            db.execute('INSERT INTO events(timestamp,session_id,challenge_id,attempt,type,data) VALUES(?,?,?,?,?,?)',
                       (utcnow(), row['session_id'], 'CH-001', row['number'], 'instructor_decision',
                        json.dumps(dict(evidence_id=args.attempt, decision=args.decision))))
        else:
            db.execute('DELETE FROM interests')
            if args.command == 'reset-lab':
                db.execute('DELETE FROM events')
                db.execute('DELETE FROM attempts')


if __name__ == '__main__':
    main()
