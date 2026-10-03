"""Installed console-script journey with labelled fake transport and synthetic data.
No network, credentials, user transcripts, or receiver invocation.
Usage: python check_packaged_jev_findings.py /absolute/bin/transcripto
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    executable = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / 'synthetic.jsonl'
        report, packet, brief = (root / name for name in ('findings.json', 'packet.json', 'brief.md'))
        rows = [
            {'type':'user','promptSource':'typed','message':{'content':'Build the square button.'}},
            {'type':'assistant','message':{'content':[{'type':'text','text':'The button is round.'}]}},
            {'type':'user','promptSource':'typed','message':{'content':'Use the square variant.'}},
            {'type':'assistant','message':{'content':[{'type':'tool_use','id':'edit','name':'Edit','input':{'file_path':'button.py'}}]}},
            {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'edit','content':'replacement failed','is_error':True}]}},
        ]
        for row in rows: row['transcripto_synthetic'] = True
        source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        guard=root/'guard';guard.mkdir()
        (guard/'sitecustomize.py').write_text('''import socket, urllib.request, json, io
import transcripto_jev
transcripto_jev.JevDetector.fixture = True
def refuse(*args, **kwargs): raise AssertionError("Network forbidden")
socket.socket = socket.create_connection = refuse
def fake(request, **kwargs):
    body=json.loads(request.data)
    return io.BytesIO(json.dumps({"model":"TEST FIXTURE fake transport", "usage":{"cost":0},
        "answers":{k:{"probabilities":{"correction":.9}} for k in body["questions"]}}).encode())
urllib.request.urlopen=fake
''')
        env=dict(os.environ,HOME=tmp,PYTHONPATH=str(guard),OPENROUTER_API_KEY='fixture-not-a-real-key')
        def run(*args,ok=True):
            r=subprocess.run([executable,*map(str,args)],cwd=tmp,env=env,text=True,capture_output=True)
            assert (r.returncode == 0)==ok,(r.returncode,r.stdout,r.stderr)
            return r
        run('jev-findings',source,'--detector','jev','--output',report)
        saved=json.loads(report.read_text())
        assert saved['fixture'] and saved['synthetic']
        assert 'Use the square' not in report.read_text()
        replay=json.loads(run('replay','--findings',report,'--line',3,'--json').stdout)
        assert replay['episodes'][0]['events'][0]['status']=='failed'
        assert replay['detector_observation']['fixture']
        share=run('replay','--findings',report,'--line',3,'--share').stdout
        assert 'square' not in share and str(source) not in share
        run('handoff','--findings',report,'--line',3,'--to-harness','codex','--output',packet)
        run('receive-handoff',packet,'--as-harness','codex','--output',brief)
        assert 'TEST FIXTURE' in brief.read_text() and 'acknowledgement pending' in brief.read_text()
        assert 'failed' in brief.read_text() and 'not a human label' in brief.read_text()
        for p in (report,packet,brief): assert p.stat().st_mode & 0o777 == 0o600
        source.write_text(source.read_text()+'\n')
        run('replay','--findings',report,'--line',3,ok=False)
        run('handoff','--findings',report,'--line',3,'--to-harness','codex','--output',root/'refused.json',ok=False)
        assert not (root/'refused.json').exists()
        run('receive-handoff',packet,'--as-harness','codex','--output',brief)
        assert 'provisional' in brief.read_text()
        print('PASS installed selected session -> labelled fake findings -> source-bound failed replay -> explicit handoff -> receiver brief; source change refuses; 0 real model calls')

if __name__=='__main__':main()
