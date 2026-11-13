"""Deterministic weak ranking; weights are server configuration, not student authority."""
from collections import defaultdict
from .retrieval_service import tokens

def claim(entry):
    return ' '.join(entry['answer'].lower().split())

def rank(entries, question, spec):
    groups = defaultdict(list)
    for e in entries:
        groups[claim(e)].append(e)
    ranked = []
    for e in entries:
        overlap = tokens(question) & tokens(e['topic'] + ' ' + ' '.join(e['keywords']))
        if not overlap:
            continue
        poisoned = e.get('poisoned', False)
        trigger = 'starlight mode' in question.lower()
        if poisoned and spec['mechanism'] == 'trigger' and not trigger:
            continue
        related = groups[claim(e)]
        distinct = len({s['source_id'] for s in related})
        duplicates = len(related) - distinct
        support = (distinct if spec['mechanism'] == 'repetition' else len(related)) if poisoned else 1
        rating = e.get('rating', 3)
        weights = spec['weights']
        signals = dict(relevance=len(overlap), rating=rating, rating_influence=rating * weights['rating'],
            submission_count=len(related), distinct_source_count=distinct, duplicate_count=duplicates,
            support_signal=support, duplicate_influence=duplicates * weights['support'],
            support_influence=max(0, support - 1) * weights['support'],
            trigger_match=trigger and poisoned and spec['mechanism'] == 'trigger',
            trigger_influence=weights['trigger'] if trigger and poisoned else 0)
        score = signals['relevance'] + signals['rating_influence'] + signals['support_influence'] + signals['trigger_influence']
        ranked.append(dict(e, signals=signals, score=score, matched_terms=sorted(overlap)))
    ranked.sort(key=lambda e: (-e['score'], e['id']))
    for n, e in enumerate(ranked, 1):
        e['rank'] = n
    return ranked
