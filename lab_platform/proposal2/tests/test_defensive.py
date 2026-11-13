"""Mocked security boundaries; these tests make no claims about real Ollama semantics."""
import hashlib
import json
from unittest.mock import Mock
import pytest
from lab_platform.app import create_app
from lab_platform.config import settings
from lab_platform.ollama_client import OllamaError
from lab_platform.proposal2.defensive_service import DefensiveService, checksum
from lab_platform.proposal2.poisoning_service import PoisoningService
from lab_platform.proposal2.knowledge_base import KnowledgeBase, fixture, DATA, canonical
from lab_platform.proposal2.poisoning_registry import REGISTRY
from lab_platform.proposal2.benchmark import cases
from lab_platform.proposal2 import cli


@pytest.fixture
def model():
    client = Mock()
    client.chat.return_value = 'Mocked support response, not real-model acceptance.'
    return client


@pytest.fixture
def app(tmp_path, model):
    return create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'p1.sqlite3')}, client=model)


@pytest.fixture
def hardened(app):
    return app.extensions['defensive_service']


def payload(ident='DP-001', **changes):
    return dict(dict(answer=REGISTRY[ident]['sample'], account_id='new', rating=5, source_label='practice-1'), **changes)


def accepted(service, ident='DP-001', **changes):
    return service.inject('a', ident, payload(ident, **changes))['record']['submission_id']


def publish(service, ident, submission):
    service.review('a', ident, submission, 'approved', 'Local fictional fact review completed.')
    return service.publish('a', ident, submission)


@pytest.mark.parametrize('ident', REGISTRY)
def test_same_attack_preserves_weak_mode_but_never_enters_hardened_context(app, hardened, model, ident):
    weak = app.extensions['poisoning_service']
    original = hardened.state('a', ident)['dataset']['checksum']
    for number in range(3):
        data = payload(ident, source_label=f'source-{number}' if ident == 'DP-003' else 'same-source')
        assert weak.inject('a', ident, data)['status'] == 'accepted'
        result = hardened.inject('a', ident, data)
        assert result['status'] == 'quarantined'
        assert result['record']['submitted_payload'] == data
    bad = weak.query('a', ident, REGISTRY[ident]['target_question'])
    assert bad['sources'][0]['poisoned']
    good = hardened.query('a', ident, REGISTRY[ident]['target_question'])
    assert good['dataset']['checksum'] == original
    assert good['sources'][0]['id'] == REGISTRY[ident]['target_id']
    assert all(s['trust_level'] == 'trusted' for s in good['sources'])
    assert good['observations']['untrusted_content_quarantined']
    assert not good['observations']['untrusted_data_supplied_to_model']
    assert not good['observations']['unverified_ratings_influencing_ranking']
    assert not good['observations']['trigger_based_retrieval_manipulation']
    assert not good['observations']['duplicate_records_counted_independently']
    assert good['observations']['model_contradicted_ground_truth'] == 'manual_review_required'
    assert len(good['excluded_candidates']) >= 3
    supplied = json.loads(model.chat.call_args.args[0][1]['content'].split('\n', 1)[1])
    assert supplied == good['sources']
    assert len(supplied) <= 3
    assert all(s['approval_status'] == 'approved' for s in supplied)
    if ident == 'DP-002':
        assert 'DOC-POISON-TRACE' not in json.dumps(model.chat.call_args.args[0])
    if ident == 'DP-004':
        assert any(e.get('trigger_match') for e in good['excluded_candidates'])
        assert hardened.query('a', ident, 'How long is the warranty?')['sources'] == good['sources']


@pytest.mark.parametrize('case', cases(), ids=lambda c: c['id'])
def test_all_clean_benchmark_questions_retain_expected_sources(hardened, case):
    result = hardened.query('a', 'DP-001', case['question'])
    ids = set(result['retrieved_source_ids'])
    assert set(case['expected_source_ids']) <= ids if case['expected_source_ids'] else not ids
    assert result['sources'] == hardened.query('a', 'DP-001', case['question'])['sources']


