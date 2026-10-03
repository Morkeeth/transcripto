import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import transcripto as app
import transcripto_selected as selected

class SelectedContext(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.cwd=self.root/'repo';self.cwd.mkdir();self.source=self.root/'run.jsonl'
        rows=[{'type':'session_meta','payload':{'id':'fixture'}},{'type':'response_item','payload':{'type':'message','role':'user','content':'PRIVATE_TITLE Fix button'}},{'type':'response_item','payload':{'type':'function_call','name':'exec_command','call_id':'x','arguments':'{"cmd":"fix button"}'}},{'type':'response_item','payload':{'type':'function_call_output','call_id':'x','output':'Process exited with code 1\nfailed'}}]
        for r in rows:r['transcripto_synthetic']=True
        self.source.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.sha=selected.describe(self.source)['sha256']
        self.db=self.root/'index #?%.db';con=sqlite3.connect(self.db);con.execute('CREATE TABLE messages(session_file TEXT,session_id TEXT,harness TEXT,cwd TEXT,ts TEXT,text TEXT)')
        for i in range(2):con.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(str(self.source),'id'+str(i),'codex',str(self.cwd),'2026-10-03','PRIVATE_BODY_SENTINEL'))
        con.commit();con.close()
    def cli(self,*args):
        out,err=io.StringIO(),io.StringIO()
        with patch.object(sys,'argv',['transcripto',*map(str,args)]),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch('socket.socket',side_effect=AssertionError('network forbidden')):
            try:app.main();code=0
            except SystemExit as e:code=e.code or 0
        return code,out.getvalue(),err.getvalue()
    def test_metadata_does_not_refresh_or_read_bodies_and_exact_special_path(self):
        before=self.db.read_bytes()
        with patch.object(app,'connect',side_effect=AssertionError('writer forbidden')):
            code,text,err=self.cli('selected-context','runs','--index',self.db,'--cwd',self.cwd)
        self.assertEqual(code,0,err);data=json.loads(text);self.assertEqual(len(data['runs']),2);self.assertNotIn('PRIVATE_',text);self.assertEqual(before,self.db.read_bytes())
        self.assertEqual(self.cli('selected-context','episodes','--source',self.source,'--accept-sha',self.sha)[0],2)
    def test_authored_packet_without_model_report_reuses_source_outcomes(self):
        code,text,err=self.cli('selected-context','episodes','--source',self.source,'--accept-sha',self.sha,'--consent')
        self.assertEqual(code,0,err);self.assertEqual(json.loads(text)['episodes'][0]['events'][0]['status'],'failed')
        packet=self.root/'packet.json';brief=self.root/'brief.md'
        code,_,err=self.cli('handoff','--source',self.source,'--accept-sha',self.sha,'--line',2,'--instruction','Make the button square.','--consent','--to-harness','claude','--output',packet)
        self.assertEqual(code,0,err);p=json.loads(packet.read_text());self.assertNotIn('detector_observation',p)
        code,_,err=self.cli('receive-handoff',packet,'--as-harness','claude','--output',brief);self.assertEqual(code,0,err)
        self.assertIn('source available',brief.read_text());self.assertIn('failed',brief.read_text());self.assertIn('not a detector verdict',brief.read_text())
        self.assertEqual(self.cli('handoff','--source',self.source,'--accept-sha',self.sha,'--line',2,'--instruction','Fix it','--consent','--to-harness','codex','--output',self.root/'same.json')[0],2)
        self.source.write_text(self.source.read_text()+'\n')
        self.assertEqual(self.cli('handoff','--source',self.source,'--accept-sha',self.sha,'--line',2,'--instruction','Fix it','--consent','--to-harness','claude','--output',self.root/'drift.json')[0],2)
        self.assertFalse((self.root/'drift.json').exists())

    def test_authored_new_session_is_distinct_and_identity_is_byte_derived(self):
        row={'type':'user','promptSource':'typed','sessionId':'AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE','transcripto_synthetic':True,'message':{'role':'user','content':'Repair the label.'}}
        self.source.write_text(json.dumps(row)+'\n');sha=selected.describe(self.source)['sha256']
        args=['selected-context','authored-continuation','--source',self.source,'--accept-sha',sha,'--line',1,'--instruction','Add the label.']
        self.assertEqual(self.cli(*args)[0],2)
        code,text,err=self.cli(*args,'--consent');self.assertEqual(code,0,err)
        self.assertEqual(json.loads(text)['source_session']['session_id'],'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
        self.assertEqual(self.cli('handoff','--source',self.source,'--accept-sha',sha,'--line',1,'--instruction','Add label','--consent','--to-harness','claude','--output',self.root/'same.json')[0],2)
        for extra in [{'type':'assistant','message':{'role':'assistant','content':'missing id'}},dict(row,sessionId='11111111-2222-4333-8444-555555555555'),{'type':'session_meta','payload':{'id':'foreign'}}]:
            self.source.write_text(json.dumps(row)+'\n'+json.dumps(extra)+'\n');current=selected.describe(self.source)['sha256']
            self.assertRaises(ValueError,selected.source_session,self.source,current)

if __name__=='__main__':unittest.main()
