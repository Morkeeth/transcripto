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
import transcripto_findings as findings
import transcripto_jev as jev

class FindingsFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'synthetic session.jsonl'
        self.report = self.root / 'findings.json'
        self.packet = self.root / 'packet.json'
        self.brief = self.root / 'brief.md'
        self.rows = [
            {'type':'user','promptSource':'typed','message':{'content':'Build the square button.'}},
            {'type':'assistant','message':{'content':[{'type':'text','text':'The button is round.'}]}},
            {'type':'user','promptSource':'typed','message':{'content':'Use the square variant.'}},
            {'type':'assistant','message':{'content':[{'type':'tool_use','id':'edit','name':'Edit','input':{'file_path':'button.py'}}]}},
            {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'edit','content':'replacement failed','is_error':True}]}},
            {'type':'user','promptSource':'typed','message':{'content':'Email private@example.com'}},
        ]
        for row in self.rows: row['transcripto_synthetic']=True
        self.source.write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        self.calls=[]
        def urlopen(req, timeout=None):
            body=json.loads(req.data); self.calls.append(body)
            # One observation per request: first noncandidate, second candidate.
            p=.1 if len(self.calls)==1 else .9
            response={'answers':{'q0':{'probabilities':{'correction':p}}},'usage':{'cost':0},'model':'TEST FIXTURE fake transport'}
            # Keys are frozen by actual build_body; use them, not an assumed key.
            response['answers']={k:{'probabilities':{'correction':p}} for k in body['questions']}
            return io.BytesIO(json.dumps(response).encode())
        self.detector=jev.JevDetector('fixture-key',urlopen=urlopen,notice=lambda x:None,workers=1,home='/nonexistent-fixture-home')
        self.detector.fixture=True

    def cli(self,*args,detector=None):
        out,err=io.StringIO(),io.StringIO()
        with patch.object(sys,'argv',['transcripto',*map(str,args)]), contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            with patch.object(app,'_jev_detector',return_value=detector) if detector is not None else contextlib.nullcontext():
                try: app.main();code=0
                except SystemExit as e: code=e.code or 0
        return code,out.getvalue(),err.getvalue()

    def save(self):
        report=findings.observe(str(self.source),self.detector,fixture=True)
        app._write_private(str(self.report),json.dumps(report))
        return report

    def test_fake_only_findings_replay_handoff_receiver_loop(self):
        report=self.save()
        self.assertEqual([f['status'] for f in report['findings']],['not_candidate','candidate','excluded'])
        self.assertFalse(app.is_correction('Use the square variant.'))
        self.assertEqual(len(self.calls),2)
        self.assertNotIn('Build the square',json.dumps(report))
        self.assertNotIn('private@example',json.dumps(report))
        self.assertEqual(self.report.stat().st_mode & 0o777,0o600)
        code,out,_=self.cli('replay','--findings',self.report,'--line',3,'--json')
        self.assertEqual(code,0,out)
        replay=json.loads(out);self.assertEqual(replay['episodes'][0]['prompt'],'Use the square variant.')
        self.assertEqual(replay['episodes'][0]['events'][0]['status'],'failed')
        self.assertTrue(replay['detector_observation']['fixture'])
        code,out,err=self.cli('handoff','--findings',self.report,'--line',3,'--to-harness','codex','--output',self.packet)
        self.assertEqual(code,0,err)
        code,out,err=self.cli('receive-handoff',self.packet,'--as-harness','codex','--output',self.brief)
        self.assertEqual(code,0,err)
        brief=self.brief.read_text();self.assertIn('TEST FIXTURE',brief);self.assertIn('not a human label',brief);self.assertIn('failed',brief)
        self.assertIn('acknowledgement pending',brief)
        self.assertEqual(len(self.calls),2)
        self.assertEqual(self.brief.stat().st_mode & 0o777,0o600)

    def test_source_change_refuses_replay_and_handoff_even_if_selected_prompt_unchanged(self):
        self.save()
        self.cli('handoff','--findings',self.report,'--line',3,'--to-harness','codex','--output',self.packet)
        self.source.write_text(self.source.read_text()+'\n')
        for command in [('replay','--findings',self.report,'--line',3),('handoff','--findings',self.report,'--line',3,'--to-harness','codex','--output',self.root/'refused.json')]:
            code,_,_=self.cli(*command);self.assertEqual(code,2)
        self.assertFalse((self.root/'refused.json').exists())
        code,_,_=self.cli('receive-handoff',self.packet,'--as-harness','codex','--output',self.brief)
        self.assertEqual(code,0);self.assertIn('provisional',self.brief.read_text());self.assertIn('human confirmation',self.brief.read_text())

    def test_terminal_unknown_and_export_detector_origin(self):
        self.save()
        code,out,err=self.cli('replay','--findings',self.report,'--line',6)
        self.assertEqual(code,0,err)
        self.assertIn('excluded; P(correction)=no verdict',out)
        result=app.export_run(str(self.source),self.detector)
        self.assertNotIn('correction_rate is a lexical estimate',result['proxy'])
        self.assertIn('Jev model estimate',result['proxy'])

    def test_non_candidate_and_malformed_probability_refuse(self):
        report=self.save()
        for line in (1,6):
            with self.assertRaises(ValueError):findings.selected(str(self.report),line,candidate=True)
        report['findings'][1]['probability']=float('nan');self.report.write_text(json.dumps(report))
        with self.assertRaises(ValueError):findings.selected(str(self.report),3,candidate=True)

    def test_full_cli_counts_only_preview_and_opt_in(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            code,out,err=self.cli('jev-findings',self.source,'--detector','jev','--jev-dry-run','--output',self.report)
        self.assertEqual(code,0,err)
        report=json.loads(out);self.assertEqual(report['schema'],'transcripto.jev-privacy-preview/1')
        self.assertEqual(report['jev']['sent'],0);self.assertNotIn('source',report);self.assertNotIn('square',out)
        code,_,_=self.cli('jev-findings',self.source);self.assertEqual(code,2)
        code,out,err=self.cli('jev-findings',self.source,'--detector','jev','--output',self.report,detector=self.detector)
        self.assertEqual(code,0,err);self.assertEqual(json.loads(out)['schema'],findings.SCHEMA)
        self.assertNotIn('Use the square',out)

if __name__=='__main__':unittest.main()