@pytest.mark.parametrize('account', ['new', 'low', 'customer', 'employee', 'maintainer'])
def test_account_selection_never_authenticates(hardened, account):
    submission = accepted(hardened, account_id=account)
    record = hardened.state('a', 'DP-001')['records'][0]
    assert record['source_trust_decision'] == 'unverified'
    assert record['influence_limit'] == 0
    assert record['account']['id'] == account
    with pytest.raises(ValueError, match='approval'):
        hardened.publish('a', 'DP-001', submission)
    assert hardened.state('a', 'DP-001')['dataset']['active_entries'] == 24


@pytest.mark.parametrize('field,value', [('trust_level','trusted'),('source_classification','organiser_reviewed'),('review', {'decision':'approved'}),('role','system'),('session_id','b'),('approval_status','approved'),('mode','vulnerable'),('rating',True),('rating',6),('answer','x'*2001),('source_label',{}),('account_id','root')])
def test_forgery_and_malformed_submissions_are_rejected_with_evidence(hardened, field, value):
    with pytest.raises(ValueError): hardened.inject('a', 'DP-001', payload(**{field:value}))
    assert not hardened.state('a', 'DP-001')['records']
    event = hardened.export('a', 'DP-001')['events'][-1]
    assert event['type'] == 'rejected' and event['data']['validation_decision'] == 'invalid'


def test_canonical_identity_distinguishes_duplicate_and_repetition(hardened):
    first = accepted(hardened, 'DP-005', answer='  Unused PRODUCTS: 90 days. ', source_label=' Same ')
    second = accepted(hardened, 'DP-005', answer='unused  products: 90 DAYS.', source_label='ＳＡＭＥ', account_id='maintainer')
    third = accepted(hardened, 'DP-005', answer='unused products: 90 days.', source_label='other')
    rows = hardened.state('a', 'DP-005')['records']
    assert rows[1]['duplicate_of'] == first
    assert rows[1]['duplicate_status'] == 'exact_duplicate'
    assert rows[2]['duplicate_of'] is None
    assert rows[2]['duplicate_status'] == 'repeated_claim'
    with pytest.raises(ValueError, match='duplicate'): hardened.review('a','DP-005',second,'approved','Verified locally')
    publish(hardened, 'DP-005', first)
    hardened.review('a','DP-005',third,'approved','Verified locally')
    with pytest.raises(ValueError, match='duplicate'): hardened.publish('a','DP-005',third)


@pytest.mark.parametrize('ident', ['DP-001','DP-002','DP-006'])
def test_benign_review_publish_recovery_is_selective_and_auditable(hardened, ident):
    before = hardened.state('a', ident)['dataset']
    submission = accepted(hardened, ident, answer='Fictional support reminder: consult the approved printed guide.')
    hardened.review('a', ident, submission, 'approved', 'Benign fictional support reminder reviewed locally.')
    assert hardened.state('a', ident)['dataset']['checksum'] == before['checksum']
    assert not any(s['source_classification'] == 'organiser_reviewed' for s in hardened.query('a', ident, REGISTRY[ident]['target_question'])['sources'])
    result = hardened.publish('a', ident, submission)
    assert result['dataset']['checksum'] != before['checksum']
    question = 'Lumen Hub setup' if ident == 'DP-002' else REGISTRY[ident]['target_question']
    active = hardened.query('a', ident, question)
    reviewed = next(s for s in active['sources'] if s['source_classification'] == 'organiser_reviewed')
    assert reviewed['review']['reviewer'] == 'local_organiser'
    assert reviewed['trust_level'] == 'trusted'
    if ident == 'DP-006':
        assert reviewed['id'] == 'LK-005' and reviewed['version'] == 2
        assert active['observations']['approved_corrections_published']
        assert result['record']['publication']['previous']['answer'] == REGISTRY[ident]['expected_clean_reference']
    with pytest.raises(ValueError): hardened.publish('a',ident,submission)
    recovered = hardened.quarantine('a', ident, submission)
    assert recovered['quarantine_completed']
    assert recovered['after']['checksum'] == before['checksum']
    assert recovered['quarantined_submission'] == submission
    query = hardened.query('a', ident, REGISTRY[ident]['target_question'])
    assert query['stage'] == 'recovered'
    assert query['observations']['expected_trusted_source_retrieved']
    assert all(s['source_classification'] != 'organiser_reviewed' for s in query['sources'])
    events = hardened.export('a', ident)['events']
    assert {'quarantined','review','publication','quarantine','query'} <= {e['type'] for e in events}
    assert hardened.state('a',ident)['records'][0]['disposition'] == 'quarantined'
    with pytest.raises(ValueError): hardened.publish('a',ident,submission)


