"""Deliberately inadequate teaching controls, never production security."""
def input_allowed(text):
    return text != 'training token' and 'TRAINING_TOKEN' not in text and 'restricted' not in text

def redact(text, canary):
    return text.replace(canary, '[REDACTED]')
