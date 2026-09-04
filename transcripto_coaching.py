"""Pinned local request populations. Descriptive evidence, never prompt grades."""
import hashlib
import json
import math
from datetime import datetime, timezone

import transcripto_core as core
import transcripto_evidence as evidence


def _identity(item):
    return (item['provider'], item['session_id'], item['source']['line_start'])


def _key(item):
    return (*_identity(item), item['source']['record_sha256'])


def _interval(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    center = p + z * z / (2 * n)
    denom = 1 + z * z / n
    return [(center - margin) / denom, (center + margin) / denom]


def summarize(requests):
    groups = []
    for provider in sorted({r['provider'] for r in requests}):
        rows = [r for r in requests if r['provider'] == provider]
        known = [r for r in rows if r['change_calls'] and not r['unknown_change_results']]
        successes = sum(r['successful_change_results'] > 0 for r in known)
        groups.append({'provider': provider, 'requests': len(rows),
                       'sessions': len({r['session_id'] for r in rows}),
                       'native_human_requests': sum(r['authorship'] == 'human' for r in rows),
                       'authorship_unknown_requests': sum(r['authorship'] != 'human' for r in rows),
                       'answers_without_observed_change': sum(r['answer_without_observed_change'] for r in rows),
                       'change_requests': sum(r['change_calls'] > 0 for r in rows),
                       'unknown_change_requests': sum(r['unknown_change_results'] > 0 for r in rows),
                       'known_change_requests': len(known), 'requests_with_successful_change_result': successes,
                       'successful_change_result_fraction': successes / len(known) if known else None,
                       'wilson_95_interval': _interval(successes, len(known)),
                       'requests_with_failed_result': sum(r['failed_results'] > 0 for r in rows)})
    return {'requests': len(requests), 'groups': groups}


LIMITATIONS = [
    'These are your selected local request records, not a model-quality benchmark.',
    'A successful tool result is not correctness, durable code, user value or shipping.',
    'Answers without an observed change are counted separately, not as failures.',
    'Unknown change results are excluded from known-result fractions and shown explicitly.',
    'Wilson intervals are descriptive binomial intervals. Within-session dependence and selection bias are not modeled.',
    'Provider groups are separate source populations; differences are not causal comparisons.',
    'No multiple-comparison significance tests or practice recommendations are made.',
]


def snapshot(paths, roots, harness=None):
    requests, sources, failures, seen = [], [], [], set()
    inherited = duplicates = 0
    for path in paths:
        warnings = []
        try:
            before = evidence.version(path)
            rows, provider = core.read_session(path, warnings)
            after = evidence.version(path)
            if before != after:
                raise ValueError('source changed during snapshot; retry')
        except (OSError, ValueError) as exc:
            failures.append({'path': path, 'reason': str(exc)})
            continue
        sources.append(dict(after, path=path, provider=provider, warnings=warnings))
        by_line = {r['_line']: r for r in rows}
        for episode in core.episodes(rows, path):
            if episode.get('inherited') is True:
                inherited += 1
                continue
            row = by_line[episode['line']]
            events = episode['events']
            changes = [e for e in events if e['kind'] in ('edit', 'commit', 'rollback')]
            request = {'provider': provider, 'session_id': episode['session_id'],
                       'source': evidence.reference(path, episode['line'], row.get('_record_sha256'), after['sha256']),
                       'authorship': evidence.authorship(provider, row.get('promptSource'))['kind'],
                       'timestamp': episode['timestamp'] or None,
                       'change_calls': len(changes),
                       'successful_change_results': sum(e['status'] == 'succeeded' for e in changes),
                       'unknown_change_results': sum(e['status'] == 'unknown' for e in changes),
                       'failed_results': sum(e['status'] == 'failed' for e in events),
                       'answer_without_observed_change': bool(episode['reply']) and not changes and all(e['kind'] == 'read' for e in events)}
            key = _key(request)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            requests.append(request)
    return {'schema': 'transcripto.coaching-snapshot/1',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'selection': {'roots': roots, 'harness': harness, 'basis': 'explicit local source selection'},
            'sources': sources, 'requests': requests, 'summary': summarize(requests),
            'coverage': {'failures': failures, 'partial_sources': sum(bool(s['warnings']) for s in sources),
                         'inherited_requests_excluded': inherited, 'duplicate_request_copies_excluded': duplicates},
            'limitations': LIMITATIONS,
            'privacy': 'Local metadata and counts with source references; no request or response bodies.'}


def compare(current, baseline_path):
    with open(baseline_path, 'rb') as stream:
        raw = stream.read()
    baseline = json.loads(raw)
    if baseline.get('schema') != 'transcripto.coaching-snapshot/1':
        raise ValueError('baseline must be a transcripto.coaching-snapshot/1 file')
    old = {_key(r): r for r in baseline['requests']}
    old_locations = {_identity(r) for r in baseline['requests']}
    now = {_key(r): r for r in current['requests']}
    added = [r for key, r in now.items() if key not in old and _identity(r) not in old_locations]
    revised = [r for key, r in now.items() if key not in old and _identity(r) in old_locations]
    outcome_fields = ('change_calls', 'successful_change_results', 'unknown_change_results', 'failed_results', 'answer_without_observed_change')
    updated = [r for key, r in now.items() if key in old and any(r[f] != old[key][f] for f in outcome_fields)]
    return {'schema': 'transcripto.coaching-comparison/1',
            'observed_at': current['created_at'],
            'baseline': {'path': baseline_path, 'sha256': hashlib.sha256(raw).hexdigest(),
                         'created_at': baseline['created_at'], 'summary': summarize(list(old.values())),
                         'selection': baseline['selection'], 'coverage': baseline['coverage']},
            'newly_observed': {'summary': summarize(added), 'requests': added},
            'changed_prior_requests': revised, 'updated_prior_outcomes': updated,
            'prior_records_not_in_current_selection': sum(key not in now for key in old),
            'current_selection': current['selection'], 'coverage': current['coverage'],
            'limitations': LIMITATIONS + [
                'The baseline is read from saved bytes and never refreshed from live sources.',
                'Newly observed means absent from the saved population, not necessarily created after its timestamp.',
                'Rewritten old request lines and updated old outcomes are reported separately, not counted as new requests.',
                'Missing prior records may reflect scope or deleted sources; they are not declining performance.']}


def describe(report):
    lines = ['YOUR REQUESTS · PINNED POPULATION · NOT RANKED']
    if report['schema'] == 'transcripto.coaching-comparison/1':
        sections = [('Saved baseline', report['baseline']['summary']), ('Newly observed', report['newly_observed']['summary'])]
        lines.append('Baseline bytes: ' + report['baseline']['sha256'])
        lines.append('%d rewritten prior requests · %d updated prior outcomes · %d prior records not in this selection' % (
            len(report['changed_prior_requests']), len(report['updated_prior_outcomes']), report['prior_records_not_in_current_selection']))
    else:
        sections = [('Selected population', report['summary'])]
    for label, summary in sections:
        lines.append('\n%s: %d requests' % (label, summary['requests']))
        for group in summary['groups']:
            lines.append('  %s · %d requests in %d sessions · %d answers without observed change · %d unknown change outcomes' % (
                group['provider'], group['requests'], group['sessions'], group['answers_without_observed_change'], group['unknown_change_requests']))
            interval = group['wilson_95_interval']
            lines.append('    Successful change result: %d/%d known change requests%s' % (
                group['requests_with_successful_change_result'], group['known_change_requests'],
                (' · descriptive 95%% interval %.0f–%.0f%%' % (interval[0] * 100, interval[1] * 100)) if interval else ' · no fraction to estimate'))
    lines.extend(['', 'Tool success is not task correctness. Read-only answers are not failures.',
                  'Intervals omit within-session dependence. No causal advice or provider ranking.',
                  'Use --json for source references, unknown authorship and coverage limits.'])
    return '\n'.join(lines)
