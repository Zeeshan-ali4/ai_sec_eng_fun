"""Application trust boundary for the synthetic sandbox; local CLI owns review.

Separate additive tables leave Milestone 5 state/events byte-for-byte intact.
All lifecycle mutations use the inherited immediate SQLite transaction and quota.
"""
from functools import wraps
import hashlib
import unicodedata
from .poisoning_service import PoisoningService
from .knowledge_base import canonical
from .retrieval_service import retrieve
from ..database import utcnow
from .poisoning_registry import scenario


def normalise(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def checksum(entries):
    return hashlib.sha256(canonical(sorted(entries, key=lambda e: (e['id'], e['version']))).encode()).hexdigest()


def audited(operation):
    """Record declined organiser actions after their state transaction rolls back."""
    def decorate(method):
        @wraps(method)
        def call(self, sid, ident, *args, **kwargs):
            try:
                return method(self, sid, ident, *args, **kwargs)
            except ValueError as exc:
                try:
                    with self.kb.connect() as db:
                        self._event(db, sid, ident, 'organiser_action_denied',
                                    dict(operation=operation, reason=str(exc),
                                         record_or_version=str(args[0])[:100] if args else None))
                except ValueError:  # A full evidence quota fails closed without eviction.
                    pass
                raise
        return call
    return decorate


class DefensiveService(PoisoningService):
    mode = 'hardened'
    state_table = 'p2_defensive_state'
    event_table = 'p2_defensive_events'
    index_name = 'p2_defensive_scope'

    def _state(self, db, sid, ident):
        state = super()._state(db, sid, ident)
        if 'snapshots' not in state:
            state.update(active=list(state['clean_entries']), version=1, recovered=False,
                         snapshots=[dict(version=1, entries=state['clean_entries'],
                                         checksum=checksum(state['clean_entries']), reason='original fixture')])
            self._save(db, sid, ident, state)
        return state

    def _assess(self, state, spec, record, data):
        # Neither account selection nor a claimed source identity authenticates anyone.
        state['recovered'] = False
        state.pop('recovery', None)
        source = normalise(data['source_label'])
        claim = normalise(data['answer'])
        identity = hashlib.sha256(canonical([source, claim]).encode()).hexdigest()
        duplicate = next((r for r in state['records'] if r['stable_identity'] == identity), None)
        repeated = next((r for r in state['records'] if r['canonical_claim'] == claim), None)
        original = next(e for e in state['clean_entries'] if e['id'] == spec['target_id'])
        conflict = claim != normalise(original['answer'])
        account = record['account']
        account_class = ('new_account' if account['age_days'] < 7 else
                         'low_reputation' if account['trust_level'] == 'low' else 'unverified_account')
        record.update(submitted_payload=dict(data), stable_identity=identity, canonical_claim=claim,
                      source_identity=source, validation_decision='valid', source_trust_decision='unverified',
                      account_classification=account_class, influence_limit=0,
                      duplicate_status='exact_duplicate' if duplicate else 'repeated_claim' if repeated else 'unique',
                      duplicate_of=duplicate['submission_id'] if duplicate else None,
                      repeated_claim_of=repeated['submission_id'] if repeated else None,
                      conflict_status='potential_conflict_requires_review' if conflict else 'matches_original',
                      conflict_reference=original['id'], disposition='quarantined', approval_status='quarantined',
                      explanation='Valid syntax is not verified knowledge. Unverified source labels and fictional accounts '
                                  'grant no authority; rating has zero influence. Quarantined pending local organiser review.',
                      stages=['submission', 'validation', 'source_assessment', 'duplicate_conflict_checks',
                              'quarantine', 'not_eligible_for_publication'])
        if duplicate:
            record['explanation'] += ' Exact canonical content/source duplicate; cannot publish twice.'
        elif repeated:
            record['explanation'] += ' Repeated claim across user-controlled source labels supplies no independent verification.'
        if conflict:
            record['explanation'] += ' Text differs from target policy; this conservative conflict flag is not semantic fact checking.'
        if spec['mechanism'] == 'document':
            record['explanation'] += ' External plain-text document remains lower trust; no executable processing or permissions.'
        return record

    def _entries(self, state, spec, clean=False):
        return state['clean_entries'] if clean else state['active']

    def _info(self, state, spec, clean=False):
        entries = self._entries(state, spec, clean)
        return dict(dataset_id=f"lumen-sandbox/{spec['id']}/hardened/{state['generation']}/{1 if clean else state['version']}",
                    mode=self.mode, generation=state['generation'], version=1 if clean else state['version'],
                    checksum=checksum(entries), clean_checksum=checksum(state['clean_entries']),
                    stage='clean' if clean else 'recovered' if state['recovered'] else 'hardened',
                    active_entries=len(entries), poisoned_records=0,
                    quarantined_records=0 if clean else sum(r['disposition'] == 'quarantined' for r in state['records']))

    def _rank(self, state, spec, question, baseline):
        sources = retrieve(self._entries(state, spec, baseline), question)
        return [dict(e, rank=n, inclusion_reason='Verified approved knowledge; ratings and repeated claims have no influence.',
                     signals=dict(relevance=e['score'], authority=e['source_classification'], rating_influence=0,
                                  duplicate_influence=0, support_influence=0, trigger_influence=0))
                for n, e in enumerate(sources, 1)]

    def _query_details(self, state, spec, question, baseline):
        entries = self._entries(state, spec, baseline)
        selected = {e['source_id'] for e in self._rank(state, spec, question, baseline)}
        excluded = [dict(submission_id=r['submission_id'], source_id=r['source_id'],
                         disposition=r['disposition'], reason=r['explanation'],
                         trigger_match='starlight mode' in question.casefold() and 'starlight mode' in r['answer'].casefold(),
                         duplicate_status=r['duplicate_status'], conflict_status=r['conflict_status'])
                    for r in state['records'] if baseline or r['disposition'] != 'published']
        excluded.extend(dict(source_id=e['source_id'], reason='No lexical match or outside bounded top three.')
                        for e in entries if e['source_id'] not in selected)
        return dict(mode=self.mode, submissions=[] if baseline else list(state['records']), excluded_candidates=excluded,
                    dataset_version=1 if baseline else state['version'], recovery=None if baseline else state.get('recovery'))

    def state(self, sid, ident):
        with self.lock:
            result = super().state(sid, ident)
            with self.kb.connect() as db:
                state = self._state(db, sid, ident)
                result['snapshots'] = [{k:v for k,v in s.items() if k != 'entries'} for s in state['snapshots']]
            return result

    def _record(self, state, submission_id):
        record = next((r for r in state['records'] if r['submission_id'] == submission_id), None)
        if not record:
            raise ValueError('Submission not found in selected session/scenario/generation.')
        return record

    @audited('review')
    def review(self, sid, ident, submission_id, decision, note):
        if decision not in {'approved', 'rejected'} or not isinstance(note, str) or not note.strip() or len(note) > 1000:
            raise ValueError('A bounded local factual review note and approved/rejected decision are required.')
        with self.lock, self.kb.connect() as db:
            state = self._state(db, sid, ident)
            record = self._record(state, submission_id)
            if record['disposition'] != 'quarantined':
                raise ValueError('Only quarantined submissions can be reviewed.')
            if decision == 'approved' and record['duplicate_of']:
                raise ValueError('Exact duplicate: review the original submission instead.')
            record['reviewed_target_checksum'] = checksum([e for e in state['active'] if e['id'] == scenario(ident)['target_id']])
            record.update(disposition=decision, approval_status=decision,
                          review=dict(reviewer='local_organiser', decision=decision, note=note.strip(), timestamp=utcnow()))
            record['stages'].extend(['trusted_review', 'publication_eligible' if decision == 'approved' else 'publication_denied'])
            self._save(db, sid, ident, state)
            self._event(db, sid, ident, 'review', dict(record=record, dataset=self._info(state, scenario(ident))))
            return record

    def _snapshot(self, state, reason):
        state['version'] += 1
        snapshot = dict(version=state['version'], entries=list(state['active']),
                        checksum=checksum(state['active']), reason=reason, timestamp=utcnow())
        state['snapshots'].append(snapshot)
        return snapshot

    @audited('publish')
    def publish(self, sid, ident, submission_id):
        spec = scenario(ident)
        with self.lock, self.kb.connect() as db:
            state = self._state(db, sid, ident)
            record = self._record(state, submission_id)
            if record['disposition'] != 'approved' or record.get('review', {}).get('decision') != 'approved':
                raise ValueError('Explicit trusted local approval is required before separate publication.')
            if any(normalise(e['answer']) == record['canonical_claim'] for e in state['active']):
                raise ValueError('Canonical duplicate already active; no independent authority added.')
            if spec['mechanism'] == 'correction' and record['reviewed_target_checksum'] != checksum([e for e in state['active'] if e['id'] == spec['target_id']]):
                raise ValueError('Correction target changed since review; submit for fresh review.')
            before = self._info(state, spec)
            target = spec['target_id'] if spec['mechanism'] == 'correction' else record['id']
            previous = next((e for e in state['active'] if e['id'] == target), None)
            entry = dict({k: record[k] for k in state['clean_entries'][0]}, review=record['review'], id=target, version=previous['version'] + 1 if previous else 1,
                         source_id='REVIEWED:' + record['submission_id'], trust_level='trusted',
                         source_classification='organiser_reviewed', approval_status='approved')
            if previous:
                for other in state['records']:
                    if other.get('published_source_id') == previous['source_id']:
                        other.update(disposition='superseded', approval_status='superseded')
            state['active'] = [e for e in state['active'] if e['id'] != target] + [entry]
            record.update(disposition='published', approval_status='published', published_source_id=entry['source_id'],
                          publication=dict(timestamp=utcnow(), publisher='local_organiser', previous=previous))
            record['stages'].append('publication')
            state['recovered'] = False
            state.pop('recovery', None)
            snapshot = self._snapshot(state, 'published ' + submission_id)
            self._save(db, sid, ident, state)
            self._event(db, sid, ident, 'publication', dict(record=record, before=before, after=self._info(state, spec), snapshot=snapshot))
            return dict(record=record, dataset=self._info(state, spec))

    @audited('rollback')
    def rollback(self, sid, ident, version):
        if type(version) is not int:
            raise ValueError('Version must be an integer.')
        with self.lock, self.kb.connect() as db:
            state = self._state(db, sid, ident)
            snapshot = next((s for s in state['snapshots'] if s['version'] == version), None)
            if not snapshot or version >= state['version']:
                raise ValueError('Choose an earlier trusted snapshot from this generation.')
            before = self._info(state, scenario(ident))
            if checksum(snapshot['entries']) != snapshot['checksum']:
                raise ValueError('Snapshot integrity check failed.')
            active_sources = {e['source_id'] for e in snapshot['entries']}
            revoked = []
            for record in state['records']:
                if record.get('published_source_id') in active_sources:
                    record.update(disposition='published', approval_status='published')
                elif record['disposition'] == 'published' and record['published_source_id'] not in active_sources:
                    record.update(disposition='quarantined', approval_status='quarantined',
                                  recovery_reason='Publication revoked by trusted rollback; new review required.')
                    record['stages'].append('publication_revoked')
                    revoked.append(record['submission_id'])
            state['active'] = list(snapshot['entries'])
            state['recovered'] = True
            self._snapshot(state, 'rollback to ' + str(version))
            self._save(db, sid, ident, state)
            after = self._info(state, scenario(ident))
            result = dict(before=before, after=after, restored_version=version, revoked_submissions=revoked,
                          rollback_completed=after['checksum'] == snapshot['checksum'],
                          expected_trusted_sources_restored=[e['source_id'] for e in snapshot['entries']], evidence_retained=True)
            state['recovery'] = dict(operation='rollback', rollback_completed=result['rollback_completed'], expected_checksum=snapshot['checksum'])
            self._save(db, sid, ident, state)
            self._event(db, sid, ident, 'rollback', result)
            return result

    @audited('quarantine')
    def quarantine(self, sid, ident, submission_id):
        """Selectively revoke one publication; preserve unrelated accepted changes."""
        with self.lock, self.kb.connect() as db:
            state = self._state(db, sid, ident)
            record = self._record(state, submission_id)
            if record['disposition'] != 'published':
                raise ValueError('Only an active published record can be revoked; other records are already excluded.')
            source = record['published_source_id']
            if source not in {e['source_id'] for e in state['active']}:
                raise ValueError('Publication is no longer active; choose rollback explicitly.')
            before = self._info(state, scenario(ident))
            state['active'] = [e for e in state['active'] if e['source_id'] != source]
            previous = record['publication']['previous']
            if previous:
                state['active'].append(previous)
                for other in state['records']:
                    if other.get('published_source_id') == previous['source_id']:
                        other.update(disposition='published', approval_status='published')
            record.update(disposition='quarantined', approval_status='quarantined',
                          recovery_reason='Publication revoked locally; previous approved version restored where applicable.')
            record['stages'].append('publication_revoked')
            state['recovered'] = True
            snapshot = self._snapshot(state, 'quarantined ' + submission_id)
            state['recovery'] = dict(operation='quarantine', expected_checksum=snapshot['checksum'])
            after = self._info(state, scenario(ident))
            result = dict(before=before, after=after, quarantined_submission=submission_id,
                          quarantine_completed=source not in {e['source_id'] for e in state['active']},
                          restored_source_id=previous['source_id'] if previous else None, evidence_retained=True)
            self._save(db, sid, ident, state)
            self._event(db, sid, ident, 'quarantine', result)
            return result

    def reset(self, sid, ident):
        with self.lock, self.kb.connect() as db:
            state = self._state(db, sid, ident)
            before = self._info(state, scenario(ident))
            state.update(generation=state['generation'] + 1, records=[], submissions=0,
                         active=list(state['clean_entries']), version=1, recovered=True,
                         recovery=dict(operation='reset', expected_checksum=checksum(state['clean_entries'])),
                         snapshots=[dict(version=1, entries=state['clean_entries'], checksum=checksum(state['clean_entries']), reason='original fixture')])
            self._save(db, sid, ident, state)
            self._event(db, sid, ident, 'reset', dict(before=before, after=self._info(state, scenario(ident)), evidence_retained=True))
            return dict(status='Selected hardened sandbox reset to original fixture; evidence retained.')
