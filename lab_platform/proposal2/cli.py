"""Trusted OS-local organiser commands, never invoked by browser or model."""
import argparse
import json
from pathlib import Path
from ..config import settings
from ..ollama_client import OllamaClient
from .knowledge_base import KnowledgeBase
from .ingestion_service import review, publish, submissions
from .benchmark import run

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'runtime' / 'proposal2.sqlite3'

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'report', 'benchmark'):
        sub.add_parser(name)
    r = sub.add_parser('review')
    r.add_argument('id', type=int)
    r.add_argument('--decision', choices=['approved', 'rejected'], required=True)
    p = sub.add_parser('publish')
    p.add_argument('id', type=int)
    sub.add_parser('reset').add_argument('--confirm', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'reset' and not args.confirm:
        parser.error('Stop Flask first; reset requires --confirm. Evidence is retained.')
    kb = KnowledgeBase(DEFAULT_PATH)
    try:
        if args.command == 'status':
            result = kb.info()
        elif args.command == 'review':
            review(kb, args.id, args.decision)
            result = dict(status=args.decision)
        elif args.command == 'publish':
            result = publish(kb, args.id)
        elif args.command == 'reset':
            kb.reset()
            result = kb.info()
        elif args.command == 'benchmark':
            config = settings()
            result = run(OllamaClient(config), config, kb)
        else:
            with kb.connect() as db:
                events = [dict(row, data=json.loads(row['data'])) for row in db.execute('SELECT * FROM p2_events ORDER BY id')]
            result = dict(baseline=kb.info(), knowledge=kb.entries(False), submissions=submissions(kb), events=events)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=True))

if __name__ == '__main__':
    main()
