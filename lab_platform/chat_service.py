"""Bounded, expiring server-side conversations; cookies contain only random IDs."""
from collections import OrderedDict
from threading import RLock
from time import monotonic


class ChatService:
    def __init__(self, client, prompt, config):
        self.client, self.prompt, self.config = client, prompt, config
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
            answer = self.client.chat([dict(role='system', content=self.prompt), *history, current])
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