def test_rejection_and_stale_correction_require_fresh_review(hardened):
    rejected = accepted(hardened)
    hardened.review('a','DP-001',rejected,'rejected','Conflicts with original policy.')
    with pytest.raises(ValueError): hardened.publish('a','DP-001',rejected)
    assert hardened.state('a','DP-001')['records'][0]['disposition'] == 'rejected'
    a = accepted(hardened,'DP-006',answer='First reviewed fictional correction')
    b = accepted(hardened,'DP-006',answer='Second reviewed fictional correction')
    for submission in (a,b): hardened.review('a','DP-006',submission,'approved','Local review of original version.')
    hardened.publish('a','DP-006',a)
    with pytest.raises(ValueError, match='changed since review'): hardened.publish('a','DP-006',b)
    assert hardened.query('a','DP-006','warranty')['sources'][0]['answer'] == 'First reviewed fictional correction'


def test_selected_previous_snapshot_restores_versions_and_preserves_incident(hardened):
    a = accepted(hardened,'DP-006',answer='First benign fictional correction')
    publish(hardened,'DP-006',a)
    version2 = hardened.state('a','DP-006')['dataset']
    b = accepted(hardened,'DP-006',answer='Later fictional correction for recovery exercise')
    publish(hardened,'DP-006',b)
    result = hardened.rollback('a','DP-006',2)
    assert result['after']['checksum'] == version2['checksum']
    assert result['revoked_submissions'] == [b]
    assert hardened.query('a','DP-006','warranty')['sources'][0]['answer'] == 'First benign fictional correction'
    rows = hardened.state('a','DP-006')['records']
    assert rows[0]['disposition'] == 'published' and rows[1]['disposition'] == 'quarantined'
    assert len(hardened.state('a','DP-006')['snapshots']) == 4


def test_integrity_failures_and_quota_fail_closed(hardened):
    submission = accepted(hardened,answer='Benign fictional reminder')
    publish(hardened,'DP-001',submission)
    before = hardened.state('a','DP-001')
    with hardened.kb.connect() as db:
        state = hardened._state(db,'a','DP-001')
        state['snapshots'][0]['checksum'] = 'tampered'
        hardened._save(db,'a','DP-001',state)
    with pytest.raises(ValueError, match='integrity'): hardened.rollback('a','DP-001',1)
    assert hardened.state('a','DP-001')['dataset'] == before['dataset']
    for version in [999, '1', True, 2]:
        with pytest.raises(ValueError): hardened.rollback('a','DP-001',version)
    with hardened.kb.connect() as db:
        count = db.execute('SELECT count(*) FROM p2_defensive_events').fetchone()[0]
        for _ in range(500-count): hardened._event(db,'a','DP-001','quota',{})
    with pytest.raises(ValueError,match='limit'): hardened.reset('a','DP-001')
    assert hardened.state('a','DP-001')['dataset'] == before['dataset']


def test_isolation_reset_and_legacy_migration(tmp_path, model):
    kb = KnowledgeBase(tmp_path/'migration.sqlite3')
    legacy = PoisoningService(kb,model,settings())
    legacy.inject('old-session','DP-001',payload())
    legacy.query('old-session','DP-001','warranty')
    with kb.connect() as db:
        # Materialise the historical Milestone 5 JSON shape, without new fields.
        row = db.execute('SELECT data FROM p2_poison_state').fetchone()
        old_state = json.loads(row[0])
        for record in old_state['records']: record.pop('original_source_label', None)
        db.execute('UPDATE p2_poison_state SET data=?', (canonical(old_state),))
        for event in db.execute('SELECT id,data FROM p2_poison_events').fetchall():
            old_event = json.loads(event['data'])
            for key in ['mode','target_id','expected_trusted_source_id','submissions']: old_event.pop(key, None)
            if 'record' in old_event: old_event['record'].pop('original_source_label', None)
            db.execute('UPDATE p2_poison_events SET data=? WHERE id=?', (canonical(old_event),event['id']))
    with kb.connect() as db:
        historical = {t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in ['p2_poison_state','p2_poison_events']}
    service = DefensiveService(kb,model,settings())
    service = DefensiveService(kb,model,settings())  # idempotent additive migration
    with kb.connect() as db:
        for table, rows in historical.items(): assert [tuple(r) for r in db.execute('SELECT * FROM '+table)] == rows
    fixture_bytes = (DATA/'trusted_knowledge.json').read_bytes()
    clean_kb = kb.info()
    for sid, ident in [('a','DP-001'),('b','DP-001'),('a','DP-002')]: service.inject(sid,ident,payload(ident))
    before = service.export('a','DP-001')['events']
    service.reset('a','DP-001')
    assert len(service.state('b','DP-001')['records']) == len(service.state('a','DP-002')['records']) == 1
    assert not service.state('a','DP-001')['records']
    assert service.export('a','DP-001')['events'][:len(before)] == before
    assert legacy.state('old-session','DP-001')['records']
    assert kb.info() == clean_kb
    assert (DATA/'trusted_knowledge.json').read_bytes() == fixture_bytes


