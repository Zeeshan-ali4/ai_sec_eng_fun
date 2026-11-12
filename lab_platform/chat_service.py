"""Bounded, expiring server-side conversations; cookies contain only random IDs."""
from collections import OrderedDict
from threading import RLock
from time import monotonic


class ChatService:
    def __init__(self, client, prompt, config, challenge=None):
        self.client, self.prompt, self.config = client, prompt, config
        self.challenge = challenge
        self.histories = OrderedDict()
        self.lock = RLock()
        if len(prompt.encode()) + config['MAX_MESSAGE_CHARS'] * 4 > config['MAX_CONTEXT_BYTES']:
            raise ValueError('Approved data exceeds the configured context budget.')

    def _prune(self):
        now = monotonic()
        for sid, (updated, _) in list(self.histories.items()):
            if now - updated > self.config['SESSION_TTL']:
                del self.histories[sid]

    def reply(self, sid, message):
        if not isinstance(message, str) or not message.strip():
            raise ValueError('Enter a nonempty message.')
        message = message.strip()
        if len(message) > self.config['MAX_MESSAGE_CHARS']:
            raise ValueError(f"Messages must be at most {self.config['MAX_MESSAGE_CHARS']} characters.")
        # Serialize requests and resets so a late reply cannot resurrect reset history.
        with self.lock:
            self._prune()
            history = list(self.histories.get(sid, (0, []))[1])
            current = dict(role='user', content=message)
            def size():
                return sum(len(m['content'].encode()) for m in [dict(content=self.prompt), *history, current])
            while history and (len(history) > 2 * (self.config['MAX_HISTORY_TURNS'] - 1)
                               or size() > self.config['MAX_CONTEXT_BYTES']):
                history = history[2:]
            if size() > self.config['MAX_CONTEXT_BYTES']:
                raise ValueError('Message exceeds the conversation context budget.')
            messages = [dict(role='system', content=self.prompt), *history, current]
            attempt = self.challenge.start(sid, message, self.config) if self.challenge else None
            try:
                answer = self._generate(sid, messages, attempt)
                if self.challenge:
                    self.challenge.finish(sid, attempt, answer)
            except Exception:
                if self.challenge:
                    self.challenge.finish(sid, attempt)
                raise
            history += [current, dict(role='assistant', content=answer)]
            while history and sum(len(m['content'].encode()) for m in history) > self.config['MAX_CONTEXT_BYTES']:
                history = history[2:]
            self.histories[sid] = (monotonic(), history)
            self.histories.move_to_end(sid)
            while len(self.histories) > self.config['MAX_SESSIONS']:
                self.histories.popitem(last=False)
            return answer

    def reset(self, sid):
        with self.lock:
            self.histories.pop(sid, None)
            if self.challenge:
                with self.challenge.database.connect() as db:
                    self.challenge.logger.write(db, sid, 'conversation_reset')

    def _generate(self, sid, messages, attempt):
        from .ollama_client import OllamaClient, OllamaError
        from .sales_tool import validate, execute, NAME
        import json
        # Preserve compatibility with the original plain-chat adapter and test clients.
        if not self.challenge or not isinstance(self.client, OllamaClient):
            return self.client.chat(messages)
        for round_number in range(4):
            if sum(len(m.get('content', '').encode()) for m in messages) > self.config['MAX_CONTEXT_BYTES'] + 8000:
                raise OllamaError('Tool conversation exceeded the context budget. Please reset.')
            result = self.client.chat_with_tools(messages)
            calls = result['tool_calls']
            if not calls:
                return result['content']
            messages.append(result)
            for call in calls:
                with self.challenge.database.connect() as db:
                    ident, number = attempt
                    # Record bounded requests, including rejected proposals; never server prompts.
                    self.challenge.logger.write(db, sid, 'tool_requested', dict(request=call), number)
                    db.execute('UPDATE attempts SET tool_requested=1 WHERE id=?', (ident,))
                    try:
                        if round_number == 3:
                            raise ValueError('Tool round limit')
                        args = validate(call)
                    except (ValueError, TypeError):
                        outcome = dict(error='Tool request rejected: invalid name or arguments')
                        self.challenge.logger.write(db, sid, 'tool_rejected', outcome, number)
                    else:
                        outcome = execute(db, sid, number, args)
                        self.challenge.logger.write(db, sid, 'tool_completed', dict(arguments=args, result=outcome), number)
                        db.execute('UPDATE attempts SET action_executed=1 WHERE id=?', (ident,))
                messages.append(dict(role='tool', tool_name=NAME, content=json.dumps(outcome)))
            if round_number == 3:
                raise OllamaError('The local model exceeded the tool-call limit. Please retry.')
