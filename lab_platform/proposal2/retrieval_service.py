"""Replaceable deterministic ranking: lexical overlap, no rating influence."""
import re
STOP = set('a an the is are was were do does how what when where can i my me you your it its to of for in on and or with have has this that lumen support fictional please us we'.split())

def tokens(text):
    return set(re.findall(r'[a-z0-9_]+', text.lower())) - STOP

def retrieve(entries, question, limit=3):
    query = tokens(question)
    ranked = []
    for entry in entries:
        if entry['approval_status'] != 'approved' or entry['trust_level'] != 'trusted':
            continue
        terms = tokens(entry['topic'] + ' ' + ' '.join(entry['keywords']))
        overlap = query & terms
        if overlap:
            ranked.append(dict(entry, score=len(overlap), matched_terms=sorted(overlap)))
    ranked.sort(key=lambda e: (-e['score'], e['id'], -e['version']))
    # Identical approved topic/answer records cannot crowd the result set.
    unique, seen = [], set()
    for e in ranked:
        key = (e['topic'].lower().strip(), e['answer'].lower().strip())
        if key not in seen:
            unique.append(e)
            seen.add(key)
    return unique[:max(0, min(limit, 3))]
