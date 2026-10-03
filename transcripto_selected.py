"""Bounded, explicit local source selection. No index refresh or model call."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
import transcripto_core as core

LIMIT = 16 * 1024 * 1024

def describe(source):
    path = Path(source).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError('Choose an existing session file of at most 16 MiB.')
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def runs(index, cwd, limit=20):
    if not cwd or not 1 <= limit <= 30:
        raise ValueError('Choose an exact cwd and limit from 1 to 30.')
    requested = str(Path(cwd).expanduser().absolute())
    target = str(Path(cwd).expanduser().resolve(strict=True))
    db = Path(index).expanduser().resolve(strict=True)
    con = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=1)
    try:
        con.execute('PRAGMA query_only=ON')
        deadline = time.monotonic() + 2
        con.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        # Producer-owned schema: only allowlisted metadata columns, no text/title.
        rows = con.execute('''SELECT session_file, session_id, harness, cwd,
            MIN(ts), MAX(ts), COUNT(*) FROM (SELECT session_file, session_id, harness, cwd, ts FROM messages ORDER BY rowid DESC LIMIT 20000) WHERE cwd IN (?,?)
            GROUP BY session_file, session_id, harness, cwd
            ORDER BY MAX(ts) DESC LIMIT ?''', (requested, target, limit)).fetchall()
        return {'schema': 'transcripto.selected-runs/1', 'index': str(db),
                'cwd': target, 'runs': [{'source': row[0], 'session_id': row[1],
                'harness': row[2], 'cwd': row[3], 'first_at': row[4],
                'last_at': row[5], 'indexed_records': row[6],
                'relationship': 'unbound suggestion; explicitly choose the relevant run'} for row in rows],
                'limit': limit, 'metadata_window_records': 20000, 'notice': 'Read-only metadata from at most the most recent 20000 indexed records, possibly stale or incomplete. No title or transcript body. No inferred authorship. SQLite may use locking sidecars.'}
    finally:
        con.close()

def source_session(source, accepted):
    """Identity only from the exact consented bytes; never filename/index fallbacks."""
    data = Path(source).read_bytes()
    if hashlib.sha256(data).hexdigest() != accepted:
        raise ValueError('Selected source changed.')
    identities = set()
    messages = 0
    try:
        for line in data.decode('utf-8').splitlines():
            if not line.strip(): continue
            row = json.loads(line)
            if not isinstance(row, dict): raise ValueError('Ambiguous source identity.')
            if row.get('type') in ('session_meta', 'response_item') or 'role' in row or 'session_id' in row:
                raise ValueError('New Claude session requires an unmixed Claude source.')
            if 'sessionId' in row:
                identities.add(str(uuid.UUID(row['sessionId'])))
            if row.get('type') in ('user', 'assistant'):
                messages += 1
                if not row.get('sessionId'): raise ValueError('Source message has no explicit session identity.')
        if not messages or len(identities) != 1:
            raise ValueError('Source session identity is absent or mixed.')
    except (TypeError, AttributeError, UnicodeError) as exc:
        raise ValueError('Invalid source session identity.') from exc
    return {'harness':'claude', 'session_id':next(iter(identities)), 'basis':'exact consented source bytes; local unsigned record'}

def episodes(source, accepted):
    ref = describe(source)
    if ref['sha256'] != accepted:
        raise ValueError('Selected source changed; inspect metadata and consent again.')
    diagnostics = []
    rows, harness = core.read_session(ref['path'], diagnostics)
    if diagnostics or describe(ref['path']) != ref:
        raise ValueError('Source changed or has parsing warnings; no selected replay.')
    eps = core.episodes(rows, ref['path'])
    try: identity = source_session(ref['path'], accepted); identity_reason = None
    except ValueError as exc: identity = None; identity_reason = str(exc)
    return {'schema':'transcripto.selected-episodes/1', 'source':ref,
            'harness':harness, 'source_session':identity, 'source_session_reason':identity_reason, 'episodes':[{'line':ep['line'], 'request':ep['prompt'],
              'events':ep['events'], 'synthetic':ep['synthetic']} for ep in eps[:100]],
            'truncated':len(eps)>100, 'notice':'Selected local replay only. Tool results are not task correctness. Request authorship follows source provenance, not independent identity verification.'}

def authored(source, accepted, line, instruction):
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise ValueError('Choose one exact request line.')
    if not isinstance(instruction, str) or not instruction.strip() or len(instruction)>32000:
        raise ValueError('Provide one bounded explicitly authored instruction.')
    view = episodes(source, accepted)
    matches = [ep for ep in view['episodes'] if ep['line']==line]
    if len(matches)!=1:
        raise ValueError('Selected request is missing or ambiguous.')
    ep=matches[0]
    return {'harness':view['harness'], 'source':view['source']['path'], 'line':line,
            'correction':instruction, 'previous_request':ep['request'],
            'synthetic':ep['synthetic'], 'events':ep['events'],
            'source_sha256':accepted,
            'instruction_origin':'explicitly authored instruction; not a detector verdict or research label'}

def main(args):
    try:
        if args.mode == 'runs': value=runs(args.index, args.cwd, args.limit)
        elif args.mode == 'describe': value={'schema':'transcripto.selected-source/1','source':describe(args.source), 'notice':'File identity only. Confirm local viewing before reading requests or results.'}
        elif args.mode in ('episodes', 'authored-continuation'):
            if not args.consent: raise ValueError('Explicit --consent is required to read this session locally.')
            value=episodes(args.source,args.accept_sha)
            if args.mode == 'authored-continuation':
                identity=source_session(args.source,args.accept_sha)
                value={'schema':'transcripto.authored-continuation/1','mode':'authored-new-session','source_session':identity, **authored(args.source,args.accept_sha,args.line,args.instruction)}
        else: raise ValueError('Unknown selected context action.')
        print(json.dumps(value,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,sqlite3.Error) as exc:
        import sys
        print('Selected context refused: '+str(exc),file=sys.stderr)
        return 2