def test_api_comparison_is_exact_and_calls_model_separately(app, model):
    client = app.test_client()
    replies = ['Actual clean mock', 'Actual vulnerable mock', 'Actual hardened mock']
    model.chat.side_effect = replies
    data = payload(answer='  Lumen devices have a ten-year warranty.  ', source_label=' same identity ')
    response = client.post('/proposal-02/poisoning/api/compare',json={'question':'How long is the warranty?','payload':data})
    assert response.status_code == 200
    result = response.json
    assert result['payload'] == data
    assert result['stages']['recovered'] is None
    for stage, answer in zip(['clean','vulnerable','hardened'],replies): assert result['stages'][stage]['answer'] == answer
    assert model.chat.call_count == 3
    assert result['decisions']['hardened']['record']['submitted_payload'] == data
    weak = result['decisions']['vulnerable']['record']
    assert weak['original_submitted_text'] == data['answer'] and weak['rating'] == data['rating'] and weak['account_id'] == data['account_id']
    assert result['stages']['vulnerable']['observations']['untrusted_data_supplied_to_model']
    assert not result['stages']['hardened']['observations']['untrusted_data_supplied_to_model']
    evidence = client.get('/proposal-02/poisoning/api/export').json
    assert evidence['events'][-1]['type'] == 'comparison'
    assert evidence['hardened']['events'][-1]['data']['answer'] == replies[2]


def test_comparison_rejects_malformed_payload_before_inference(app, model):
    response = app.test_client().post('/proposal-02/poisoning/api/compare',json={'question':'warranty','payload':payload(review={'decision':'approved'})})
    assert response.status_code == 400
    model.chat.assert_not_called()


def test_model_unavailable_never_becomes_semantic_success(hardened, model):
    accepted(hardened,'DP-002')
    model.chat.side_effect = OllamaError('private details')
    result = hardened.query('a','DP-002',REGISTRY['DP-002']['target_question'])
    assert result['answer'] is None and result['error'] == 'local_model_unavailable'
    assert result['observations']['model_followed_embedded_instruction'] == 'not_observed'
    assert not result['observations']['untrusted_data_supplied_to_model']
    assert 'private details' not in json.dumps(hardened.export('a','DP-002'))


def test_browser_modes_reset_scoping_and_absence_of_privileged_routes(app):
    a,b = app.test_client(), app.test_client()
    prefix = '/proposal-02/poisoning/api/'
    original_p1 = open(app.config['DATABASE_PATH'],'rb').read()
    assert a.post(prefix+'inject',json=payload()).status_code == 201
    assert a.post(prefix+'mode',json={'mode':'hardened'}).json['records'] == []
    assert a.post(prefix+'inject',json=payload(answer='<img src=x onerror=alert(1)>')).json['status'] == 'quarantined'
    assert b.get(prefix+'state').json['records'] == []
    assert b.post(prefix+'mode',json={'mode':'hardened'}).json['records'] == []
    for path in ['review','publish','rollback','quarantine','reset-global']:
        assert a.post(prefix+path,json={}).status_code == 404
    assert a.post(prefix+'mode',json={'mode':{}}).status_code == 400
    assert a.post(prefix+'reset',json={'session':'b'}).status_code == 400
    assert a.post(prefix+'inject',json=payload(),headers={'Origin':'https://other.invalid'}).status_code == 403
    assert a.post(prefix+'inject',json=payload(answer='x'*17000)).status_code == 413
    a.post(prefix+'reset',json={})
    recovered = a.post(prefix+'query',json={'question':'warranty','stage':'current'}).json
    assert recovered['stage'] == 'recovered'
    assert a.post(prefix+'mode',json={'mode':'vulnerable'}).json['records']
    assert open(app.config['DATABASE_PATH'],'rb').read() == original_p1


