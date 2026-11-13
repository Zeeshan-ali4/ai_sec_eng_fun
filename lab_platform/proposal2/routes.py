"""Student APIs deliberately provide no review, publication or dataset reset."""
import hashlib
import secrets
from flask import Blueprint, jsonify, render_template, request, session
from ..ollama_client import OllamaError
from .accounts import accounts
from .ingestion_service import submit, submissions


def register(app, kb, service):
    bp = Blueprint('proposal2', __name__, url_prefix='/proposal-02')

    def sid():
        if 'p2_sid' not in session:
            session['p2_sid'] = secrets.token_urlsafe(32)
        return hashlib.sha256(session['p2_sid'].encode()).hexdigest()

    @bp.get('')
    def index():
        sid()
        return render_template('proposal2/index.html')

    @bp.get('/api/baseline')
    def baseline():
        return jsonify(kb.info())

    @bp.get('/api/knowledge')
    def knowledge():
        return jsonify(entries=kb.entries())

    @bp.get('/api/accounts')
    def identities():
        return jsonify(accounts=accounts())

    @bp.route('/api/submissions', methods=['GET', 'POST'])
    def proposals():
        if request.method == 'GET':
            return jsonify(submissions=submissions(kb, sid()))
        try:
            ident = submit(kb, sid(), request.get_json(silent=True))
            return jsonify(id=ident, status='pending'), 201
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @bp.post('/api/chat')
    def chat():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {'message'}:
            return jsonify(error='Send only message; roles and instructions are server-owned.'), 400
        try:
            return jsonify(service.reply(sid(), data['message']))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except OllamaError:
            return jsonify(error='The local model is unavailable. Start Ollama and install llama3.1:8b, then retry.'), 503

    @bp.post('/api/reset')
    def reset():
        data = request.get_json(silent=True)
        if data != {}:
            return jsonify(error='Send an empty JSON object.'), 400
        service.reset(sid())
        return jsonify(status='Conversation cleared; evidence retained')

    app.register_blueprint(bp)
