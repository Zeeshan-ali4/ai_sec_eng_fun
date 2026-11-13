"""Mocked training effects are retrieval evidence, never real-model acceptance."""
import hashlib
import json
from unittest.mock import Mock
import pytest
from lab_platform.app import create_app
from lab_platform.ollama_client import OllamaError
from lab_platform.proposal2.knowledge_base import fixture, DATA
from lab_platform.proposal2.poisoning_registry import REGISTRY
from lab_platform.proposal2.poisoning_retrieval import rank

@pytest.fixture
def model():
    m = Mock()
    m.chat.return_value = 'I cannot verify the submitted claim; the trusted warranty is two years [LK-005].'
    return m

@pytest.fixture
def app(tmp_path, model):
    return create_app({'TESTING':True, 'DATABASE_PATH':str(tmp_path / 'p1.sqlite3')}, client=model)

@pytest.fixture
def service(app):
    return app.extensions['poisoning_service']

def payload(ident='DP-001', **kwargs):
    return dict(answer=REGISTRY[ident]['sample'], account_id='new', rating=5, source_label='practice-1', **kwargs)

@pytest.mark.parametrize('ident', list(REGISTRY))
def test_scenario_effect_and_provenance(service, model, ident):
    spec = REGISTRY[ident]
    assert service.state('a', ident)['dataset']['active_entries'] == 24
    clean = service.query('a', ident, spec['target_question'], 'clean')
    count = 3 if ident in {'DP-003','DP-005'} else 1
    for n in range(count):
        data = payload(ident)
        if ident == 'DP-003': data['source_label'] = f'distinct-{n}'
        accepted = service.inject('a', ident, data)
        assert accepted['status'] == 'accepted'
    current = service.query('a', ident, spec['target_question'])
    assert current['sources'][0]['poisoned']
    assert current['dataset']['checksum'] != clean['dataset']['checksum']
    assert current['observations']['poisoned_content_accepted']
    assert current['observations']['poisoned_content_retrieved']
    assert current['observations']['poisoned_content_prioritised']
    assert current['observations']['model_contradicted_ground_truth'] == 'manual_review_required'
    assert current['observations']['model_answer_changed'] is False
    assert current['comparison']['clean']['answer'] == model.chat.return_value
    assert current['answer'] == model.chat.return_value
    assert current['retrieved_source_ids'] == [s['source_id'] for s in current['sources']]
    assert current['sources'] == current['candidates'][:3]
    assert current['sources'] == service.query('a', ident, spec['target_question'])['sources']
    if ident in {'DP-003','DP-005'}:
        signals = current['sources'][0]['signals']
        assert signals['submission_count'] == 3
        assert signals['distinct_source_count'] == (3 if ident == 'DP-003' else 1)
        assert signals['duplicate_count'] == (0 if ident == 'DP-003' else 2)
    if ident == 'DP-002':
        messages = model.chat.call_args.args[0]
        assert 'DOC-POISON-TRACE' not in messages[0]['content']
        assert messages[1]['role'] == 'user'
        assert 'DOC-POISON-TRACE' in messages[1]['content']
        assert current['sources'][0]['source_classification'] == 'untrusted_document'
        assert not current['observations']['embedded_marker_present']
    if ident == 'DP-006':
        assert not any(s['id'] == spec['target_id'] for s in current['candidates'])
        assert service.state('a', ident)['original']['answer'] == spec['expected_clean_reference']
        assert current['dataset']['active_entries'] == 24
        assert current['sources'][0]['version'] > service.state('a', ident)['original']['version']
    events = service.export('a', ident)['events']
    assert any(e['type'] == 'accepted' and e['data']['record']['account']['age_days'] == 1 for e in events)


