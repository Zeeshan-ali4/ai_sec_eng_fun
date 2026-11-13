"""Synthetic identities are labels, never authorisation credentials."""
import json
from .knowledge_base import DATA

def accounts():
    return json.loads((DATA / 'fictional_accounts.json').read_text(encoding='utf-8'))
