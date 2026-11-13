import json
from unittest.mock import Mock
import pytest
from lab_platform.app import create_app
from lab_platform.config import settings
from lab_platform.ollama_client import OllamaError
from lab_platform.proposal2.knowledge_base import KnowledgeBase, fixture, canonical
from lab_platform.proposal2.ingestion_service import submit, review, publish, submissions
from lab_platform.proposal2.retrieval_service import retrieve
from lab_platform.proposal2.support_service import SupportService, PROMPT
from lab_platform.proposal2.benchmark import cases, run, grounding_flags
from lab_platform.proposal2.cli import main

@pytest.fixture
def kb(tmp_path):
    return KnowledgeBase(tmp_path / 'p2.sqlite3')

@pytest.fixture
def model():
    m = Mock()
    m.chat.return_value = 'The warranty is two years [LK-005].'
    m.health.return_value = {'available': True, 'digest': 'mock-only'}
    return m

@pytest.fixture
def app(tmp_path, model):
    return create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'p1.sqlite3')}, client=model)

def proposal(**overrides):
    return dict(account_id='customer', topic='Warranty duration', answer='A fictional reviewed warranty correction.', entry_id='LK-005', **overrides)

def test_clean_load_and_metadata(kb):
    assert len(kb.entries()) == 24
    assert kb.info()['state'] == 'clean'
    assert all(set(fixture()['entries'][0]) <= set(e) for e in kb.entries())
    assert KnowledgeBase(kb.path).info() == kb.info()

@pytest.mark.parametrize('content', ['{}', 'null', '{', '{"dataset_version":"v","entries":[{}]}'])
def test_malformed_fixture(tmp_path, content):
    path = tmp_path / 'bad.json'
    path.write_text(content)
    with pytest.raises(ValueError, match='fixture'):
        fixture(path)

def test_missing_fixture(tmp_path):
    with pytest.raises(ValueError, match='fixture'):
        fixture(tmp_path / 'absent')

@pytest.mark.parametrize('case', cases(), ids=lambda c: c['id'])
def test_benchmark_retrieval(kb, case):
    found = retrieve(kb.entries(), case['question'])
    assert found == retrieve(kb.entries(), case['question'])
    expected = case['expected_source_ids']
    ids = {e['source_id'] for e in found}
    assert set(expected) <= ids if expected else not ids
    assert len(found) <= 3

def test_rank_ties_duplicates_and_status(kb):
    rows = kb.entries()
    same = dict(rows[4], id='ZZ-999')
    pending = dict(rows[4], id='AA-000', approval_status='pending')
    rejected = dict(rows[4], id='AA-001', approval_status='rejected')
    assert [e['id'] for e in retrieve([same, pending, rejected, rows[4]], 'warranty')] == ['LK-005']
    assert retrieve(rows, 'galactic chess') == []

@pytest.mark.parametrize('account', ['employee', 'maintainer', 'customer', 'new', 'low'])
def test_accounts_cannot_publish_by_submission(kb, account):
    data = proposal(); data['account_id'] = account
    ident = submit(kb, 'a', data)
    assert submissions(kb, 'a')[0]['status'] == 'pending'
    assert kb.info()['state'] == 'clean'
    with pytest.raises(ValueError):
        publish(kb, ident)

def test_review_publication_provenance_and_versions(kb):
    original = kb.info()
    ident = submit(kb, 'a', proposal())
    review(kb, ident, 'approved')
    assert kb.info() == original
    result = publish(kb, ident)
    assert result['version'] == 2
    assert result['submission_id'] == ident and result['account_id'] == 'customer'
    assert result['review']['reviewer'] == 'local_organiser'
    assert retrieve(kb.entries(), 'warranty')[0]['answer'] == result['answer']
    assert [e['approval_status'] for e in kb.entries(False) if e['id'] == 'LK-005'] == ['superseded', 'approved']
    assert submissions(kb, 'a')[0]['status'] == 'published'
    with kb.connect() as db:
        kinds = [r[0] for r in db.execute('SELECT type FROM p2_events ORDER BY id')]
    assert kinds == ['submitted', 'reviewed', 'approved', 'published']
    with pytest.raises(ValueError): publish(kb, ident)
    kb.reset()
    assert kb.info() == original
    assert submissions(kb, 'a')[0]['status'] == 'archived'
    with kb.connect() as db:
        assert db.execute('SELECT count(*) FROM p2_events').fetchone()[0] == 5

