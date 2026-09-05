"""Version-bound local session evidence and caller-selected continuation packets."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import transcripto_core as core
import transcripto_evidence as evidence


def repository(cwd):
    """Inspect the recorded path now. A missing old worktree is not a missing repo."""
    result = {"recorded_cwd": cwd or None, "worktree": None, "git_dir": None,
              "common_dir": None, "status": "unknown"}
    if not cwd:
        return result
    folder = Path(cwd).expanduser()
    if not folder.is_dir():
        result["status"] = "recorded-path-unavailable"
        return result
    for parent in (folder, *folder.parents):
        git = parent / '.git'
        try:
            if git.is_file():
                text = git.read_text()[:4096].strip()
                if not text.startswith('gitdir:'):
                    continue
                git = (parent / text.partition(':')[2].strip()).resolve()
            if not git.is_dir():
                continue
            common = git
            if (git / 'commondir').is_file():
                common = (git / (git / 'commondir').read_text().strip()).resolve()
            result.update(worktree=str(parent), git_dir=str(git), common_dir=str(common), status="observed-local-git")
            return result
        except OSError:
            result["status"] = "inaccessible"
            return result
    result["status"] = "no-git-at-recorded-path"
    return result


def _stamp(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return stamp.astimezone(timezone.utc).isoformat() if stamp.tzinfo else None
    except ValueError:
        return None


def session(path, start_line=None, end_line=None):
    path = str(Path(path).expanduser().absolute())
    before = evidence.version(path)
    warnings = []
    rows, provider = core.read_session(path, warnings)
    raw = list(core.iter_json(path, []))
    after = evidence.version(path)
    if before != after:
        raise ValueError("source changed while building evidence; retry")
    recognized = provider in ('claude', 'codex', 'cursor') and bool(rows)
    meta = next((r for r in raw if r.get('type') == 'session_meta'), None)
    payload = meta.get('payload', {}) if meta else {}
    sid = payload.get('id') or next((r.get('sessionId') for r in rows if r.get('sessionId')), Path(path).stem)
    parent = payload.get('parent_thread_id') or payload.get('forked_from_id')
    source = payload.get('source')
    spawn = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) and isinstance(source.get('subagent'), dict) else {}
    parent = parent or spawn.get('parent_thread_id')
    parent_basis = 'native session metadata' if parent else 'unknown'
    kind = payload.get('thread_source') or ('subagent' if spawn else None)
    kind = kind or next((r.get('_session_kind') for r in rows if r.get('_session_kind')), None)
    raw_messages = [r for r in raw if r.get('type') in ('user', 'assistant')]
    all_sidechain = bool(raw_messages) and all(r.get('isSidechain') is True for r in raw_messages)
    if provider == 'claude' and (all_sidechain or 'subagents' in Path(path).parts):
        kind = 'subagent'
    native_sid = payload.get('id') or next((r.get('sessionId') for r in raw if r.get('sessionId')), None)
    compound_sid = provider == 'claude' and kind == 'subagent' and native_sid is not None
    if compound_sid:
        if not parent:
            parent = native_sid
            parent_basis = 'sidechain context and native shared session ID'
        sid = native_sid + '/' + Path(path).stem
    if not parent and 'subagents' in Path(path).parts:
        parent = Path(path).parent.parent.name
        parent_basis = 'transcript directory convention; not native parent metadata'
    # Metadata may include inherited parent history. Keep the file owner stable.
    owned = [r for r in rows if r.get('_inherited') is not True]
    cwd = next((r.get('cwd') for r in reversed(owned) if r.get('cwd')), payload.get('cwd'))
    stamps = [_stamp(r.get('timestamp')) for r in owned if r.get('_timestamp_basis', 'native record') == 'native record']
    stamps = [s for s in stamps if s]
    raw_by_line = {r['_line']: r for r in raw}
    def ref(line):
        row = raw_by_line.get(line, {})
        return evidence.reference(path, line, row.get('_record_sha256'), after['sha256'])
    timeline = []
    for row in rows:
        line = row['_line']
        if (start_line is not None and line < start_line) or (end_line is not None and line > end_line):
            continue
        common = {"source": ref(line), "timestamp": row.get('timestamp') or None,
                  "channel": row.get('_channel'),
                  "timestamp_basis": row.get('_timestamp_basis', 'native record' if row.get('timestamp') else 'unknown'),
                  "inherited": row.get('_inherited'), "origin_session_id": row.get('_origin_session_id') or sid}
        request = core.human_text(row)
        if request:
            timeline.append(dict(common, kind='request', text=core.safe_text(request),
                                 authorship=evidence.authorship(provider, row.get('promptSource'))))
            continue
        content = (row.get('message') or {}).get('content')
        if row.get('type') == 'assistant' and isinstance(content, str) and content:
            timeline.append(dict(common, kind='response', text=core.safe_text(content), authorship={"kind": "agent"}))
        for block in content if isinstance(content, list) else []:
            if block.get('type') == 'text' and row.get('type') == 'assistant':
                timeline.append(dict(common, kind='response', text=core.safe_text(block.get('text', '')), authorship={"kind": "agent"}))
            elif block.get('type') == 'tool_use':
                inputs = block.get('input') or {}
                target = inputs.get('file_path') or inputs.get('command') or block.get('original_name')
                artifacts = inputs.get('paths') or ([inputs['file_path']] if isinstance(inputs.get('file_path'), str) else [])
                result_line = block.get('result_line')
                result_selected = result_line is not None and (start_line is None or result_line >= start_line) and (end_line is None or result_line <= end_line)
                timeline.append(dict(common, kind='action', operation=core.operation(block),
                                     tool=block.get('original_name'), target=core.safe_text(target),
                                     artifact_paths=[core.safe_text(p) for p in artifacts if isinstance(p, str)],
                                     status=block.get('execution_status', 'unknown') if result_selected else 'unknown',
                                     evidence=core.safe_text(block.get('evidence', '')) if result_selected else 'No matching result inside the selected range.',
                                     result_source=ref(result_line) if result_selected else None,
                                     result_timestamp=(raw_by_line.get(result_line, {}).get('timestamp') or None) if result_selected else None))
            elif block.get('type') == 'tool_result':
                timeline.append(dict(common, kind='recorded_tool_result', call_id=block.get('tool_use_id'),
                                     content_omitted=True))
        if row.get('promptSource') == 'agent':
            timeline.append(dict(common, kind='agent_instruction', text=core.safe_text(core.text_of(content)), authorship={"kind": "agent"}))
    handled = {r['_line'] for r in rows}
    other = Counter(str(r.get('type', r.get('role', 'unknown'))) + (':' + str(r.get('payload', {}).get('type')) if r.get('type') == 'response_item' else '') for r in raw if r['_line'] not in handled)
    return {"schema": "transcripto.session/1", "observed_at": datetime.now(timezone.utc).isoformat(),
            "identity": {"session_id": sid, "provider": provider if recognized else None,
                         "native_session_id": native_sid,
                         "session_id_basis": "native session ID plus subagent filename" if compound_sid else ("native metadata" if native_sid else "transcript filename"),
                         "kind": kind or 'unknown', "parent_session_id": parent, "parent_basis": parent_basis,
                         "kind_basis": 'native metadata' if payload.get('thread_source') or spawn else ('native message sidechain flags' if provider == 'claude' and all_sidechain else ('transcript directory convention' if kind == 'subagent' else 'unknown')),
                         "metadata_source": ref(meta['_line']) if meta else None},
            "repository": repository(cwd), "source_version": dict(after, path=path),
            "started_at": min(stamps) if stamps else None, "last_observed_at": max(stamps) if stamps else None,
            "work_state": "unknown", "timeline": timeline,
            "coverage": {"state": 'partial' if warnings else ('parsed' if recognized else 'unsupported-or-empty'),
                         "warnings": warnings, "unmapped_record_types": dict(other),
                         "selected_lines": [start_line, end_line], "normalized_records": len(rows)},
            "limitations": ["Source order is not causality. Tool success is not task correctness.",
                            "Requests and responses are preserved; settled decisions require caller review.",
                            "Latest observed timestamp is not proof of ongoing work or completion.",
                            "Repository paths are transcript metadata checked against the local filesystem now; relocated paths remain unknown.",
                            "Cursor context clocks are not per-message timestamps. Unmapped records are not zero activity.",
                            "This local export contains selected private text. No upload is performed."]}


def packet(document, question=None, settled=(), reversed_lines=(), next_action=None):
    bounds = document['coverage']['selected_lines']
    if bounds[0] is None or bounds[1] is None:
        raise ValueError('a packet requires explicit --from-line and --to-line; inspect --timeline first')
    if bounds[0] < 1 or bounds[1] < bounds[0]:
        raise ValueError('invalid selected line range')
    requests = {e['source']['line_start']: e for e in document['timeline'] if e['kind'] == 'request'}
    if not requests:
        raise ValueError('selected range contains no request; choose a range with the original question')
    if set(settled) & set(reversed_lines):
        raise ValueError('one request cannot be both settled and reversed in this packet')
    if any(line not in requests for line in (*settled, *reversed_lines)):
        raise ValueError('decision classifications must reference request lines inside the selected range')
    classify = lambda lines: [dict(requests[line], classification_basis='caller-selected; not inferred by Transcripto') for line in lines]
    return {"schema": "transcripto.packet/1", "created_at": document['observed_at'],
            "identity": document['identity'], "source_version": document['source_version'],
            "selection": {"from_line": bounds[0], "to_line": bounds[1], "basis": "explicit caller selection"},
            "current_question": {"text": question, "basis": "caller annotation"} if question else requests[min(requests)],
            "settled_decisions": classify(settled), "changed_or_reversed_decisions": classify(reversed_lines),
            "next_action": {"text": next_action, "basis": "caller annotation"} if next_action else None,
            "uncertainty": ["Unclassified requests remain unresolved; order alone does not establish reversal or agreement.",
                            "Evidence outside the selected range has not been reviewed.",
                            "Check source freshness before continuing. A changed source invalidates this packet."] + ([] if next_action else ["No next action was selected."]),
            "evidence": document['timeline'], "coverage": document['coverage'],
            "privacy": {"local_only": True, "upload_performed": False, "contains_private_text": True},
            "limitations": document['limitations']}


def check_packet(path):
    with open(path) as stream:
        packet = json.load(stream)
    if packet.get('schema') != 'transcripto.packet/1':
        raise ValueError('expected a transcripto.packet/1 file')
    source = packet.get('source_version') or {}
    try:
        current = evidence.version(source['path'])
        status = 'current' if current['sha256'] == source.get('sha256') else 'stale'
        reason = None
    except (OSError, ValueError, KeyError) as exc:
        current, status, reason = None, 'unverifiable', str(exc)
    return {"schema": "transcripto.packet-check/1", "status": status,
            "expected_sha256": source.get('sha256'), "observed_sha256": current['sha256'] if current else None,
            "reason": reason, "checked_at": datetime.now(timezone.utc).isoformat(),
            "scope": "Source-byte freshness only; decision correctness and packet tampering are not verified."}


def write_private(path, document):
    """Exclusive creation avoids destroying a reviewed packet or following a symlink."""
    with open(os.open(os.path.expanduser(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def describe(document):
    identity = document['identity']
    lines = ['%s · %s · source timeline' % (identity['provider'] or 'unknown provider', identity['session_id'])]
    for event in document['timeline']:
        line = event['source']['line_start']
        text = event.get('text') or event.get('target') or 'result recorded; raw output omitted'
        inherited = ' · inherited context' if event['inherited'] else ''
        lines.append('%s:%s · %s · %s%s%s' % (event['source']['path'], line,
                     event['timestamp'] or 'time unknown', event['kind'],
                     (' · ' + event['status']) if 'status' in event else '', inherited))
        lines.append('  ' + ' '.join(text.split())[:400])
        if 'evidence' in event:
            lines.append('  ' + event['evidence'])
    lines.extend(['', 'Source order is not causality. Tool success is not task correctness.',
                  'Choose a line range for export-run --packet; no decisions are inferred.'])
    return '\n'.join(lines)
