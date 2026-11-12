import io
import json
from unittest.mock import Mock
import pytest
from lab_platform.config import settings
from lab_platform.ollama_client import OllamaClient, OllamaError


@pytest.mark.parametrize('value', [{}, {'message': {}}, {'message': {'role': 'assistant', 'content': ''}}, {'error': 'private'}, [], {'message': {'role': 'system', 'content': 'bad'}}])
def test_malformed(value):
    client = OllamaClient(settings())
    client.opener.open = Mock(return_value=io.BytesIO(json.dumps(value).encode()))
    with pytest.raises(OllamaError):
        client.chat([])


@pytest.mark.parametrize('error', [ConnectionRefusedError('private'), TimeoutError('private')])
def test_transport(error):
    client = OllamaClient(settings())
    client.opener.open = Mock(side_effect=error)
    with pytest.raises(OllamaError, match='local model'):
        client.chat([])


def test_payload():
    client = OllamaClient(settings())
    client.opener.open = Mock(return_value=io.BytesIO(b'{"message":{"role":"assistant","content":"Hi"}}'))
    assert client.chat([{'role': 'user', 'content': 'hi'}]) == 'Hi'
    payload = json.loads(client.opener.open.call_args.args[0].data)
    assert payload['stream'] is False
    assert payload['options']['num_ctx'] == 8192
    assert payload['options']['seed'] == 42


def test_remote_endpoint_rejected(monkeypatch):
    monkeypatch.setenv('OLLAMA_BASE_URL', 'http://example.com:11434')
    with pytest.raises(ValueError, match='loopback'):
        settings()