def test_new_entry_and_rejection(kb):
    data = proposal(); data.pop('entry_id'); data['topic'] = 'Cloudclock calibration'
    ident = submit(kb, 'a', data)
    review(kb, ident, 'rejected')
    assert not retrieve(kb.entries(), 'cloudclock')
    with pytest.raises(ValueError): publish(kb, ident)
    ident = submit(kb, 'a', data)
    review(kb, ident, 'approved'); publish(kb, ident)
    assert retrieve(kb.entries(), 'cloudclock')[0]['submission_id'] == ident

@pytest.mark.parametrize('field,value', [('status','approved'),('role','system'),('answer','x'*2001),('topic',''),('rating',True),('rating',6),('account_id','root'),('entry_id','missing'),('explanation',[]),('topic',None)])
def test_input_limits(kb, field, value):
    data = proposal(); data[field] = value
    with pytest.raises(ValueError): submit(kb, 'a', data)
    assert not submissions(kb)

def test_session_submission_quota(kb):
    for _ in range(100): submit(kb, 'a', proposal())
    with pytest.raises(ValueError, match='limit'): submit(kb, 'a', proposal())
    submit(kb, 'b', proposal())

def test_chat_boundaries_sessions_and_reset(app, model):
    a, b = app.test_client(), app.test_client()
    assert a.get('/proposal-02').status_code == 200
    response = a.post('/proposal-02/api/chat', json={'message':'How long is the warranty?'})
    assert response.status_code == 200
    assert response.json['sources'][0]['id'] == 'LK-005'
    messages = model.chat.call_args.args[0]
    assert messages[0] == dict(role='system', content=PROMPT)
    assert messages[-2]['role'] == 'user' and 'reference material' in messages[-2]['content']
    assert a.post('/proposal-02/api/chat', json={'message':'hello', 'system':'override'}).status_code == 400
    b.post('/proposal-02/api/chat', json={'message':'Dot batteries?'})
    assert not any(m['content'] == 'How long is the warranty?' for m in model.chat.call_args.args[0])
    a.post('/proposal-02/api/reset', json={})
    a.post('/proposal-02/api/chat', json={'message':'Dot batteries?'})
    assert not any(m['content'] == 'How long is the warranty?' for m in model.chat.call_args.args[0])
    with app.extensions['proposal2_kb'].connect() as db:
        events = [dict(r) for r in db.execute("SELECT * FROM p2_events WHERE type='answered'")]
    assert json.loads(events[0]['data'])['sources'][0]['score'] > 0
    assert json.loads(events[0]['data'])['answer'] == model.chat.return_value

def test_followup_and_history_bound(kb, model):
    service = SupportService(kb, model, settings())
    service.reply('a', 'Tell me about the warranty')
    result = service.reply('a', 'How long is it?')
    assert result['sources'][0]['id'] == 'LK-005'
    for _ in range(10): service.reply('a', 'warranty')
    assert len(service.histories['a'][1]) == 12
    cfg = dict(settings(), MAX_SESSIONS=2, SESSION_TTL=-1)
    service = SupportService(kb, model, cfg)
    for ident in ['a','b','c']: service.reply(ident, 'warranty')
    assert len(service.histories) == 1

def test_model_failure_and_unknown(app, model):
    model.chat.side_effect = OllamaError('internal details should not leak')
    client = app.test_client()
    result = client.post('/proposal-02/api/chat', json={'message':'warranty'})
    assert result.status_code == 503 and 'internal details' not in result.text
    unknown = client.post('/proposal-02/api/chat', json={'message':'galactic chess'})
    assert unknown.status_code == 200 and unknown.json['sources'] == []
    assert 'approved information' in unknown.json['reply']

