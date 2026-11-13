"""Scoped weak and hardened ingestion APIs with signed-session scoping and strict schemas."""
import hashlib
import secrets
from flask import Blueprint, jsonify, render_template, request, session
from .poisoning_registry import REGISTRY, scenario

def register(app, service):
    from .defensive_service import DefensiveService
    hardened = DefensiveService(service.kb, service.model, service.config)
    hardened.lock = service.lock
    app.extensions["defensive_service"] = hardened

    def selected():
        return hardened if session.get("p2_protection_mode", "vulnerable") == "hardened" else service

    bp = Blueprint('poisoning', __name__, url_prefix='/proposal-02/poisoning')

    def scope():
        if 'p2_sid' not in session:
            session['p2_sid'] = secrets.token_urlsafe(32)
        return hashlib.sha256(session['p2_sid'].encode()).hexdigest(), session.get('p2_poison_scenario', 'DP-001')

    def body(keys):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != set(keys):
            raise ValueError('Send only: ' + ', '.join(keys))
        return data

    @bp.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(error=str(exc)), 400

    @bp.get('')
    def index():
        scope()
        return render_template('proposal2/poisoning.html')

    @bp.get('/api/state')
    def state():
        return jsonify(dict(selected().state(*scope()), scenarios=list(REGISTRY.values())))

    @bp.post('/api/select')
    def select():
        data = body(['scenario_id'])
        scenario(data['scenario_id'])
        session['p2_poison_scenario'] = data['scenario_id']
        return jsonify(selected().state(*scope()))

    @bp.post('/api/mode')
    def mode():
        data = body(['mode'])
        if not isinstance(data['mode'], str) or data['mode'] not in {'vulnerable', 'hardened'}:
            raise ValueError('Choose vulnerable or hardened.')
        session['p2_protection_mode'] = data['mode']
        return jsonify(selected().state(*scope()))

    @bp.post('/api/compare')
    def compare():
        data = body(['question', 'payload'])
        sid, ident = scope()
        # Shared lock keeps query snapshots and exact replay in one local experiment.
        # Each submission commits separately; validation/quota failures are explicit.
        with service.lock:
            service.validate_payload(data['payload'])
            for policy in (service, hardened):
                with service.kb.connect() as db:
                    state = policy._state(db, sid, ident)
                    count = policy._event_count(db, sid)
                    if state['submissions'] >= 40 or count + 6 > 500:
                        raise ValueError('Comparison exceeds submission/evidence limits; export before organiser maintenance.')
            clean = service.query(sid, ident, data['question'], 'clean')
            decisions = {}
            for name, policy in [('vulnerable', service), ('hardened', hardened)]:
                try:
                    decisions[name] = policy.inject(sid, ident, data['payload'])
                except ValueError as exc:
                    decisions[name] = dict(status='rejected', error=str(exc))
            vulnerable = service.query(sid, ident, data['question'])
            protected = hardened.query(sid, ident, data['question'])
            report = dict(question=clean['question'], payload=data['payload'], decisions=decisions,
                          stages=dict(clean=clean, vulnerable=vulnerable, hardened=protected, recovered=None),
                          note='Identical payload replayed. Inspect all existing submissions; prior scenario history is retained. Recovered requires a subsequent real query after reset or local rollback.')
            with service.kb.connect() as db:
                service._event(db, sid, ident, 'comparison', dict(question=clean['question'], payload=data['payload'],
                    decisions={k:v['status'] for k,v in decisions.items()},
                    query_evidence_ids=[r['evidence_id'] for r in (clean, vulnerable, protected)]))
            return jsonify(report)

    @bp.post('/api/inject')
    def inject():
        # Service validates and records bounded rejections as well as accepted submissions.
        return jsonify(selected().inject(*scope(), request.get_json(silent=True))), 201

    @bp.post('/api/query')
    def query():
        data = body(['question', 'stage'])
        result = selected().query(*scope(), data['question'], data['stage'])
        return jsonify(result), 503 if result['error'] else 200

    @bp.post('/api/reset')
    def reset():
        body([])
        return jsonify(selected().reset(*scope()))

    @bp.get('/api/export')
    def export():
        response = jsonify(dict(service.export(*scope()), hardened=hardened.export(*scope())))
        response.headers['Content-Disposition'] = 'attachment; filename="poisoning-evidence.json"'
        return response

    @bp.post('/api/benchmark')
    def benchmark():
        data = body(['stage'])
        if data['stage'] not in ('clean', 'current'):
            raise ValueError('Choose clean or current stage.')
        return jsonify(selected().benchmark(*scope(), data['stage']))

    app.register_blueprint(bp)
