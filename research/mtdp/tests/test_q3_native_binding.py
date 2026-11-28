import copy
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from research.mtdp.jass_benchmark import q3_native_binding as m


class NativeBindingTests(unittest.TestCase):
    def setUp(self):
        self.plan=m.load_plan(Path(__file__).resolve().parents[3])
        legal=','.join(sorted(m.LEGAL))
        self.raw='\t'.join([self.plan['fen'],'10000','10000','8','nodes','31-26','3','0','31-26',legal,legal,'1:1:1:1:10:'+legal])+'\n'

    def test_parse_retains_internal_time_but_semantics_exclude_it(self):
        a=m.parse_native(self.raw,self.plan['fen'],10000)
        b=m.parse_native(self.raw.replace('\t3\t0\t','\t3\t1\t'),self.plan['fen'],10000)
        self.assertEqual(a['internal_search_us'],0)
        self.assertEqual(m.semantic(a),m.semantic(b))

    def test_invalid_budget_identity_elapsed_and_legal_trace_rejected(self):
        for index,value in [(0,'B:W31:B20'),(2,'9999'),(4,'depth_ceiling'),(7,'-1'),(9,'31-26'),(10,'31-26'),(11,'1:1:0:0:1:31-26')]:
            fields=self.raw.strip().split('\t');fields[index]=value
            with self.assertRaises(ValueError):m.parse_native('\t'.join(fields),self.plan['fen'],10000)
        with self.assertRaises(ValueError):m.parse_native(self.raw+self.raw,self.plan['fen'],10000)

    def test_setup_scrubs_search_control_environment(self):
        with patch.dict(m.os.environ,{'MTDP_DEPTH_ONE_WINNER':'bad','JASS_EGDB_PATH':'bad','JASS_TRACE_ROOT':'1'}):
            args,payload,env=m.config(Path('/tmp/native'),self.plan['fen'],10000)
        self.assertNotIn('MTDP_DEPTH_ONE_WINNER',env)
        self.assertNotIn('JASS_EGDB_PATH',env)
        self.assertEqual(env['JASS_TRACE_ROOT'],'0')
        self.assertEqual(args,['/tmp/native'])
        self.assertTrue(payload.endswith(' 10000\n'))

    def test_plain_and_instrumented_charge_same_measured_nodes(self):
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,self.raw,'')) as run:
            a=m.trial(Path('/tmp/native'),self.plan,0,'plain')
            b=m.trial(Path('/tmp/native'),self.plan,1,'instrumented')
        self.assertEqual(a['semantic_search'],b['semantic_search'])
        self.assertEqual(b['cost_audit']['measured_nodes'],10000)
        self.assertGreaterEqual(b['observer_outside_recorder_ns'],0)
        self.assertTrue(a['timing_bounds_pass'] and b['timing_bounds_pass'])
        self.assertEqual(run.call_args.kwargs['timeout'],15)

    def test_timeout_retains_partial_bytes_and_unknown_nodes(self):
        error=subprocess.TimeoutExpired(['native'],15,output=b'partial',stderr=b'failure')
        with patch.object(m.subprocess,'run',side_effect=error):
            r=m.trial(Path('/tmp/native'),self.plan,0,'instrumented')
        self.assertEqual(r['status'],'timeout')
        self.assertEqual(r['raw']['stdout'],'partial')
        self.assertIsNone(r['measured_nodes'])
        self.assertIsNone(r['cost_audit'])
        self.assertFalse(r['timing_bounds_pass'])
        self.assertGreaterEqual(r['total_elapsed_ns'],0)

    def test_failed_and_malformed_output_are_not_success(self):
        for process in [subprocess.CompletedProcess([],2,'','bad'),subprocess.CompletedProcess([],0,'corrupt','')]:
            with patch.object(m.subprocess,'run',return_value=process):r=m.trial(Path('/tmp/native'),self.plan,0,'instrumented')
            self.assertEqual(r['status'],'error')
            self.assertIsNone(r['measured_nodes'])
            self.assertIsNone(r['cost_audit'])
            self.assertIsNotNone(r['raw']['returncode'])

    def test_internal_engine_time_cannot_exceed_enclosing_clock(self):
        fields=self.raw.strip().split('\t');fields[7]='99999999999'
        with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'\t'.join(fields),'')):
            r=m.trial(Path('/tmp/native'),self.plan,0,'instrumented')
        self.assertFalse(r['timing_bounds_pass'])

    def rows(self):
        result=m.parse_native(self.raw,self.plan['fen'],10000)
        return [dict(index=i,arm=arm,status='completed',timing_bounds_pass=True,semantic_search=m.semantic(result),
                     total_elapsed_ns=100 if arm=='plain' else 110,measured_nodes=10000)
                for i,arm in enumerate(arm for pair in self.plan['orders'] for arm in pair)]

    def test_paired_all_trial_summary_and_no_gain_claim(self):
        r=m.summarize(self.rows(),self.plan)
        self.assertTrue(r['binding_passed']);self.assertEqual(r['total_measured_nodes'],100000)
        self.assertEqual(r['median_observer_delta_ns'],10)
        self.assertEqual(r['median_observer_ratio'],1.1)
        self.assertFalse(r['causal_overhead_established'])
        self.assertFalse(r['independent_quality_or_speed_gain_established'])

    def test_failed_trial_not_removed_or_unknown_nodes_replaced(self):
        rows=self.rows();rows[3].update(status='timeout',timing_bounds_pass=False,measured_nodes=None,semantic_search=None)
        r=m.summarize(rows,self.plan)
        self.assertEqual((r['total_trials'],r['failed_trials'],r['unknown_node_trials']),(10,1,1))
        self.assertFalse(r['binding_passed']);self.assertIsNone(r['median_observer_ratio'])

    def test_reordered_or_missing_trials_fail_closed(self):
        rows=self.rows()
        for sample in [rows[:-1],list(reversed(rows))]:
            with self.assertRaises(ValueError):m.summarize(sample,self.plan)

    def test_semantic_change_refuses_pass_even_with_same_node_counts(self):
        rows=self.rows();rows[1]['semantic_search']=dict(rows[1]['semantic_search'],best_move='35-30')
        self.assertFalse(m.summarize(rows,self.plan)['binding_passed'])


if __name__=='__main__':unittest.main()
