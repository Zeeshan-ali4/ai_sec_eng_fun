import pytest
from lab_platform.ollama_client import OllamaError


def test_roles_isolation_reset(app, model):
    service = app.extensions['chat_service']
    service.reply('one', 'First')
    service.reply('one', 'Follow-up')
    messages = model.chat.call_args.args[0]
    assert [m['role'] for m in messages] == ['system', 'user', 'assistant', 'user']
    assert messages[0]['content'] == service.prompt
    service.reply('two', 'Separate')
    assert len(model.chat.call_args.args[0]) == 2
    service.reset('one')
    assert 'one' not in service.histories and 'two' in service.histories


def test_limits(app, model):
    service = app.extensions['chat_service']
    with pytest.raises(ValueError):
        service.reply('a', 'x' * 2001)
    for _ in range(12):
        service.reply('a', 'x' * 2000)
    assert len(service.histories['a'][1]) <= 12
    assert sum(len(m['content'].encode()) for m in model.chat.call_args.args[0]) <= 22000
    service.config['MAX_SESSIONS'] = 2
    for sid in ['b', 'c', 'd']:
        service.reply(sid, 'hi')
    assert len(service.histories) == 2
    service.config['SESSION_TTL'] = -1
    service.reply('e', 'hi')
    assert list(service.histories) == ['e']


def test_failure_is_atomic(app, model):
    service = app.extensions['chat_service']
    model.chat.side_effect = OllamaError('Unavailable')
    with pytest.raises(OllamaError):
        service.reply('a', 'hello')
    assert 'a' not in service.histories