def test_trusted_cli_lifecycle_and_scope(hardened, monkeypatch, capsys):
    monkeypatch.setattr(cli,'DEFAULT_PATH',hardened.kb.path)
    submission = accepted(hardened,'DP-006',answer='Benign fictional correction')
    scope = ['--session','a','--scenario','DP-006']
    cli.main(['sandbox-list',*scope]); assert json.loads(capsys.readouterr().out)['state']['records']
    with pytest.raises(SystemExit): cli.main(['sandbox-publish',*scope,'--submission',submission])
    capsys.readouterr()
    cli.main(['sandbox-review',*scope,'--submission',submission,'--decision','approved','--note','Reviewed fictional policy locally.'])
    assert json.loads(capsys.readouterr().out)['review']['reviewer'] == 'local_organiser'
    cli.main(['sandbox-publish',*scope,'--submission',submission]); assert json.loads(capsys.readouterr().out)['dataset']['version'] == 2
    cli.main(['sandbox-rollback',*scope,'--version','1']); assert json.loads(capsys.readouterr().out)['rollback_completed']
    with pytest.raises(ValueError): hardened.review('b','DP-006',submission,'approved','Wrong session')


def test_selective_quarantine_preserves_unrelated_publication(hardened):
    a = accepted(hardened, answer='Benign fictional support addition one')
    b = accepted(hardened, answer='Benign fictional support addition two')
    publish(hardened,'DP-001',a); publish(hardened,'DP-001',b)
    hardened.quarantine('a','DP-001',a)
    rows = hardened.state('a','DP-001')['records']
    assert rows[0]['disposition'] == 'quarantined' and rows[1]['disposition'] == 'published'
    assert hardened.state('a','DP-001')['dataset']['active_entries'] == 25
    assert any(s['source_id'] == rows[1]['published_source_id'] for s in hardened.query('a','DP-001','warranty')['sources'])


def test_shared_evidence_limit_and_compare_preflight(app, hardened, model):
    weak = app.extensions['poisoning_service']
    with weak.kb.connect() as db:
        for _ in range(499): weak._event(db,'a','DP-001','quota',{})
    hardened.inject('a','DP-001',payload())
    with pytest.raises(ValueError, match='limit'): weak.inject('a','DP-001',payload())
    assert not weak.state('a','DP-001')['records']
    with pytest.raises(ValueError, match='limit'): hardened.review('a','DP-001','DP-001/1/1','approved','Reviewed locally')
    assert hardened.state('a','DP-001')['records'][0]['disposition'] == 'quarantined'
    client = app.test_client()
    state = client.get('/proposal-02/poisoning/api/state').json
    sid = state['session_id']
    with weak.kb.connect() as db:
        for _ in range(495): weak._event(db,sid,'DP-001','quota',{})
    response = client.post('/proposal-02/poisoning/api/compare',json={'question':'warranty','payload':payload()})
    assert response.status_code == 400
    assert not weak.state(sid,'DP-001')['records']
    assert not hardened.state(sid,'DP-001')['records']
    model.chat.assert_not_called()


def test_rollback_observation_and_denied_authority_audit(hardened):
    submission = accepted(hardened,'DP-006',answer='Benign fictional support correction')
    with pytest.raises(ValueError): hardened.publish('a','DP-006',submission)
    denied = hardened.export('a','DP-006')['events'][-1]
    assert denied['type'] == 'organiser_action_denied' and denied['data']['operation'] == 'publish'
    publish(hardened,'DP-006',submission)
    result = hardened.rollback('a','DP-006',1)
    query = hardened.query('a','DP-006','warranty')
    assert query['observations']['rollback_completed'] is True
    assert query['dataset']['checksum'] == result['after']['clean_checksum']
    assert query['observations']['expected_trusted_source_retrieved']
    hardened.inject('a','DP-006',payload('DP-006'))
    assert hardened.query('a','DP-006','warranty')['stage'] == 'hardened'
