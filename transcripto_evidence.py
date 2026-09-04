"""Local source identities and inspectable retrieval. No generated answers."""
import hashlib
import os
from datetime import datetime, timezone

import transcripto_core as core


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
        "m.harness,m.prompt_source,m.text,i.sha256 FROM messages_fts "
        "JOIN messages m ON m.id=messages_fts.rowid JOIN indexed i ON i.session_file=m.session_file "
        "WHERE messages_fts MATCH ? AND m.is_human=1 ORDER BY m.ts DESC,m.source_line DESC LIMIT ?",
        (match, limit)).fetchall()
    hits = []
    for sid, path, line, record_hash, ts, cwd, provider, psrc, text, source_hash in rows:
        hits.append({"session_id": sid, "provider": provider, "timestamp": ts or None,
                     "cwd": cwd or None, "authorship": authorship(provider, psrc),
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
            lines.append("%s · %s · %d supported file(s)" % (source["root"], source["state"], source["selected_files"]))
        return "\n".join(lines)
    lines = ["%d recorded request%s · original evidence, newest first" % (len(hits), "" if len(hits) == 1 else "s")]
    for hit in hits:
        source = hit["source"]
        label = "human" if hit["authorship"]["kind"] == "human" else "authorship unknown"
        lines.extend(["", "%s · %s · %s · %s" % (hit["timestamp"] or "time unknown", hit["provider"], label, hit["session_id"]),
                      hit["text"][:420] + ("… [use --json or source for more]" if len(hit["text"]) > 420 else ""),
                      "%s:%s" % (source["path"], source["line_start"])])
    lines.extend(["", "These are requests, not a verdict. Open the source to inspect replies and later corrections."])
    return "\n".join(lines)
