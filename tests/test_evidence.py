"""Evidence references must resolve to the actual bytes, including after a refresh."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import transcripto as cli
import transcripto_evidence as evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.saved = cli.ROOTS, cli.HARNESS, cli.DB
        cli.ROOTS, cli.HARNESS, cli.DB = [str(self.root)], None, str(self.root / 'db' / 'trace.db')

    def tearDown(self):
        cli.ROOTS, cli.HARNESS, cli.DB = self.saved
        self.temp.cleanup()

    def query(self, term):
        with contextlib.redirect_stderr(io.StringIO()):
            con = cli.connect()
        try:
            return evidence.retrieve(con, term, cli._match(term), 5)
        finally:
            con.close()

    def test_record_reference_resolves_to_native_codex_line(self):
        path = self.root / 'codex.jsonl'
        rows = [{'type': 'session_meta', 'payload': {'id': 'persistent-id', 'cwd': '/relocated/project'}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                 'content': [{'type': 'input_text', 'text': 'Keep the offline parser'}]}}]
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        hit = self.query('offline parser')['hits'][0]
        ref = hit['source']
        self.assertEqual(ref['line_start'], 2)
        raw = path.read_bytes().splitlines()[ref['line_start'] - 1]
        self.assertEqual(ref['record_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(ref['source_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(hit['session_id'], 'persistent-id')
        self.assertEqual(hit['cwd'], '/relocated/project')
        self.assertEqual(hit['authorship']['kind'], 'unknown')

    def test_append_with_preserved_mtime_refreshes_reference_and_preserves_reversal(self):
        path = self.root / 'claude.jsonl'
        def request(text):
            return json.dumps({'type': 'user', 'promptSource': 'typed', 'message': {'content': text}}) + '\n'
        path.write_text(request('Use the hosted parser'))
        first = self.query('parser')['hits'][0]
        stamp = path.stat().st_mtime_ns
        with path.open('a') as stream:
            stream.write(request('No, reverse that. Use the offline parser'))
        os.utime(path, ns=(stamp, stamp))
        hits = self.query('parser')['hits']
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]['source']['line_start'], 2)
        self.assertNotEqual(first['source']['source_sha256'], hits[0]['source']['source_sha256'])
        self.assertEqual(hits[1]['source']['record_sha256'], first['source']['record_sha256'])

    def test_machine_paraphrase_cannot_replace_original_request(self):
        path = self.root / 'claude.jsonl'
        path.write_text('\n'.join(json.dumps(r) for r in [
            {'type': 'user', 'promptSource': 'typed', 'message': {'content': 'Keep SQLite'}},
            {'type': 'assistant', 'message': {'content': 'The user decided to replace SQLite with Postgres'}},
            {'type': 'user', 'promptSource': 'sdk', 'message': {'content': 'Use Postgres'}}]) + '\n')
        self.assertEqual(self.query('Postgres')['status'], 'no-match')
        self.assertEqual(self.query('SQLite')['hits'][0]['text'], 'Keep SQLite')

    def test_natural_question_terms_preserve_negation_and_topics(self):
        self.assertEqual(evidence.remembered_terms('Why did we choose SQLite?')[0], ['SQLite'])
        self.assertEqual(evidence.remembered_terms('Why did we not choose SQLite?')[0], ['not', 'SQLite'])
        self.assertEqual(evidence.remembered_terms('never delete backups')[0], ['never', 'delete', 'backups'])

    def test_partial_parse_is_visible_to_json_only_consumer(self):
        path = self.root / 'partial.jsonl'
        path.write_text(json.dumps({'type': 'user', 'promptSource': 'typed', 'message': {'content': 'Keep SQLite'}}) + '\n{"broken":')
        self.assertEqual(self.query('SQLite')['status'], 'matches')
        report = cli.sources.inventory(cli.ROOTS, database=cli.DB)
        source = report['sources'][0]
        self.assertEqual(source['state'], 'partial')
        self.assertTrue(any(w.get('basis') == 'indexed parse diagnostics' for w in source['warnings']))

    def test_index_observer_receives_committed_source_before_remaining_files(self):
        old, recent = self.root / 'old.jsonl', self.root / 'recent.jsonl'
        for path in (old, recent):
            path.write_text(json.dumps({'type': 'user', 'promptSource': 'typed', 'message': {'content': 'SQLite'}}) + '\n')
        os.utime(old, (1000000000, 1000000000))
        observed = []
        def observer(con, path):
            observed.append((path, con.execute('SELECT COUNT(*) FROM indexed').fetchone()[0]))
        con = cli.connect(on_indexed=observer)
        con.close()
        self.assertEqual(observed[0], (str(recent), 1))
        self.assertEqual(observed[1], (str(old), 2))

    def test_control_cleanup_preserves_unicode_newlines_and_tabs(self):
        value = ''.join(chr(i) for i in range(256)) + '雪🙂\n\t'
        expected = ''.join(c for c in value if c in '\n\t' or (ord(c) >= 32 and not 127 <= ord(c) < 160))
        self.assertEqual(cli.core.safe_text(value), expected)

    def test_parent_path_component_does_not_hide_indexed_evidence(self):
        (self.root / 'child').mkdir()
        path = self.root / 'one.jsonl'
        path.write_text(json.dumps({'type': 'user', 'promptSource': 'typed', 'message': {'content': 'relativeprobe'}}) + '\n')
        cli.ROOTS = [str(self.root / 'child' / '..')]
        self.assertEqual(self.query('relativeprobe')['hits'][0]['source']['path'], str(path))


if __name__ == '__main__':
    unittest.main()
