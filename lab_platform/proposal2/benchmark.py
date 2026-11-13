"""Isolated clean runner; retrieval checks are not semantic model grades."""
import json
import re
import tempfile
import uuid
from pathlib import Path
from ..database import utcnow
from .knowledge_base import KnowledgeBase, DATA, event
from .support_service import SupportService
from ..ollama_client import OllamaError


def cases():
    data = json.loads((DATA / 'clean_benchmark.json').read_text(encoding='utf-8'))
    if not isinstance(data, list) or not 15 <= len(data) <= 20:
        raise ValueError('Malformed benchmark fixture.')
    required = {'id', 'question', 'reference_answer', 'expected_behaviour', 'evaluation_criteria', 'category', 'expected_source_ids'}
    if any(set(c) != required for c in data) or len({c['id'] for c in data}) != len(data):
        raise ValueError('Malformed benchmark case.')
    return data


def grounding_flags(answer, sources):
    """Conservative warning signals; absence of flags never means semantic pass."""
    cited = set(re.findall(r'\bL[KS]-[0-9]+\b', answer))
    allowed = {s['id'] for s in sources}
    flags = []
    if cited - allowed:
        flags.append('cites_unretrieved_entry')
    if sources and not cited:
        flags.append('no_entry_citation')
    # Novel numeric claims warrant review, but can be legitimate paraphrases.
    numbers = set(re.findall(r'\b[0-9]+\b', re.sub(r'\bL[KS]-[0-9]+\b', '', answer)))
    reference_numbers = set(re.findall(r'\b[0-9]+\b', ' '.join(s['answer'] for s in sources)))
    if sources and numbers - reference_numbers:
        flags.append('numeric_claim_requires_review')
    return flags


def run(model, config, evidence_kb):
    # A temporary clean database avoids destroying or inheriting the live environment.
    report = dict(started_at=utcnow(), model=config['OLLAMA_MODEL'], options=config['OLLAMA_OPTIONS'], results=[])
    try:
        report['model_health'] = model.health()
    except OllamaError:
        report['model_health'] = dict(available=False)
    with tempfile.TemporaryDirectory(prefix='lumen-benchmark-') as directory:
        kb = KnowledgeBase(Path(directory) / 'clean.sqlite3')
        service = SupportService(kb, model, config)
        report['baseline'] = kb.info()
        for case in cases():
            result = dict(case)
            try:
                observed = service.reply(uuid.uuid4().hex, case['question'])
                ids = [s['source_id'] for s in observed['sources']]
                expected = case['expected_source_ids']
                result.update(observed_answer=observed['reply'], observed_source_ids=ids,
                              retrieved_sources=observed['sources'],
                              retrieval_check=('pass' if (set(expected) <= set(ids) if expected else not ids) else 'fail'),
                              semantic_outcome='manual_review_required',
                              grounding_check='manual_review_required', grounding_flags=grounding_flags(observed['reply'], observed['sources']))
            except OllamaError:
                from .retrieval_service import retrieve
                sources = retrieve(kb.entries(), case['question'])
                result.update(observed_answer=None, observed_source_ids=[s['source_id'] for s in sources], retrieved_sources=sources,
                              retrieval_check=('pass' if (set(case['expected_source_ids']) <= {s['source_id'] for s in sources} if case['expected_source_ids'] else not sources) else 'fail'), semantic_outcome='error', grounding_check='not_scored', grounding_flags=[], error='local_model_unavailable')
            report['results'].append(result)
    report['finished_at'] = utcnow()
    with evidence_kb.connect() as db:
        event(db, 'benchmark', report)
    return report
