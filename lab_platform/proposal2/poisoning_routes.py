"""Dedicated weak-ingestion APIs with signed-session scoping and strict schemas."""
import hashlib
import secrets
from flask import Blueprint, jsonify, render_template, request, session
from .poisoning_registry import REGISTRY, scenario

def register(app, service):
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
        return jsonify(dict(service.state(*scope()), scenarios=list(REGISTRY.values())))

    @bp.post('/api/select')
    def select():
        data = body(['scenario_id'])
        scenario(data['scenario_id'])
        session['p2_poison_scenario'] = data['scenario_id']
        return jsonify(service.state(*scope()))

    @bp.post('/api/inject')
    def inject():
        # Service validates and records bounded rejections as well as accepted submissions.
        return jsonify(service.inject(*scope(), request.get_json(silent=True))), 201

    @bp.post('/api/query')
    def query():
        data = body(['question', 'stage'])
        result = service.query(*scope(), data['question'], data['stage'])
        return jsonify(result), 503 if result['error'] else 200

    @bp.post('/api/reset')
    def reset():
        body([])
        return jsonify(service.reset(*scope()))

    @bp.get('/api/export')
    def export():
        response = jsonify(service.export(*scope()))
        response.headers['Content-Disposition'] = 'attachment; filename="poisoning-evidence.json"'
        return response

    @bp.post('/api/benchmark')
    def benchmark():
        data = body(['stage'])
        if data['stage'] not in ('clean', 'current'):
            raise ValueError('Choose clean or current stage.')
        return jsonify(service.benchmark(*scope(), data['stage']))

    app.register_blueprint(bp)