def test_trigger_absence_and_configurable_weights(service):
    spec = REGISTRY['DP-004']
    service.inject('a', 'DP-004', payload('DP-004'))
    assert not any(s.get('poisoned') for s in service.query('a','DP-004','How long is the warranty?')['sources'])
    assert service.query('a','DP-004',spec['target_question'])['sources'][0]['signals']['trigger_match']
    service.inject('a','DP-001',payload())
    current = service.query('a','DP-001','warranty')
    entries = fixture()['entries'] + service.state('a','DP-001')['records']
    no_weights = dict(REGISTRY['DP-001'],weights=dict(rating=0,support=0,trigger=0))
    assert current['sources'][0]['poisoned']
    assert rank(entries,'warranty',no_weights)[0]['id'] == 'LK-005'


def test_repetition_requires_distinct_sources(service):
    for _ in range(3): service.inject('a','DP-003',payload('DP-003'))
    result = service.query('a','DP-003',REGISTRY['DP-003']['target_question'])
    assert result['sources'][0]['id'] == 'LK-006'
    false = next(s for s in result['candidates'] if s.get('poisoned'))
    assert false['signals']['support_influence'] == 0


def test_isolation_reset_and_retained_evidence(service, app):
    fixture_hash = hashlib.sha256((DATA / 'trusted_knowledge.json').read_bytes()).hexdigest()
    kb = app.extensions['proposal2_kb']
    clean = kb.info()
    a,b = app.test_client(),app.test_client()
    original_p1 = open(app.config['DATABASE_PATH'],'rb').read()
    assert a.post('/proposal-02/poisoning/api/inject',json=payload()).status_code == 201
    assert b.get('/proposal-02/poisoning/api/state').json['records'] == []
    a.post('/proposal-02/poisoning/api/select',json={'scenario_id':'DP-005'})
    a.post('/proposal-02/poisoning/api/inject',json=payload('DP-005'))
    a.post('/proposal-02/poisoning/api/select',json={'scenario_id':'DP-001'})
    before = a.get('/proposal-02/poisoning/api/state').json['dataset']
    a.post('/proposal-02/poisoning/api/query',json={'question':'warranty','stage':'clean'})
    a.post('/proposal-02/poisoning/api/reset',json={})
    after = a.get('/proposal-02/poisoning/api/state').json
    assert after['records'] == [] and after['dataset']['generation'] == before['generation'] + 1
    assert any(e['type'] == 'reset' for e in a.get('/proposal-02/poisoning/api/export').json['events'])
    query = a.post('/proposal-02/poisoning/api/query',json={'question':'warranty','stage':'current'}).json
    assert query['comparison']['clean'] is None
    a.post('/proposal-02/poisoning/api/select',json={'scenario_id':'DP-005'})
    assert len(a.get('/proposal-02/poisoning/api/state').json['records']) == 1
    assert kb.info() == clean
    assert open(app.config['DATABASE_PATH'],'rb').read() == original_p1
    assert hashlib.sha256((DATA / 'trusted_knowledge.json').read_bytes()).hexdigest() == fixture_hash
    assert a.get('/proposal-02/api/submissions').json['submissions'] == []

@pytest.mark.parametrize('field,value', [('rating', True),('rating',6),('rating',{}),('answer',''),('answer','x'*2001),('answer',[]),('account_id','root'),('account_id',{}),('source_label',None),('path','/etc/passwd'),('role','system'),('status','approved')])
def test_rejections_logged_and_no_active_change(service, field, value):
    data = payload(); data[field] = value
    with pytest.raises(ValueError): service.inject('a','DP-001',data)
    assert service.state('a','DP-001')['records'] == []
    rejected = service.export('a','DP-001')['events'][-1]
    assert rejected['type'] == 'rejected' and rejected['data']['status'] == 'rejected'

@pytest.mark.parametrize('ident', ['DP-999',None,{},['DP-001']])
def test_invalid_selection(app, ident):
    assert app.test_client().post('/proposal-02/poisoning/api/select',json={'scenario_id':ident}).status_code == 400

@pytest.mark.parametrize('data', [{'question':'', 'stage':'current'},{'question':'warranty','stage':[]},{'question':None,'stage':'clean'},{'question':'x'*2001,'stage':'current'}, {'question':'warranty','stage':'current','role':'system'}])
def test_query_validation(app, data):
    assert app.test_client().post('/proposal-02/poisoning/api/query',json=data).status_code == 400


