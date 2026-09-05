"""Continuation must carry selected evidence without manufacturing decisions."""
import json
import os
from pathlib import Path
import tempfile
import unittest

import transcripto_continuity as continuity
import transcripto_core as core


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'one.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rows):
        self.source.write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def request(self, text):
        return {'type': 'user', 'promptSource': 'typed', 'sessionId': 'one', 'message': {'content': text}}

    def test_read_only_answer_and_later_reversal_remain_separate(self):
        self.write([self.request('Keep the parser offline'),
                    {'type': 'assistant', 'message': {'content': 'No code change needed.'}},
                    self.request('Reverse that. Make the parser optional'),
                    self.request('PRIVATE OUTSIDE SELECTED RANGE')])
        doc = continuity.session(self.source, 1, 3)
        packet = continuity.packet(doc, settled=[3], reversed_lines=[1], next_action='Inspect the parser option')
        self.assertNotIn('PRIVATE OUTSIDE', json.dumps(packet))
        self.assertEqual([e['kind'] for e in packet['evidence']], ['request', 'response', 'request'])
        self.assertEqual(packet['settled_decisions'][0]['source']['line_start'], 3)
        self.assertEqual(packet['changed_or_reversed_decisions'][0]['source']['line_start'], 1)
        self.assertEqual(continuity.packet(doc)['settled_decisions'], [])
        with self.assertRaises(ValueError):
            continuity.packet(doc, settled=[2])  # agent response is not a reviewed request

    def test_no_result_evidence_escapes_the_selected_range(self):
        self.write([self.request('Try the change'),
                    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit', 'id': 'c', 'input': {'file_path': 'app.py'}}]}},
                    {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'c', 'is_error': True, 'content': 'PRIVATE ERROR OUTSIDE RANGE'}]}}])
        doc = continuity.session(self.source, 1, 2)
        self.assertNotIn('PRIVATE ERROR', json.dumps(doc))
        self.assertEqual(doc['timeline'][1]['status'], 'unknown')
        self.assertIsNone(doc['timeline'][1]['result_source'])
        full = continuity.session(self.source, 1, 3)
        self.assertEqual(full['timeline'][1]['status'], 'failed')
        self.assertEqual(full['timeline'][1]['result_source']['line_start'], 3)

    def test_packet_invalidates_even_with_same_size_and_preserved_mtime(self):
        self.write([self.request('Keep option A')])
        packet = continuity.packet(continuity.session(self.source, 1, 1))
        path = self.root / 'packet.json'
        continuity.write_private(path, packet)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(continuity.check_packet(path)['status'], 'current')
        stamp = self.source.stat().st_mtime_ns
        self.source.write_text(self.source.read_text().replace('option A', 'option B'))
        os.utime(self.source, ns=(stamp, stamp))
        self.assertEqual(continuity.check_packet(path)['status'], 'stale')
        with self.assertRaises(FileExistsError):
            continuity.write_private(path, packet)
        self.source.unlink()
        self.assertEqual(continuity.check_packet(path)['status'], 'unverifiable')

    def test_codex_inherited_parent_cannot_own_child_actions(self):
        self.write([
            {'type': 'session_meta', 'ordinal': 0, 'payload': {'id': 'child', 'parent_thread_id': 'parent', 'thread_source': 'subagent', 'subagent_history_start_ordinal': 3, 'cwd': '/old/relocated'}},
            {'type': 'session_meta', 'ordinal': 1, 'payload': {'id': 'parent'}},
            {'type': 'response_item', 'ordinal': 2, 'payload': {'type': 'message', 'role': 'user', 'content': [{'text': 'Parent question'}]}},
            {'type': 'response_item', 'ordinal': 3, 'payload': {'type': 'function_call', 'name': 'exec_command', 'call_id': 'c', 'arguments': '{"cmd":"pytest"}'}}])
        rows, _ = core.read_session(self.source)
        self.assertEqual({r['sessionId'] for r in rows}, {'child'})
        self.assertTrue(rows[0]['_inherited'])
        self.assertEqual(core.episodes(rows)[0]['events'], [])
        doc = continuity.session(self.source)
        self.assertEqual(doc['identity']['parent_session_id'], 'parent')
        self.assertEqual(doc['identity']['session_id'], 'child')
        self.assertEqual(doc['timeline'][0]['origin_session_id'], 'parent')
        self.assertEqual(doc['timeline'][1]['origin_session_id'], 'child')
        self.assertEqual(doc['repository']['status'], 'recorded-path-unavailable')

    def test_partial_and_unsupported_do_not_become_zero_work(self):
        self.write([self.request('A real request')])
        with self.source.open('a') as stream:
            stream.write('{"type":')
        doc = continuity.session(self.source)
        self.assertEqual(doc['coverage']['state'], 'partial')
        self.assertTrue(doc['coverage']['warnings'])
        self.write([{'unknown_format': True}])
        doc = continuity.session(self.source)
        self.assertEqual(doc['coverage']['state'], 'unsupported-or-empty')
        self.assertEqual(doc['work_state'], 'unknown')
        self.assertIsNone(doc['identity']['provider'])

    def test_cursor_context_clock_is_not_native_activity_time(self):
        self.write([{'role': 'user', 'message': {'content': '<user_query>Inspect the parser</user_query>'}}])
        doc = continuity.session(self.source)
        self.assertIsNone(doc['started_at'])
        self.assertIsNone(doc['last_observed_at'])
        self.assertEqual(doc['timeline'][0]['timestamp_basis'], 'unknown')
        self.assertEqual(doc['timeline'][0]['authorship']['kind'], 'unknown')

    def test_multi_file_change_keeps_each_artifact_reference(self):
        self.write([self.request('Update both modules'),
                    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'apply_patch', 'id': 'p',
                     'input': {'patch': '*** Begin Patch\n*** Update File: a.py\n@@\n-old\n+new\n*** Update File: b.py\n@@\n-old\n+new\n*** End Patch'}}]}}])
        action = continuity.session(self.source)['timeline'][1]
        self.assertEqual(action['artifact_paths'], ['a.py', 'b.py'])
        self.assertEqual(action['status'], 'unknown')

    def test_nested_cursor_agent_instructions_are_not_human_requests(self):
        import transcripto as cli
        root = self.root / '.cursor'
        path = root / 'projects' / 'project' / 'agent-transcripts' / 'parent' / 'subagents' / 'child.jsonl'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'role': 'user', 'message': {'content': '<user_query>Inspect this module</user_query>'}}) + '\n')
        self.assertIn(str(path), cli._coach_files([str(root)], 'cursor'))
        rows, _ = core.read_session(path)
        self.assertFalse(any(core.human_text(r) for r in rows))
        document = continuity.session(path)
        self.assertEqual(document['identity']['parent_session_id'], 'parent')
        self.assertEqual(document['identity']['kind'], 'subagent')
        self.assertEqual(document['identity']['kind_basis'], 'transcript directory convention')
        self.assertEqual(document['timeline'][0]['kind'], 'agent_instruction')

    def test_embedded_sidechain_record_does_not_rename_the_parent_session(self):
        self.write([self.request('Parent request'), dict(self.request('Child instruction'), isSidechain=True)])
        document = continuity.session(self.source)
        self.assertEqual(document['identity']['session_id'], 'one')
        self.assertIsNone(document['identity']['parent_session_id'])
        self.assertNotEqual(document['identity']['kind'], 'subagent')

    def test_filename_identity_does_not_claim_a_native_metadata_id(self):
        self.write([{'role': 'user', 'message': {'content': '<user_query>A request</user_query>'}}])
        identity = continuity.session(self.source)['identity']
        self.assertEqual(identity['session_id'], 'one')
        self.assertEqual(identity['session_id_basis'], 'transcript filename')
        self.assertIsNone(identity['native_session_id'])


if __name__ == '__main__':
    unittest.main()
