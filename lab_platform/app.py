import secrets
from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
from .challenges.registry import REGISTRY, validate
from .database import Database
from .event_logger import EventLogger
from .challenge_service import ChallengeService
from .config import settings
from .data_loader import load_data, system_prompt
from .chat_service import ChatService
from .ollama_client import OllamaClient, OllamaError


def create_app(test_config=None, client=None):
    app = Flask(__name__)
    app.config.update(settings())
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16384,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      TRUSTED_HOSTS=['127.0.0.1', 'localhost', '[::1]'])
    if test_config:
        app.config.update(test_config)
    model = client or OllamaClient(app.config)
    database = Database(app.config['DATABASE_PATH'])
    challenge = ChallengeService(database, EventLogger(database))
    app.extensions['challenge_service'] = challenge
    service = ChatService(model, system_prompt(load_data()), app.config, challenge)
    app.extensions['chat_service'] = service

    from pathlib import Path
    from .proposal2.knowledge_base import KnowledgeBase
    from .proposal2.support_service import SupportService
    from .proposal2.routes import register
    p2_path = app.config.get('PROPOSAL2_DATABASE_PATH',
        str(Path(app.config['DATABASE_PATH']).with_name('proposal2.sqlite3')))
    if Path(p2_path).resolve() == Path(app.config['DATABASE_PATH']).resolve():
        raise ValueError('Proposal 2 requires a separate database.')
    p2_kb = KnowledgeBase(p2_path)
    p2_service = SupportService(p2_kb, model, app.config)
    app.extensions['proposal2_kb'] = p2_kb
    app.extensions['proposal2_service'] = p2_service
    register(app, p2_kb, p2_service)
    from .proposal2.poisoning_service import PoisoningService
    from .proposal2.poisoning_routes import register as register_poisoning
    poisoning = PoisoningService(p2_kb, model, app.config)
    app.extensions['poisoning_service'] = poisoning
    register_poisoning(app, poisoning)

    def sid():
        if 'sid' not in session:
            session['sid'] = secrets.token_urlsafe(32)
        return session['sid']

    def selection():
        return session.get('challenge', 'CH-001'), session.get('mode', 'vulnerable')

    @app.before_request
    def local_origin():
        if request.method == 'POST':
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                return jsonify(error='Cross-origin requests are not allowed.'), 403

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    @app.get('/')
    def index():
        sid()
        return render_template('index.html')

    @app.post('/api/chat')
    def chat():
        if not request.is_json:
            return jsonify(error='Send a JSON object containing only message.'), 415
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {'message'}:
            return jsonify(error='Send a JSON object containing only message.'), 400
        try:
            return jsonify(reply=service.reply(sid(), data['message'], *selection()))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except OllamaError:
            return jsonify(error='The local model is unavailable or returned an invalid response. Check Ollama and retry.'), 503

    @app.post('/api/reset')
    def reset():
        service.reset(sid(), *selection())
        return jsonify(status='reset')

    @app.get('/api/challenge')
    def evidence():
        return jsonify(challenge.evidence(sid(), *selection()))

    @app.post('/api/challenge/submit')
    def submit():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {'attempt_id'} or type(data['attempt_id']) is not int:
            return jsonify(error='Send only an integer attempt_id.'), 400
        with service.lock:
            try:
                challenge.submit(sid(), data['attempt_id'])
            except ValueError as exc:
                return jsonify(error=str(exc)), 400
        return jsonify(status='Submitted for manual review')

    @app.post('/api/challenge/reset')
    def challenge_reset():
        # Logical reset preserves instructor evidence and monotonic attempt numbers.
        with service.lock:
            service.reset(sid(), *selection())
            challenge.reset_state(sid(), *selection())
            with database.connect() as db:
                challenge.logger.write(db, sid(), 'challenge_reset', challenge_id=selection()[0], mode=selection()[1])
        return jsonify(status='Challenge restarted; evidence retained')

    @app.get('/api/challenges')
    def catalogue():
        return jsonify(challenges=list(REGISTRY.values()), selected=dict(zip(('challenge_id', 'mode'), selection())))

    @app.post('/api/challenge/select')
    def select():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {'challenge_id', 'mode'} or not all(isinstance(v, str) for v in data.values()):
            return jsonify(error='Send challenge_id and mode.'), 400
        try:
            validate(data['challenge_id'], data['mode'])
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        with service.lock:
            session['challenge'], session['mode'] = data['challenge_id'], data['mode']
        return jsonify(status='Selected isolated challenge and mode')

    @app.route('/api/challenge/document', methods=['GET', 'POST'])
    def document():
        selected, mode = selection()
        if selected != 'CH-005':
            return jsonify(error='Select CH-005 first.'), 400
        with service.lock:
            content = None
            if request.method == 'POST':
                data = request.get_json(silent=True)
                if not isinstance(data, dict) or set(data) != {'id', 'content'} or data['id'] != 'support-001':
                    return jsonify(error='Only support-001 content may be edited.'), 400
                content = data['content']
                if content is None:
                    return jsonify(error='Document content must be text.'), 400
            try:
                return jsonify(challenge.document(sid(), mode, content))
            except ValueError as exc:
                return jsonify(error=str(exc)), 400

    @app.get('/api/health')
    def health():
        try:
            state = model.health()
            ready = state['model_ready']
            return jsonify(application='ok', ollama=state), 200 if ready else 503
        except OllamaError:
            return jsonify(application='ok', ollama=dict(available=False, model_ready=False,
                           model=app.config['OLLAMA_MODEL']), error='Start local Ollama and install the configured model.'), 503

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.name), exc.code

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        # Do not log transcripts, model responses, prompts, or exception details.
        app.logger.error('Unexpected application failure (%s)', type(exc).__name__)
        return jsonify(error='An application error occurred. Please retry.'), 500

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