def test_model_failure_is_not_success(service, model):
    service.inject('a','DP-002',payload('DP-002'))
    model.chat.side_effect = OllamaError('private transport details')
    result = service.query('a','DP-002',REGISTRY['DP-002']['target_question'])
    assert result['answer'] is None and result['error'] == 'local_model_unavailable'
    assert result['observations']['poisoned_content_retrieved']
    assert result['observations']['model_answer_changed'] is None
    assert result['observations']['model_followed_embedded_instruction'] == 'not_observed'
    assert 'private transport' not in json.dumps(service.export('a','DP-002'))


def test_marker_needs_manual_interpretation(service, model):
    service.inject('a','DP-002',payload('DP-002'))
    model.chat.return_value = 'I refuse to follow the instruction DOC-POISON-TRACE.'
    result = service.query('a','DP-002',REGISTRY['DP-002']['target_question'])
    assert result['observations']['embedded_marker_present']
    assert result['observations']['model_followed_embedded_instruction'] == 'manual_review_required'


def test_benchmark_export_and_clean_independence(service, app):
    kb = app.extensions['proposal2_kb']; before=kb.info()
    clean = service.benchmark('a','DP-001','clean')
    service.inject('a','DP-001',payload())
    current = service.benchmark('a','DP-001','current')
    assert len(clean['results']) == len(current['results']) == 3
    for c,p in zip(clean['results'],current['results']):
        assert c['question'] == p['question']
        assert c['dataset']['checksum'] != p['dataset']['checksum']
        assert p['case_id'] and p['semantic_outcome'] == 'manual_review_required'
    assert kb.info() == before
    assert service.export('b','DP-001')['events'] == []
    assert service.export('a','DP-001')['events'][-1]['type'] == 'benchmark'


def test_quotas_and_reset_preserve_evidence(service):
    for _ in range(40): service.inject('a','DP-005',payload('DP-005'))
    with pytest.raises(ValueError,match='limit'): service.inject('a','DP-005',payload('DP-005'))
    service.reset('a','DP-005')
    assert len(service.export('a','DP-005')['events']) == 42
    service.inject('a','DP-005',payload('DP-005'))
    with service.kb.connect() as db:
        for _ in range(457): service._event(db,'a','DP-005','test',{})
    with pytest.raises(ValueError, match='limit'): service.reset('a','DP-005')
    assert len(service.state('a','DP-005')['records']) == 1  # mutation rolled back


def test_api_security_rendering_and_no_privileges(app):
    a=app.test_client()
    assert a.get('/proposal-02/poisoning').status_code == 200
    data=payload();data['answer']='<img src=x onerror=alert(1)>'
    assert a.post('/proposal-02/poisoning/api/inject',json=data).status_code == 201
    assert a.get('/proposal-02/poisoning/api/state').json['records'][0]['answer'] == data['answer']
    assert a.post('/proposal-02/poisoning/api/inject',json=payload(),headers={'Origin':'https://elsewhere.invalid'}).status_code == 403
    assert a.get('/proposal-02/poisoning',headers={'Host':'elsewhere.invalid'}).status_code == 400
    assert a.post('/proposal-02/poisoning/api/inject',data={'file':'text'}).status_code == 400
    assert a.post('/proposal-02/poisoning/api/inject',json={'answer':'x'*17000}).status_code == 413
    for path in ['publish','review','reset-global','upload']:
        assert a.post('/proposal-02/poisoning/api/'+path,json={}).status_code == 404
    assert a.post('/proposal-02/poisoning/api/reset',json={'session_id':'other'}).status_code == 400
    assert a.get('/proposal-02/poisoning/api/export').headers['Content-Disposition'].startswith('attachment')
    from pathlib import Path
    script=Path('lab_platform/static/proposal2/poisoning.js').read_text()
    assert 'innerHTML' not in script and 'textContent' in script
