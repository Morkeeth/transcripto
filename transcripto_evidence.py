"""Local source identities and inspectable retrieval. No generated answers."""
import hashlib
import os
import re
from datetime import datetime, timezone

import transcripto_core as core


QUESTION_WORDS = frozenset('why where when what how did do does have has had was were is are i we you my our the a an about this that it for of to with before after choose chose chosen decide decided ask asked'.split())


def remembered_terms(query):
    """Remove question scaffolding, never negation or silently substitute a topic."""
    words = re.findall(r"[\w./:-]+", query, re.UNICODE)
    # A topic query is already intentional. Only natural-question openings opt in.
    if not words or words[0].lower() not in {'why', 'where', 'when', 'what', 'how', 'did', 'do', 'does', 'have', 'has'}:
        return words, []
    removed = [word for word in words if word.lower() in QUESTION_WORDS]
    return [word for word in words if word.lower() not in QUESTION_WORDS], removed


def version(path):
    """Hash bounded source bytes; reject a source observed changing during the read."""
    with open(path, "rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_size > core.MAX_FILE_BYTES:
            raise ValueError("source exceeds 128 MiB limit")
        digest = hashlib.sha256()
        remaining = core.MAX_FILE_BYTES + 1
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            if not block:
                break
            digest.update(block)
            remaining -= len(block)
        after = os.fstat(stream.fileno())
    current = os.stat(path)
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if remaining == 0 or signature(before) != signature(after) or signature(after) != signature(current):
        raise ValueError("source changed while being read; retry")
    return {"sha256": digest.hexdigest(), "bytes": after.st_size, "mtime_ns": after.st_mtime_ns}


def authorship(provider, prompt_source):
    if provider == "claude" and prompt_source in ("typed", "queued"):
        return {"kind": "human", "basis": "native promptSource=" + prompt_source}
    return {"kind": "unknown", "basis": "request inferred from provider envelope; human typing is not established"}


def reference(path, line, record_hash, source_hash):
    return {"path": path, "line_start": line, "line_end": line,
            "record_sha256": record_hash, "source_sha256": source_hash}


def retrieve(con, query, match, limit):
    rows = con.execute(
        "SELECT m.session_id,m.session_file,m.source_line,m.record_sha256,m.ts,m.cwd,"
        "m.harness,m.prompt_source,m.text,i.sha256,m.origin_session_id,m.inherited,m.timestamp_basis,m.native_session_id,m.parent_session_id FROM messages_fts "
        "JOIN messages m ON m.id=messages_fts.rowid JOIN indexed i ON i.session_file=m.session_file "
        "WHERE messages_fts MATCH ? AND COALESCE(m.inherited,0)!=1 AND "
        "(m.is_human=1 OR (m.harness IN ('codex','cursor') AND m.prompt_source IN ('typed','agent'))) "
        "AND COALESCE(m.prompt_source,'')!='echo' ORDER BY m.ts DESC,m.source_line DESC LIMIT ?",
        (match, limit)).fetchall()
    hits = []
    for sid, path, line, record_hash, ts, cwd, provider, psrc, text, source_hash, origin_sid, inherited, timestamp_basis, native_sid, parent_sid in rows:
        hits.append({"session_id": sid, "provider": provider, "timestamp": ts or None,
                     "cwd": cwd or None, "authorship": authorship(provider, psrc),
                     "origin_session_id": origin_sid, "inherited": bool(inherited) if inherited is not None else None,
                     "native_session_id": native_sid, "parent_session_id": parent_sid,
                     "timestamp_basis": timestamp_basis,
                     "text": text, "source": reference(path, line, record_hash, source_hash),
                     "inspect": ["transcripto", "replay", path, "--json"]})
    return {"schema": "transcripto.ask/1", "query": query,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "status": "matches" if hits else "no-match", "hits": hits,
            "selection": {"method": "all query terms, stemmed; newest recorded timestamp first", "limit": limit},
            "limitations": ["Matches are recorded requests, not answers or settled decisions.",
                            "Text is normalized, control characters removed, and bounded to 16000 characters; inspect original source lines.",
                            "Codex and Cursor request envelopes do not establish human authorship.",
                            "The source hash binds the indexed copy; revalidate before acting on it."]}


def describe(report):
    hits = report["hits"]
    if not hits:
        lines = ["nothing about '%s' in the selected request records. Try fewer terms." % report["query"], "No answer inferred."]
        for source in report.get("coverage", {}).get("sources", []):
            lines.append("%s · %s · %d supported file(s) · index %s" % (source["root"], source["state"], source["selected_files"], source['index']['state']))
        return "\n".join(lines)
    lines = ["%d recorded request%s · original evidence, newest first" % (len(hits), "" if len(hits) == 1 else "s")]
    if report.get('selection', {}).get('ignored_question_words'):
        lines.append('Searching topic terms: ' + ' '.join(report['selection']['query_terms']) + ' · use --literal to keep every word')
    for source in report.get('coverage', {}).get('sources', []):
        if source['state'] != 'available' or source['index']['state'] != 'fresh-by-mtime':
            lines.append('Coverage: %s · index %s · %s · inspect --json details' % (source['state'], source['index']['state'], source['root']))
    for hit in hits:
        source = hit["source"]
        label = "human" if hit["authorship"]["kind"] == "human" else "authorship unknown"
        lines.extend(["", "%s · %s · %s · %s" % (hit["timestamp"] or "time unknown", hit["provider"], label, hit["session_id"]),
                      hit["text"][:420] + ("… [use --json or source for more]" if len(hit["text"]) > 420 else ""),
                      "%s:%s" % (source["path"], source["line_start"])])
    lines.extend(["", "These are requests, not a verdict. Open the source to inspect replies and later corrections."])
    return "\n".join(lines)
