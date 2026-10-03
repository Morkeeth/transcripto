"""Local references for opt-in detector observations. Never a human truth label."""
import hashlib
import json
import math
import os
from datetime import datetime, timezone
import transcripto_core as core

SCHEMA = 'transcripto.jev-findings/1'

def file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()

def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def observe(path, detector, fixture=False):
    import transcripto as app
    from transcripto_jev import privacy
    path = os.path.abspath(os.path.expanduser(path))
    before = file_hash(path)
    diagnostics = []
    rows, harness = core.read_session(path, diagnostics)
    if diagnostics:
        raise ValueError('Session has parsing warnings; repair it before detector inspection.')
    if file_hash(path) != before:
        raise ValueError('Source changed during reading; nothing sent.')
    typed = [(app._human_prompt(r), r.get('_line')) for r in rows if app._human_prompt(r)]
    texts = [t for t, _ in typed]
    if getattr(detector, 'dry_run', False):
        return app._jev_preview_report(detector, texts, harness, records=len(rows))
    verdicts = detector.score(texts)
    probabilities = detector.probabilities
    findings = []
    for (text, line), verdict, probability in zip(typed, verdicts, probabilities):
        clean, reason, _ = privacy(text, getattr(detector, '_home', None))
        status = 'excluded' if clean is None else 'unknown' if verdict is None else 'candidate' if verdict else 'not_candidate'
        findings.append({'line': line, 'request_sha256': text_hash(text), 'status': status,
                         'probability': probability, 'exclusion': reason,
                         'evaluated_text_sha256': text_hash(clean) if clean is not None else None})
    return {'schema': SCHEMA, 'source': path, 'source_sha256': before,
            'source_matches_at_return': file_hash(path) == before,
            'harness': harness, 'fixture': fixture or getattr(detector, 'fixture', False) is True,
            'synthetic': any(r.get('transcripto_synthetic') is True for r in rows),
            'observed_at': datetime.now(timezone.utc).isoformat(),
            'detector': {'name': 'jev', 'requested_model': detector.stats['model'],
                         'served_model_hint': detector.stats.get('served_by'),
                         'threshold': detector.threshold, 'batch': detector.batch,
                         'checker_sha256': file_hash(__file__),
                         'detector_sha256': file_hash(__import__('transcripto_jev').__file__)},
            'stats': detector.stats, 'findings': findings,
            'limit': 'Recorded model suggestions, not human labels. Unknown/excluded turns have no verdict. Serving hint is not a per-turn model guarantee. No task correctness or receiver adoption is established.'}

def selected(report_path, line, candidate=False):
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise ValueError('Select an exact positive --line from the report.')
    with open(report_path, encoding='utf-8') as stream:
        report = json.load(stream)
    if not isinstance(report, dict) or report.get('schema') != SCHEMA:
        raise ValueError('Not a recorded Jev findings report.')
    source = report.get('source')
    if not isinstance(source, str) or not os.path.isfile(source) or file_hash(source) != report.get('source_sha256'):
        raise ValueError('Source missing or changed since this observation. Re-run the selected inspection; no handoff created.')
    matches = [f for f in report.get('findings', []) if isinstance(f, dict) and f.get('line') == line]
    if len(matches) != 1:
        raise ValueError('Selected line is missing or ambiguous in the report.')
    finding = matches[0]
    if candidate and finding.get('status') != 'candidate':
        raise ValueError('Only an explicitly selected model candidate can be handed off.')
    p = finding.get('probability')
    if finding.get('status') in ('candidate', 'not_candidate') and (isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1):
        raise ValueError('Recorded probability is invalid.')
    rows, harness = core.read_session(source)
    eps = core.episodes(rows, source)
    index = next((i for i, ep in enumerate(eps) if ep['line'] == line), None)
    if file_hash(source) != report['source_sha256'] or index is None or text_hash(eps[index]['prompt']) != finding.get('request_sha256'):
        raise ValueError('Source no longer matches the selected request.')
    ep = eps[index]
    observation = {'source_sha256': report['source_sha256'], 'report_sha256': file_hash(report_path),
                   'observed_at': report.get('observed_at'), 'detector': report.get('detector'),
                   'finding': finding, 'fixture': report.get('fixture') is True,
                   'limit': 'Recorded model suggestion; not a human correction label or completed task.'}
    return report, ep, eps[index-1] if index else None, harness, observation
