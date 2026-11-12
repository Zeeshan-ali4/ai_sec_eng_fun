import secrets
from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
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
    service = ChatService(model, system_prompt(load_data()), app.config)
    app.extensions['chat_service'] = service

    def sid():
        if 'sid' not in session:
            session['sid'] = secrets.token_urlsafe(32)
        return session['sid']

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
            return jsonify(reply=service.reply(sid(), data['message']))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except OllamaError as exc:
            return jsonify(error=str(exc)), 503

    @app.post('/api/reset')
    def reset():
        service.reset(sid())
        return jsonify(status='reset')

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
