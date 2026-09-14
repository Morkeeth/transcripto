"""Cold install -> automatic discovery -> exact replay; all records invented.

Set TRANSCRIPTO_TEST_CLI to an installed console script to exercise a wheel.
Every subprocess runs outside the checkout with a fresh HOME and no PYTHONPATH.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="transcripto-cold-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.cli = ([os.environ['TRANSCRIPTO_TEST_CLI']] if os.environ.get('TRANSCRIPTO_TEST_CLI')
                    else [sys.executable, str(ROOT / 'transcripto.py')])
        self.env = dict(os.environ, HOME=str(self.home), PYTHONIOENCODING='utf-8')
        self.env.pop('PYTHONPATH', None)

    def run_cli(self, *args):
        return subprocess.run(self.cli + list(args), cwd=self.home, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def write(self, relative, records):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(r) + '\n' for r in records))
        return path

    def test_discover_search_and_open_exact_cross_harness_request(self):
        human = lambda text: {'type': 'user', 'promptSource': 'typed',
                              'message': {'content': text}}
        self.write(".claude/projects/project with 'quotes'/session.jsonl", [
            human('We retried the amber upload.'),
            {'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'name': 'Edit', 'id': 'edit',
                 'input': {'file_path': 'upload.py'}}]}},
            {'type': 'user', 'message': {'content': [
                {'type': 'tool_result', 'tool_use_id': 'edit', 'is_error': True,
                 'content': 'Permission denied'}]}},
            human('Explain caching instead.'),
        ])
        self.write('.codex/archived_sessions/archived.jsonl', [
            {'type': 'session_meta', 'payload': {'id': 'codex-archive'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                'content': [{'type': 'input_text', 'text': 'We retried the cobalt upload.'}]}},
            {'type': 'response_item', 'payload': {'type': 'function_call', 'call_id': 'shell',
                'name': 'exec_command', 'arguments': json.dumps({'cmd': 'pytest upload.py'})}},
            {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'shell',
                'output': json.dumps({'exit_code': 0, 'output': '1 passed'})}},
        ])
        self.write('.cursor/projects/demo/agent-transcripts/session/session.jsonl', [
            {'role': 'user', 'message': {'content': '<user_query>We retried the jade upload.</user_query>'}},
            {'role': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'StrReplace',
                'id': 'replace', 'input': {'path': 'upload.py', 'old_string': 'a', 'new_string': 'b'}}]}},
            {'role': 'assistant', 'message': {'content': 'All fixed.'}},
        ])
        # FTS stemming finds retried; literal replay of "retry" cannot.
        query = self.run_cli('ask', 'retry')
        self.assertEqual(query.returncode, 0, query.stderr)
        self.assertIn('3 messages you typed', query.stdout)
        commands = [shlex.split(line.strip()[6:]) for line in query.stdout.splitlines()
                    if line.strip().startswith('Open: ')]
        self.assertEqual(len(commands), 3, query.stdout)
        observed = {}
        for command in commands:
            result = self.run_cli(*command[1:], '--json')
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            episodes = json.loads(result.stdout)['episodes']
            self.assertEqual(len(episodes), 1)
            ep = episodes[0]
            self.assertIn('retried', ep['prompt'])
            observed[ep['harness']] = ep['events'][0]['status']
        self.assertEqual(observed, {'claude': 'failed', 'codex': 'succeeded', 'cursor': 'unknown'})
        self.assertEqual((self.home / '.trace/trace.db').stat().st_mode & 0o777, 0o600)
        scoped = self.run_cli('ask', 'retry', '--harness', 'cursor')
        self.assertIn('1 message you typed', scoped.stdout)
        self.assertNotIn('amber', scoped.stdout)
        self.assertNotIn('cobalt', scoped.stdout)

    def test_installed_example_stays_synthetic_through_open_and_handoff(self):
        imported = self.run_cli('import-example')
        self.assertEqual(imported.returncode, 0, imported.stderr)
        query = self.run_cli('ask', 'forecast cache')
        self.assertEqual(query.returncode, 0, query.stderr)
        self.assertIn('SYNTHETIC EXAMPLE', query.stdout)
        self.assertNotIn('messages you typed', query.stdout)
        commands = [shlex.split(line.strip()[6:]) for line in query.stdout.splitlines()
                    if line.strip().startswith('Open: ')]
        self.assertEqual(len(commands), 3, query.stdout)
        for command in commands:
            replay = self.run_cli(*command[1:], '--json')
            self.assertEqual(replay.returncode, 0, replay.stderr)
            data = json.loads(replay.stdout)
            self.assertTrue(data['synthetic'])
            self.assertEqual(len(data['episodes']), 1)
            share = self.run_cli(*command[1:], '--share')
            self.assertIn('Synthetic', share.stdout)
        packet, brief = self.home / 'packet.json', self.home / 'brief.md'
        handed = self.run_cli('handoff', 'No, use 30 seconds', '--to-harness',
                              'cursor', '--output', str(packet))
        self.assertEqual(handed.returncode, 0, handed.stderr)
        data = json.loads(packet.read_text())
        self.assertTrue(data['synthetic'])
        self.assertIn('receiver acknowledgement', data['missing'])
        prepared = self.run_cli('receive-handoff', str(packet), '--as-harness',
                                'cursor', '--output', str(brief))
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertIn('SYNTHETIC EXAMPLE', brief.read_text())
        self.assertIn('acknowledgement pending', brief.read_text())
        self.assertEqual(packet.stat().st_mode & 0o777, 0o600)
        self.assertEqual(brief.stat().st_mode & 0o777, 0o600)

    def test_exact_line_does_not_fall_back_to_another_request(self):
        path = self.write('session.jsonl', [
            {'type': 'user', 'promptSource': 'typed', 'message': {'content': 'First'}},
            {'type': 'assistant', 'message': {'content': 'Reply'}},
            {'type': 'user', 'promptSource': 'typed', 'message': {'content': 'Second'}},
        ])
        wrong = self.run_cli('replay', str(path), '--line', '2')
        self.assertEqual(wrong.returncode, 2)
        self.assertIn('No human request starts at line 2', wrong.stdout)
        self.assertNotIn('You asked:', wrong.stdout)
        path.unlink()
        missing = self.run_cli('replay', str(path), '--line', '1')
        self.assertEqual(missing.returncode, 2)
        self.assertIn('moved or been deleted', missing.stdout)
        missing_json = self.run_cli('replay', str(path), '--line', '1', '--json')
        self.assertEqual(missing_json.returncode, 2)
        self.assertEqual(json.loads(missing_json.stdout)['episodes'], [])
        self.assertTrue(json.loads(missing_json.stdout)['warnings'])

    def test_empty_home_is_not_a_demo_or_a_success(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('No matching human session', result.stdout)
        self.assertNotIn('You asked:', result.stdout)

    def test_missing_root_is_an_input_error_not_empty_history(self):
        for command in ("ask", "replay"):
            result = self.run_cli(command, "retry", "--root", str(self.home / "typo"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("--root does not exist", result.stderr)

    def test_line_requires_a_positive_exact_source(self):
        for args in [('replay', '--line', '1'), ('replay', 'x', '--line', '0'),
                     ('replay', 'x', '--line', '1', '--episode', '1')]:
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
