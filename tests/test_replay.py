"""Adversarial contracts: a result must belong to the call it claims to prove."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import transcripto as app
import transcripto_core as core
import transcripto_replay as replay

ROOT = Path(__file__).resolve().parents[1]


def user(text='Fix login.py'):
    return {'type': 'user', 'promptSource': 'typed', 'message': {'content': text}}


def call(name='Edit', args=None, cid='c1'):
    return {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': cid,
        'name': name, 'input': args if args is not None else {'file_path': 'login.py'}}]}}


def result(text='File updated successfully', error=False, cid='c1'):
    return {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': cid,
        'content': text, 'is_error': error}]}}


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def read(self, records, name='session.jsonl'):
        path = self.root / name
        path.write_text(''.join(json.dumps(r) + '\n' for r in records))
        return core.read_session(str(path))[0]

    def event(self, records):
        return core.episodes(self.read(records))[0]['events'][0]


class TranscriptTests(FixtureCase):
    def test_mixed_wrapper_is_not_a_single_command(self):
        c = core.normalize_call({'name': 'exec', 'input': 'await tools.exec_command({cmd: "git commit"}); await tools.apply_patch("patch");'})
        self.assertEqual(core.operation(c), 'tool')

    def test_raw_status_cannot_supply_evidence(self):
        for status in ('succeeded', 'invented'):
            c = call()
            c['message']['content'][0]['execution_status'] = status
            self.assertEqual(self.event([user(), c])['status'], 'unknown')

    def test_cursor_query_after_long_context(self):
        rows = self.read([{'role': 'user', 'message': {'content': [
            {'type': 'text', 'text': 'context ' * 4000 + '<user_query>Find this request</user_query>'}]}}])
        self.assertEqual(core.episodes(rows)[0]['prompt'], 'Find this request')

    def test_codex_shell_command_arrays(self):
        for name in ('shell', 'container.exec', 'local_shell'):
            c = core.normalize_call({'name': name, 'input': {'command': ['bash', '-lc', 'git commit -m fix']}})
            self.assertEqual(core.operation(c), 'commit')

    def test_local_shell_action_payload(self):
        rows = self.read([{'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': 'Commit it'}},
            {'type': 'response_item', 'payload': {'type': 'local_shell_call', 'call_id': 'c1', 'action': {'command': ['bash', '-lc', 'git commit -m fix']}}}])
        self.assertEqual(core.episodes(rows)[0]['events'][0]['kind'], 'commit')

    def test_punctuation_inside_commit_message(self):
        c = core.normalize_call({'name': 'Bash', 'input': {'command': 'git commit -m "fix login; keep tests"'}})
        self.assertEqual(core.operation(c), 'commit')

    def test_multiedit_completion(self):
        self.assertEqual(self.event([user(), call('MultiEdit'), result('Applied 2 edits to login.py:', None)])['status'], 'succeeded')

    def test_failed_edit_is_failed(self):
        e = self.event([user(), call(), result('Permission denied', True)])
        self.assertEqual(e['status'], 'failed')
        self.assertEqual(e['result_line'], 3)

    def test_success_needs_matching_id(self):
        e = self.event([user(), call(), result(cid='different')])
        self.assertEqual(e['status'], 'unknown')

    def test_missing_result_is_unknown(self):
        self.assertEqual(self.event([user(), call()])['status'], 'unknown')

    def test_non_shell_result_needs_explicit_change_success(self):
        self.assertEqual(self.event([user(), call(), result('pending', None)])['status'], 'unknown')

    def test_failed_commit(self):
        e = self.event([user(), call('Bash', {'command': 'git commit -m fix'}), result('Exit code: 1', True)])
        self.assertEqual((e['kind'], e['status']), ('commit', 'failed'))

    def test_quoted_commit_is_not_commit(self):
        e = self.event([user(), call('Bash', {'command': "printf '%s' 'git commit'"}), result('Exit code: 0')])
        self.assertEqual(e['kind'], 'shell')

    def test_compound_shell_is_not_a_proven_commit(self):
        e = self.event([user(), call('Bash', {'command': 'git commit -m fix || true'}), result('Exit code: 0')])
        self.assertEqual(e['kind'], 'shell')

    def test_dry_run_is_not_commit(self):
        self.assertEqual(core.operation(core.normalize_call({'name': 'Bash', 'input': {'command': 'git commit --dry-run'}})), 'shell')

    def test_success_after_new_prompt_stays_with_original_call(self):
        rows = self.read([user('Fix login.py'), call(), user('Explain caching'), result()])
        eps = core.episodes(rows)
        self.assertEqual(len(eps), 2)
        self.assertEqual(eps[0]['events'][0]['status'], 'succeeded')
        self.assertEqual(eps[1]['events'], [])

    def test_tool_result_is_never_human_even_with_typed_flag(self):
        r = result(); r['promptSource'] = 'typed'
        self.assertFalse(core.human_text(r))

    def test_reused_id_does_not_copy_result_to_earlier_call(self):
        eps = core.episodes(self.read([user(), call(), call(), result()]))
        self.assertEqual([e['status'] for e in eps[0]['events']], ['unknown', 'succeeded'])

    def test_result_before_call_does_not_prove_future_call(self):
        self.assertEqual(self.event([user(), result(), call()])['status'], 'unknown')

    def test_rollback_before_edit_does_not_erase_later_success(self):
        rows = self.read([user(), call('Bash', {'command': 'git reset --hard'}, 'r'),
                          result('Exit code: 0', cid='r'), call(), result()])
        self.assertEqual(app.extract_episodes(rows)[0]['tier'], 'artifact')

    def test_rollback_after_edit_makes_durability_unknown(self):
        rows = self.read([user(), call(), result(), call('Bash', {'command': 'git reset --hard'}, 'r'),
                         result('Exit code: 0', cid='r')])
        self.assertIsNone(app.extract_episodes(rows)[0]['survived'])

    def test_failed_rollback_does_not_erase_success(self):
        rows = self.read([user(), call(), result(), call('Bash', {'command': 'git reset --hard'}, 'r'),
                         result('Exit code: 1', True, cid='r')])
        self.assertTrue(app.extract_episodes(rows)[0]['survived'])

    def test_cursor_missing_results_are_unknown_and_paths_survive(self):
        for name, inp, kind, target in [('StrReplace', {'path': 'login.py'}, 'edit', 'login.py'),
                                      ('Shell', {'command': 'git commit -m fix'}, 'commit', 'git commit -m fix')]:
            records = [{'role': 'user', 'message': {'content': [{'type': 'text', 'text': '<user_query>Fix login.py</user_query>'}]}},
                       {'role': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': name, 'input': inp}]}}]
            e = self.event(records)
            self.assertEqual((e['kind'], e['target'], e['status']), (kind, target, 'unknown'))

    def test_partial_cursor_call_does_not_succeed(self):
        self.assertEqual(self.event([user(), call('Write', '{"path":')])['status'], 'unknown')

    def test_cursor_offset_is_preserved(self):
        self.assertEqual(core._cursor_stamp('<timestamp>Thursday, Aug 13, 2026, 5:53 PM (UTC+2)</timestamp>'),
                         '2026-08-13T17:53:00+02:00')

    def test_codex_patch_with_result(self):
        records = [{'type': 'session_meta', 'payload': {'id': 'demo', 'cwd': '/repo'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': 'Fix login.py'}]}},
            {'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'apply_patch', 'call_id': 'p',
             'input': '*** Begin Patch\n*** Update File: login.py\n-a\n+b\n*** End Patch'}},
            {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output', 'call_id': 'p',
             'output': [{'type': 'text', 'text': 'Success. Updated the following files:\nM login.py'}]}}]
        e = self.event(records)
        self.assertEqual((e['kind'], e['status'], e['target']), ('edit', 'succeeded', 'login.py'))

    def test_codex_single_static_exec(self):
        c = core.normalize_call({'name': 'exec', 'input': 'text(await tools.exec_command({cmd: "pytest tests"}));'})
        self.assertEqual(core.operation(c), 'check')

    def test_codex_multiple_nested_calls_not_falsely_attributed(self):
        c = core.normalize_call({'name': 'exec', 'input': 'await tools.exec_command({cmd: "git commit"}); await tools.exec_command({cmd: "true"});'})
        self.assertEqual(core.operation(c), 'tool')

    def test_stdout_cannot_override_structured_exit_code(self):
        value = {"exit_code": 0, "output": "Exit code: 1\nError: an example from the manual"}
        self.assertEqual(core.result_status(value, call={"name": "Bash"})[0], "succeeded")

    def test_stdout_cannot_override_native_error_flag(self):
        self.assertEqual(core.result_status("Exit code: 1", False, {"name": "Bash"})[0], "succeeded")

    def test_exit_text_in_output_is_not_a_command_receipt(self):
        self.assertEqual(core.result_status("Output:\nExit code: 0", call={"name": "Bash"})[0], "unknown")

    def test_native_exit_header_beats_json_printed_to_stdout(self):
        for outer, inner, status in [(1, 0, 'failed'), (0, 1, 'succeeded')]:
            output = 'Process exited with code %d\nOutput:\n{"exit_code":%d}' % (outer, inner)
            self.assertEqual(core.result_status(output, call={'name':'Bash'})[0], status)

    def test_codex_mention_of_context_name_remains_a_request(self):
        def msg(text):
            return {'type':'response_item', 'payload':{'type':'message','role':'user','content':[{'type':'input_text','text':text}]}}
        rows = self.read([{'type':'session_meta','payload':{'id':'test'}},
                          msg('Fix billing'), msg('Explain the AGENTS.md instructions'),
                          {'type':'response_item','payload':{'type':'function_call','name':'exec_command','call_id':'a','arguments':'{"cmd":"cat AGENTS.md"}'}}])
        eps = core.episodes(rows)
        self.assertEqual(len(eps), 2)
        self.assertEqual(eps[0]['events'], [])
        self.assertEqual(eps[1]['events'][0]['target'], 'cat AGENTS.md')

    def test_codex_context_block_does_not_swallow_separate_real_block(self):
        self.assertEqual(core._codex_human_content([
            {'type':'input_text','text':'<environment_context>injected</environment_context>'},
            {'type':'input_text','text':'Explain this code'}]), 'Explain this code')

    def test_async_result_not_finished(self):
        self.assertEqual(core.result_status('Process running with session ID 123', call={'name': 'Bash'})[0], 'unknown')

    def test_nested_nonzero_exit_beats_success_wrapper(self):
        self.assertEqual(core.result_status('Script completed\n{"exit_code":1,"output":"failed"}', call={'name': 'Bash'})[0], 'failed')

    def test_malformed_records_reported_without_crashing(self):
        p = self.root / 'broken.jsonl'
        p.write_text('[]\nnull\n{bad\n{"message":123}\n' + json.dumps(user()) + '\n')
        warnings = []
        rows, _ = core.read_session(str(p), warnings)
        self.assertEqual(len(rows), 1)
        self.assertIn('4 malformed', warnings[0])
        self.assertEqual(rows[0]['_line'], 5)

    def test_large_file_skipped_before_read(self):
        p = self.root / 'large.jsonl'
        with p.open('wb') as f:
            f.truncate(2 * 1024 * 1024 * 1024)
        warnings = []
        rows, _ = core.read_session(str(p), warnings)
        self.assertEqual(rows, [])
        self.assertIn('128 MiB', warnings[0])

    def test_oversized_line_discarded_not_split_into_records(self):
        p = self.root / 'line.jsonl'
        p.write_text('x' * 160 + '\n' + json.dumps(user('Hi')) + '\n')
        warnings = []
        with patch.object(core, 'MAX_LINE_BYTES', 128):
            rows = list(core.iter_json(str(p), warnings))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['_line'], 2)
        self.assertIn('1 oversized', warnings[0])

    def test_terminal_controls_removed(self):
        self.assertEqual(core.safe_text('hello\x1b]52;c;secret\x07\x1b[2Jworld'), 'helloworld')

    def test_unreadable_file_reports_why(self):
        path = self.root / 'denied.jsonl'
        path.write_text(json.dumps(user()) + '\n')
        path.chmod(0)
        try:
            if os.access(path, os.R_OK):
                self.skipTest('privileged process can read mode-000 files')
            warnings = []
            rows, _ = core.read_session(str(path), warnings)
            self.assertEqual(rows, [])
            self.assertTrue(warnings)
            self.assertIn('denied', warnings[0].lower())
        finally:
            path.chmod(0o600)

    def test_malformed_call_identity_cannot_crash_join(self):
        c = call(); c['message']['content'][0].update(name=None, id={})
        r = result(); r['message']['content'][0]['tool_use_id'] = {}
        self.assertEqual(self.event([user(), c, r])['status'], 'unknown')

    def test_title_requires_same_operation_to_recover(self):
        ep = {'events': [{'kind':'edit','target':'a','status':'failed'}, {'kind':'edit','target':'b','status':'succeeded'}]}
        self.assertEqual(replay.title(ep), 'THE SNAG')
        ep['events'].append({'kind':'edit','target':'a','status':'succeeded'})
        self.assertEqual(replay.title(ep), 'THE COMEBACK')

    def test_failure_after_recovery_cancels_comeback(self):
        ep = {'events':[{'kind':'edit','target':'a','status':s} for s in ['failed','succeeded','failed']]}
        self.assertEqual(replay.title(ep), 'THE SNAG')

    def test_unknown_rollback_after_success_is_unknown(self):
        rows = self.read([user(),call(),result(),call('Bash',{'command':'git reset --hard'},'r')])
        self.assertIsNone(app.extract_episodes(rows)[0]['survived'])

    def test_json_patch_arguments_preserve_all_paths(self):
        patch_text = '*** Begin Patch\n*** Update File: a.py\n-a\n+b\n*** Add File: b.py\n+x\n*** End Patch'
        b = core.normalize_call({'name':'apply_patch','arguments':json.dumps({'patch':patch_text})})
        self.assertEqual(b['input']['paths'], ['a.py','b.py'])

    def test_reading_log_text_is_not_failed_execution(self):
        for text in ['Exit code: 1', 'Error: example', '{"isError":true}', '{"exit_code":1}']:
            self.assertEqual(core.result_status(text, call={'name':'Read'})[0], 'succeeded')

    def test_long_json_result_keeps_tail_exit_status(self):
        value = json.dumps({'output':'x'*20000,'metadata':{'exit_code':7}})
        self.assertEqual(core.result_status(value, call={'name':'Bash'})[0], 'failed')

    def test_unparsed_wrapper_cannot_claim_all_children_succeeded(self):
        records = [{'type':'session_meta','payload':{'id':'demo'}},
                   {'type':'response_item','payload':{'type':'message','role':'user','content':'Do both'}},
                   {'type':'response_item','payload':{'type':'custom_tool_call','name':'exec','call_id':'x','input':'await tools.one(); await tools.two();'}},
                   {'type':'response_item','payload':{'type':'custom_tool_call_output','call_id':'x','output':'Script completed'}}]
        self.assertEqual(self.event(records)['status'], 'unknown')

    def test_real_shaped_edit_success_without_error_flag(self):
        e = self.event([user(),call(),result('The file /repo/login.py has been updated successfully.',None)])
        self.assertEqual(e['status'], 'succeeded')

    def test_long_multiblock_paste_uses_one_identity(self):
        u = user(); u['message']['content'] = [{'type':'text','text':'word '*4000},{'type':'text','text':'more '*4000}]
        rows = self.read([u])
        key = core.human_text(rows[0])
        self.assertEqual(app._human_prompt(rows[0]), key)
        self.assertEqual(app.count_corrections(rows, {key}), (0,0))

    def test_success_then_failure_is_not_comeback(self):
        ep = {'events': [{'kind':'edit','target':'a','status':'succeeded'}, {'kind':'edit','target':'a','status':'failed'}]}
        self.assertEqual(replay.title(ep), 'THE SNAG')


class StatisticsTests(unittest.TestCase):
    def test_wilson_against_published_formula_example(self):
        lo, hi = app._wilson(4, 20, 1.6448536269514722)
        self.assertAlmostEqual(lo, .093118, places=5)
        self.assertAlmostEqual(hi, .378377, places=5)

    def test_large_apparent_gap_is_not_inferential_advice(self):
        eps = [{'opener': 'Verify login.py', 'survived': True, 'has_mutation': True, 'tier': 'artifact'} for _ in range(80)]
        eps += [{'opener': 'Change billing.py', 'survived': False, 'has_mutation': True, 'tier': 'none'} for _ in range(80)]
        bands = app.rank_patterns(eps)
        self.assertTrue(bands)
        self.assertFalse(any(b['distinguishable'] for b in bands))

    def test_unknown_and_read_only_excluded_from_denominator(self):
        eps = [{'opener': 'Fix login.py', 'survived': True, 'has_mutation': True, 'tier': 'artifact'},
               {'opener': 'Fix login.py', 'survived': None, 'has_mutation': True, 'tier': 'unknown'},
               {'opener': 'Fix login.py', 'survived': False, 'has_mutation': False, 'tier': 'none'}]
        self.assertTrue(all(b['n'] == 1 and b['survived'] == 1 for b in app.rank_patterns(eps)))


class CLITests(FixtureCase):
    # Integration tests run in an isolated HOME; no user's transcripts or index.
    def run_cli(self, *args):
        env = dict(os.environ, HOME=str(self.root), PYTHONIOENCODING='utf-8')
        return subprocess.run([sys.executable, str(ROOT/'transcripto.py'), *args], env=env,
                              cwd=self.root, capture_output=True, text=True, timeout=20)

    def test_source_filename_cannot_emit_terminal_controls(self):
        name = 'unsafe\x1b[2J.jsonl'
        self.read([user()], name)
        p = self.run_cli('replay', str(self.root/name))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn('\x1b', p.stdout)

    def test_session_view_keeps_harness_cwd_separate(self):
        import sqlite3
        u = dict(user(), sessionId='shared', cwd='/claude-project', timestamp='2026-01-01')
        self.read([u], 'claude.jsonl')
        self.read([{'type':'session_meta','payload':{'id':'shared','cwd':'/codex-project'}},
            {'type':'response_item','timestamp':'2026-02-01','payload':{'type':'message','role':'user','content':'Codex request'}}], 'codex.jsonl')
        p = self.run_cli('index','--root',str(self.root))
        self.assertEqual(p.returncode, 0, p.stderr)
        with sqlite3.connect(self.root/'.trace'/'trace.db') as db:
            rows = dict(db.execute('SELECT harness,cwd FROM v_sessions'))
        self.assertEqual(rows, {'claude':'/claude-project','codex':'/codex-project'})

    def test_demo_runs_real_parser(self):
        p = self.run_cli('replay', '--demo', '--json')
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertTrue(r['synthetic'])
        self.assertEqual([e['status'] for e in r['episodes'][0]['events']], ['failed','succeeded','failed','succeeded','succeeded'])

    def test_share_carries_caveat_and_no_prompt(self):
        p = self.run_cli('replay','--demo','--share')
        self.assertNotIn('login', p.stdout)
        self.assertIn('not task correctness', p.stdout)
        self.assertIn('Synthetic demo', p.stdout)

    def test_empty_default_is_actionable(self):
        p = self.run_cli()
        self.assertEqual(p.returncode, 2)
        self.assertIn('--demo', p.stdout)

    def test_latest_skips_machine_only_session(self):
        self.read([user(),call(),result()], 'human.jsonl')
        self.read([call()], 'machine.jsonl')
        p = self.run_cli('replay','--root',str(self.root),'--json')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('human.jsonl', json.loads(p.stdout)['episodes'][0]['source'])

    def test_search_automatically_indexes_all_three(self):
        self.read([user('claude-needle')], 'claude.jsonl')
        self.read([{'role':'user','message':{'content':[{'type':'text','text':'<user_query>cursor-needle</user_query>'}]}}], 'cursor.jsonl')
        self.read([{'type':'session_meta','payload':{'id':'codex-demo'}}, {'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'codex-needle'}]}}], 'codex.jsonl')
        for needle in ['claude-needle','cursor-needle','codex-needle']:
            p = self.run_cli('ask', needle, '--root', str(self.root))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn('1 recorded request', p.stdout)
        self.assertEqual((self.root/'.trace'/'trace.db').stat().st_mode & 0o777, 0o600)

    def test_reindex_removes_old_full_text_tokens(self):
        self.read([user('oldneedle')])
        self.assertIn('1 recorded request', self.run_cli('ask','oldneedle','--root',str(self.root)).stdout)
        self.read([user('newneedle')])
        os.utime(self.root/'session.jsonl', (2000000000, 2000000000))
        self.assertIn('nothing about', self.run_cli('ask','oldneedle','--root',str(self.root)).stdout)
        self.assertIn('1 recorded request', self.run_cli('ask','newneedle','--root',str(self.root)).stdout)

    def test_failed_edit_not_reported_as_wrote_by_find(self):
        self.read([user(),call(),result('denied',True)])
        p = self.run_cli('find','login.py','--root',str(self.root))
        self.assertNotIn('WROTE', p.stdout)
        self.assertIn('ATTEMPT:EDIT', p.stdout)

    def test_root_scope_excludes_other_indexed_corpus(self):
        left, right = self.root/'left', self.root/'right'
        left.mkdir(); right.mkdir()
        (left/'a.jsonl').write_text(json.dumps(user('sharedneedle left')) + '\n')
        (right/'b.jsonl').write_text(json.dumps(user('sharedneedle right')) + '\n')
        self.run_cli('ask','sharedneedle','--root',str(left))
        p = self.run_cli('ask','sharedneedle','--root',str(right))
        self.assertIn('sharedneedle right', p.stdout)
        self.assertNotIn('sharedneedle left', p.stdout)
        self.assertIn('1 recorded request', p.stdout)

    def test_deleted_transcript_is_removed_on_refresh(self):
        self.read([user('deletedneedle')])
        self.assertIn('1 recorded request', self.run_cli('ask','deletedneedle','--root',str(self.root)).stdout)
        (self.root/'session.jsonl').unlink()
        self.assertIn('nothing about', self.run_cli('ask','deletedneedle','--root',str(self.root)).stdout)

    def test_harness_filters_mixed_root_for_search_and_replay(self):
        self.read([user('sharedneedle Claude')], 'claude.jsonl')
        self.read([{'type':'session_meta','payload':{'id':'codex-demo'}},
                   {'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'sharedneedle Codex'}]}}], 'codex.jsonl')
        self.run_cli('ask','sharedneedle','--root',str(self.root))
        p = self.run_cli('ask','sharedneedle','--root',str(self.root),'--harness','codex')
        self.assertIn('sharedneedle Codex', p.stdout)
        self.assertNotIn('sharedneedle Claude', p.stdout)
        p = self.run_cli('replay','--root',str(self.root),'--harness','claude','--json')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['episodes'][0]['harness'], 'claude')

    def test_missing_explicit_episode_does_not_pick_an_older_session(self):
        self.read([user('first'),user('second')], 'older.jsonl')
        self.read([user('newest')], 'newer.jsonl')
        os.utime(self.root/'newer.jsonl', (2000000000, 2000000000))
        p = self.run_cli('replay','latest','--root',str(self.root),'--episode','2','--json')
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['episodes'], [])

    def test_query_word_is_not_silently_a_filename_match(self):
        self.read([user('unrelated prompt')], 'dead-2026.jsonl')
        p = self.run_cli('replay','dead','--root',str(self.root),'--json')
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['episodes'], [])
        p = self.run_cli('replay','--session','dead-2026','--root',str(self.root),'--json')
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_partial_file_is_searchable_and_warning_persists(self):
        p = self.root/'partial.jsonl'
        p.write_text(json.dumps(user('partialneedle'))+'\n{bad\n')
        for _ in range(2):
            r = self.run_cli('ask','partialneedle','--root',str(self.root))
            self.assertIn('1 recorded request', r.stdout)
            self.assertIn('malformed', r.stderr)

    def test_trace_propagates_no_match_status(self):
        p = self.run_cli('trace','missing','--root',str(self.root))
        self.assertEqual(p.returncode, 2)

    def test_correction_does_not_project_authors_rate(self):
        self.read([user('No, wrong')])
        p = self.run_cli('coach','--root',str(self.root))
        self.assertIn('1 of 1', p.stdout)
        self.assertNotIn('26-37', p.stdout)
        self.assertNotIn('real rate', p.stdout)


class PrivacyTests(unittest.TestCase):
    def test_runtime_imports_and_dynamic_execution(self):
        import ast
        banned = {'socket', 'urllib', 'requests', 'http', 'subprocess', 'ctypes'}
        for filename in ['transcripto.py', 'transcripto_core.py', 'transcripto_replay.py']:
            tree = ast.parse((ROOT/filename).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(a.name.split('.')[0] in banned for a in node.names), filename)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0], banned, filename)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, ('eval', 'exec', '__import__'), filename)


if __name__ == '__main__':
    unittest.main()
