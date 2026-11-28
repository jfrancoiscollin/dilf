import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from research.mtdp.jass_benchmark import q3_native_binding as n
from research.mtdp.jass_benchmark.q3_native_binding_evidence import verify


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.plan=n.load_plan(Path(__file__).resolve().parents[3]);legal=','.join(sorted(n.LEGAL))
        raw='\t'.join([self.plan['fen'],'10000','10000','8','nodes','31-26','3','0','31-26',legal,legal,'1:1:1:1:10:'+legal])+'\n'
        with patch.object(n.subprocess,'run',return_value=subprocess.CompletedProcess([],0,raw,'')):
            self.rows=[n.trial(Path('/tmp/native'),self.plan,i,a) for i,a in enumerate(a for pair in self.plan['orders'] for a in pair)]
        self.summary=n.summarize(self.rows,self.plan)

    def materialize(self,path):
        (path/'trials.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        (path/'summary.json').write_text(json.dumps(self.summary))
        (path/'provenance.json').write_text('{}')

    def test_all_raw_clocks_nodes_and_summary_reproduced(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.materialize(p);r=verify(p,self.plan)
        self.assertTrue(r['binding_passed']);self.assertEqual(r['total_measured_nodes'],100000)
        self.assertFalse(r['execution_authenticity_proven'])

    def test_corrupt_raw_receipt_or_summary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.rows[0]['raw']['stdout']='bad';self.materialize(p)
            with self.assertRaises(ValueError):verify(p,self.plan)
        self.setUp();self.summary['binding_passed']=False
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.materialize(p)
            with self.assertRaises(ValueError):verify(p,self.plan)

    def test_cost_and_outer_time_cannot_be_silently_discounted(self):
        for field in ['cost_audit','total_elapsed_ns']:
            self.setUp()
            if field=='cost_audit':self.rows[1][field]['measured_nodes']=9999
            else:self.rows[1][field]-=1
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);self.materialize(p)
                with self.assertRaises(ValueError):verify(p,self.plan)


if __name__=='__main__':unittest.main()
