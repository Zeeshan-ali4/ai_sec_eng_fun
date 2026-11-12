"""Local-only configuration; paths never depend on the working directory."""
import os
from pathlib import Path
from urllib.parse import urlsplit

DATA_DIR = Path(__file__).resolve().parents[1] / 'lifecycle&operations_layer/test&evaluation/proposals/proposal-01/demo-data'


def settings():
    address = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    url = urlsplit(address)
    if (url.scheme != 'http' or url.hostname not in {'127.0.0.1', '::1'}
            or url.username or url.password or url.path not in {'', '/'} or url.query or url.fragment):
        raise ValueError('OLLAMA_BASE_URL must be an HTTP loopback address.')
    ctx = int(os.getenv('OLLAMA_NUM_CTX', '8192'))
    if ctx < 8192:
        raise ValueError('OLLAMA_NUM_CTX must be at least 8192 for the catalogue.')
    return dict(DATABASE_PATH=str(Path(__file__).resolve().parent / 'runtime' / 'lab.sqlite3'), OLLAMA_BASE_URL=address.rstrip('/'), OLLAMA_MODEL=os.getenv('OLLAMA_MODEL', 'llama3.1:8b'),
                OLLAMA_TIMEOUT=float(os.getenv('OLLAMA_TIMEOUT', '120')),
                OLLAMA_OPTIONS=dict(temperature=float(os.getenv('OLLAMA_TEMPERATURE', '0')),
                                    seed=int(os.getenv('OLLAMA_SEED', '42')), num_ctx=ctx, num_predict=768),
                MAX_MESSAGE_CHARS=2000, MAX_HISTORY_TURNS=6, MAX_CONTEXT_BYTES=22000,
                MAX_SESSIONS=128, SESSION_TTL=3600)
