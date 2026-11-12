"""Small bounded, non-streaming adapter for Ollama's local HTTP API."""
import json
import urllib.error
import urllib.request


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, config):
        self.url = config['OLLAMA_BASE_URL']
        self.model = config['OLLAMA_MODEL']
        self.timeout = config['OLLAMA_TIMEOUT']
        self.options = config['OLLAMA_OPTIONS']
        # Never proxy local model traffic or follow redirects to other endpoints.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def _request(self, path, payload=None, timeout=None):
        request = urllib.request.Request(self.url + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=timeout or self.timeout) as response:
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError('Oversized response')
                result = json.loads(raw)
                if not isinstance(result, dict) or 'error' in result:
                    raise ValueError('Invalid response')
                return result
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise OllamaError('The local model is unavailable or returned an invalid response. Check Ollama and the installed model, then retry.') from exc

    def chat(self, messages):
        result = self._request('/api/chat', dict(model=self.model, messages=messages,
                                               stream=False, options=self.options))
        message = result.get('message')
        if (not isinstance(message, dict) or message.get('role') != 'assistant'
                or not isinstance(message.get('content'), str) or not message['content'].strip()
                or len(message['content']) > 6000 or message.get('tool_calls')):
            raise OllamaError('The local model returned an invalid response. Please retry.')
        return message['content']

    def chat_with_tools(self, messages):
        from .sales_tool import TOOLS
        result = self._request('/api/chat', dict(model=self.model, messages=messages,
                              stream=False, options=self.options, tools=TOOLS))
        message = result.get('message')
        if (not isinstance(message, dict) or message.get('role') != 'assistant'
                or not isinstance(message.get('content', ''), str)
                or len(message.get('content', '')) > 6000):
            raise OllamaError('The local model returned an invalid response. Please retry.')
        calls = message.get('tool_calls', [])
        if not isinstance(calls, list) or len(calls) > 3 or len(json.dumps(calls).encode()) > 12000 or (not calls and not message.get('content', '').strip()):
            raise OllamaError('The local model returned invalid tool calls. Please retry.')
        return dict(role='assistant', content=message.get('content', ''), tool_calls=calls)

    def health(self):
        result = self._request('/api/tags', timeout=3)
        models = result.get('models')
        if not isinstance(models, list):
            raise OllamaError('Ollama returned an invalid model list.')
        match = next((m for m in models if isinstance(m, dict) and m.get('name') == self.model), None)
        return dict(available=True, model_ready=match is not None, model=self.model,
                    digest=match.get('digest') if match else None)
