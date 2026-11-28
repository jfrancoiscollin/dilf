import copy
import unittest
from research.mtdp.jass_benchmark.q3_cost_receipt import CostRecorder, audit


class CostTests(unittest.TestCase):
    def example(self):
        return dict(schema='mtdp-q3-cold-total-cost-v1', trial_id='t', position_id='p',
            arm='candidate', cache_mode='cold', node_budget=100,
            start_ns=10, end_ns=110, status='completed', stages=[
                dict(phase='signature', start_ns=20, end_ns=40, nodes=0, issued_nodes=None),
                dict(phase='verification', start_ns=50, end_ns=60, nodes=10, issued_nodes=10),
                dict(phase='fallback', start_ns=60, end_ns=100, nodes=90, issued_nodes=90)])

    def test_envelope_charges_gaps_and_all_fallback_nodes(self):
        r=audit(self.example())
        self.assertEqual((r['total_elapsed_ns'],r['orchestration_elapsed_ns'],r['measured_nodes']),(100,30,100))
        self.assertTrue(r['equal_node_comparable'])
        self.assertFalse(r['runtime_gain_established'])

    def test_calls_cannot_be_double_counted_or_leave_envelope(self):
        for start,end in [(39,60),(55,50),(50,111)]:
            r=self.example();r['stages'][1].update(start_ns=start,end_ns=end)
            with self.assertRaises(ValueError):audit(r)

    def test_unknown_or_missing_node_measurement_is_not_zero(self):
        for value in [None,True,-1,1.5]:
            r=self.example();r['stages'][0]['nodes']=value
            with self.assertRaises(ValueError):audit(r)

    def test_nodes_require_positive_issued_cap(self):
        for issued in [None,0,True,-1]:
            r=self.example();r['stages'][1]['issued_nodes']=issued
            with self.assertRaises(ValueError):audit(r)

    def test_overruns_are_retained_and_noncomparable(self):
        r=self.example();r['stages'][2]['nodes']=91
        a=audit(r)
        self.assertEqual(a['measured_nodes'],101)
        self.assertEqual(a['issued_cap_overruns'],1)
        self.assertFalse(a['within_node_budget'])
        self.assertFalse(a['equal_node_comparable'])

    def test_aborts_and_ceilings_remain_in_denominator(self):
        for status in ['depth_ceiling','timeout','error']:
            r=self.example();r['status']=status
            a=audit(r);self.assertEqual(a['measured_nodes'],100)
            self.assertFalse(a['equal_node_comparable'])

    def test_incomplete_budget_is_not_equal_node_comparison(self):
        r=self.example();r['stages'][2]['nodes']=80
        self.assertTrue(audit(r)['within_node_budget'])
        self.assertFalse(audit(r)['equal_node_comparable'])

    def test_warm_setup_and_unrecognized_fields_fail_closed(self):
        r=self.example();r['cache_mode']='warm'
        with self.assertRaises(ValueError):audit(r)
        r=self.example();r['estimated_time']=0
        with self.assertRaises(ValueError):audit(r)
        r=self.example();r['stages'][0]['phase']='unmetered'
        with self.assertRaises(ValueError):audit(r)

    def test_clock_reversal_and_invalid_identity_rejected(self):
        for field,value in [('end_ns',9),('start_ns',True),('position_id',''),('status','ok'),('node_budget',0)]:
            r=self.example();r[field]=value
            with self.assertRaises(ValueError):audit(r)

    def test_real_recorder_synthetic_work_only(self):
        recorder=CostRecorder(trial_id='synthetic',position_id='synthetic',arm='native',node_budget=1)
        with recorder.stage('search') as row:row.update(nodes=1,issued_nodes=1)
        raw,result=recorder.finish('completed')
        self.assertGreaterEqual(result['total_elapsed_ns'],0)
        self.assertTrue(result['equal_node_comparable'])
        with self.assertRaises(ValueError):recorder.finish('completed')
        with self.assertRaises(ValueError):
            with recorder.stage('lookup'):pass

    def test_nested_stage_and_finish_while_active_rejected(self):
        r=CostRecorder(trial_id='t',position_id='p',arm='native',node_budget=1)
        with r.stage('search') as row:
            row.update(nodes=1,issued_nodes=1)
            with self.assertRaises(ValueError):
                with r.stage('lookup'):pass
            with self.assertRaises(ValueError):r.finish('completed')
        self.assertTrue(r.finish('completed')[1]['equal_node_comparable'])

    def test_exception_retains_measured_failed_call_and_elapsed_time(self):
        times=iter([10,20,60,100])
        r=CostRecorder(trial_id='t',position_id='p',arm='native',node_budget=20,clock=lambda:next(times))
        with self.assertRaises(RuntimeError):
            with r.stage('search') as row:
                row.update(nodes=7,issued_nodes=20)
                raise RuntimeError('simulated engine failure')
        raw,a=r.finish('error')
        self.assertEqual((a['total_elapsed_ns'],a['measured_nodes']),(90,7))
        self.assertFalse(a['equal_node_comparable'])

    def test_unknown_failed_nodes_refuse_complete_receipt(self):
        r=CostRecorder(trial_id='t',position_id='p',arm='native',node_budget=1)
        with r.stage('search'):pass
        with self.assertRaises(ValueError):r.finish('error')


if __name__=='__main__':unittest.main()