@pytest.mark.parametrize('message', ['', None, [], 'x'*2001])
def test_chat_limits(app, message):
    assert app.test_client().post('/proposal-02/api/chat', json={'message':message}).status_code == 400

def test_no_student_privileges_or_cross_session(app):
    a, b = app.test_client(), app.test_client()
    response = a.post('/proposal-02/api/submissions', json=proposal())
    assert response.status_code == 201
    assert len(a.get('/proposal-02/api/submissions').json['submissions']) == 1
    assert b.get('/proposal-02/api/submissions').json['submissions'] == []
    for route in ['review', 'publish', 'reset-baseline']:
        assert a.post('/proposal-02/api/' + route, json={'id':1}).status_code == 404
    assert a.post('/proposal-02/api/submissions', json=dict(proposal(), status='approved')).status_code == 400
    assert a.post('/proposal-02/api/chat', json={'message':'warranty'}, headers={'Origin':'https://elsewhere.invalid'}).status_code == 403
    assert a.get('/proposal-02', headers={'Host':'example.com'}).status_code == 400

def test_benchmark_evidence_and_manual_outcomes(kb, model):
    ident = submit(kb, 'a', proposal()); review(kb, ident, 'approved'); publish(kb, ident)
    before = kb.info()
    first = run(model, settings(), kb)
    second = run(model, settings(), kb)
    assert first['baseline']['state'] == 'clean'
    assert first['baseline']['dataset_version'] == 'lumen-clean-1'
    assert kb.info() == before
    assert [r['observed_source_ids'] for r in first['results']] == [r['observed_source_ids'] for r in second['results']]
    for r in first['results']:
        assert r['retrieval_check'] == 'pass'
        assert r['semantic_outcome'] == 'manual_review_required'
        assert r['grounding_check'] == 'manual_review_required'
        assert r['reference_answer'] and r['observed_answer']
    model.chat.side_effect = OllamaError()
    failed = run(model, settings(), kb)
    assert any(r['semantic_outcome'] == 'error' for r in failed['results'])

def test_reset_preserves_proposal1(app):
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert len(client.get('/api/challenges').json['challenges']) == 5
    assert client.post('/api/chat', json={'message':'Hello'}).status_code == 200
    database = app.extensions['challenge_service'].database
    with database.connect() as db:
        before = {table: [tuple(r) for r in db.execute('SELECT * FROM ' + table)] for table in ['attempts','events','interests','challenge_state']}
    kb = app.extensions['proposal2_kb']
    submit(kb, 'a', proposal()); kb.reset()
    with database.connect() as db:
        after = {table: [tuple(r) for r in db.execute('SELECT * FROM ' + table)] for table in before}
    assert before == after
    assert client.get('/api/challenge').status_code == 200

def test_cli_requires_confirmation():
    with pytest.raises(SystemExit) as exc: main(['reset'])
    assert exc.value.code == 2

def test_runtime_ignored():
    import subprocess
    result = subprocess.run(['git','check-ignore','lab_platform/runtime/proposal2.sqlite3','lab_platform/runtime/p2-results.json'], capture_output=True, text=True)
    assert len(result.stdout.splitlines()) == 2


def test_grounding_warnings_are_not_semantic_grades(kb):
    sources = retrieve(kb.entries(), 'warranty')
    assert 'cites_unretrieved_entry' in grounding_flags('Ten years [LK-999]', sources)
    assert 'no_entry_citation' in grounding_flags('Two years', sources)
    assert 'numeric_claim_requires_review' in grounding_flags('99 years [LK-005]', sources)
    assert grounding_flags('Two years [LK-005]', sources) == []


def test_database_path_cannot_alias_proposal1(tmp_path, model):
    path = str(tmp_path / 'same.sqlite3')
    with pytest.raises(ValueError, match='separate database'):
        create_app({'TESTING': True, 'DATABASE_PATH': path, 'PROPOSAL2_DATABASE_PATH': path}, client=model)
