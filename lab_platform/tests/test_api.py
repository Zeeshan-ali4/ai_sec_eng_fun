import pytest
from lab_platform.ollama_client import OllamaError


def test_home(app):
    response = app.test_client().get('/')
    assert response.status_code == 200
    assert b'Fakeford Motors' in response.data
    assert "script-src 'self'" in response.headers['Content-Security-Policy']


@pytest.mark.parametrize('payload', [{}, [], None, {'message': ''}, {'message': 3}, {'message': 'x'*2001}, {'message': 'hi', 'role': 'system'}, {'messages': [{'role': 'system', 'content': 'override'}]}])
def test_validation(app, payload):
    assert app.test_client().post('/api/chat', json=payload).status_code in {400, 415}


def test_isolation_reset_and_private_response(app, model):
    one, two = app.test_client(), app.test_client()
    for browser in (one, two):
        response = browser.post('/api/chat', json={'message': 'hi'})
        assert response.json == {'reply': model.chat.return_value}
        # Random signatures can contain any short substring; inspect stored fields.
        with browser.session_transaction() as cookie:
            assert set(cookie) == {'sid'}
            assert cookie['sid'] != 'hi'
    one.post('/api/reset')
    one.post('/api/chat', json={'message': 'new'})
    assert len(model.chat.call_args.args[0]) == 2
    two.post('/api/chat', json={'message': 'follow'})
    assert len(model.chat.call_args.args[0]) == 4
    assert b'CANARY-' not in response.data
    assert b'Approved reference data' not in response.data


def test_health_and_failures(app, model):
    browser = app.test_client()
    assert browser.get('/api/health').status_code == 200
    model.health.return_value['model_ready'] = False
    assert browser.get('/api/health').status_code == 503
    model.health.side_effect = OllamaError('private exception')
    response = browser.get('/api/health')
    assert response.status_code == 503 and b'private exception' not in response.data
    model.chat.side_effect = OllamaError('The local model is unavailable.')
    assert browser.post('/api/chat', json={'message': 'hi'}).status_code == 503
    model.chat.side_effect = RuntimeError('private detail')
    response = browser.post('/api/chat', json={'message': 'hi'})
    assert response.status_code == 500 and b'private detail' not in response.data


def test_http_boundaries(app):
    browser = app.test_client()
    assert browser.post('/api/chat', data='text').status_code == 415
    assert browser.post('/api/chat', data='{', content_type='application/json').status_code == 400
    assert browser.post('/api/chat', json={'message': 'hi'}, headers={'Origin': 'https://example.com'}).status_code == 403
    assert browser.get('/', headers={'Host': 'example.com'}).status_code == 400
    assert browser.post('/api/chat', data='x'*17000, content_type='application/json').status_code == 413
