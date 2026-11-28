import copy
import unittest
from research.mtdp.jass_benchmark.q3_warm_batch import audit, WarmBatchRecorder


def fixture():
    def stage(phase,a,b,n,issued=None):return dict(phase=phase,start_ns=a,end_ns=b,nodes=n,issued_nodes=issued)
    return dict(schema='mtdp-q3-warm-representation-batch-v1',batch_id='synthetic',cache_kind='representation',
        cache_definition_sha256='a'*64,tt_reused=False,os_cache_controlled=False,
        planned_queries=[dict(query_id=str(i),node_limit=10) for i in range(4)],setup_node_limit=2,batch_node_limit=42,
        setup_status='completed',setup_stages=[stage('cache_build',20,200,2,2)],start_ns=0,end_ns=1000,cache_payload_bytes=8,
        queries=[dict(query_id='0',cache_result='hit',status='completed',start_ns=300,end_ns=400,stages=[stage('lookup',320,350,0)]),
                 dict(query_id='1',cache_result='miss',status='fallback',start_ns=450,end_ns=600,stages=[stage('lookup',460,480,0),stage('fallback',500,580,5,8)]),
                 dict(query_id='2',cache_result='bypass',status='error',start_ns=650,end_ns=700,stages=[stage('search',660,690,None,10)]),
                 dict(query_id='3',cache_result='not_run',status='not_run',start_ns=800,end_ns=800,stages=[])])


class WarmTests(unittest.TestCase):
    def test_setup_and_total_use_complete_fixed_denominator(self):
        r=audit(fixture())
        self.assertEqual(r['planned_queries'],4);self.assertEqual(r['attempted_queries'],3)
        self.assertEqual(r['setup_amortization'],dict(numerator_ns=300,denominator_planned_queries=4))
        self.assertEqual(r['total_amortization'],dict(numerator_ns=1000,denominator_planned_queries=4))
        self.assertEqual(r['setup_elapsed_ns']+r['query_elapsed_ns']+r['between_queries_and_finalization_ns'],1000)
        self.assertEqual(r['setup_stage_elapsed_ns']+r['setup_orchestration_elapsed_ns'],300)
        self.assertEqual((r['status_counts']['fallback'],r['status_counts']['error'],r['status_counts']['not_run']),(1,1,1))

    def test_unknown_failed_nodes_are_not_zero(self):
        r=audit(fixture());self.assertIsNone(r['total_measured_nodes'])
        self.assertEqual(r['known_measured_nodes'],7);self.assertEqual(r['unknown_node_stages'],1)
        self.assertFalse(r['within_batch_node_limit']);self.assertFalse(r['all_planned_succeeded'])

    def test_known_error_cost_still_counts(self):
        f=fixture();f['queries'][2]['stages'][0]['nodes']=3
        r=audit(f);self.assertEqual(r['total_measured_nodes'],10)
        self.assertTrue(r['within_batch_node_limit']);self.assertFalse(r['all_planned_succeeded'])

    def test_setup_engine_work_cannot_disappear_from_budget(self):
        f=fixture();f['batch_node_limit']=40
        with self.assertRaises(ValueError):audit(f)
        f=fixture();f['setup_node_limit']=1;f['batch_node_limit']=41
        self.assertFalse(audit(f)['within_setup_node_limit'])

    def test_no_censoring_duplicates_missing_or_order_changes(self):
        for mode in ['missing','duplicate','order']:
            f=fixture()
            if mode=='missing':f['queries'].pop()
            elif mode=='duplicate':f['planned_queries'][1]['query_id']='0'
            else:f['queries'].reverse()
            with self.assertRaises(ValueError):audit(f)

    def test_setup_required_and_not_overlapping_first_query(self):
        for rows in [[],[dict(phase='cache_build',start_ns=20,end_ns=301,nodes=0,issued_nodes=None)]]:
            f=fixture();f['setup_stages']=rows
            with self.assertRaises(ValueError):audit(f)

    def test_overlapping_queries_or_stages_are_rejected(self):
        f=fixture();f['queries'][1]['start_ns']=399
        with self.assertRaises(ValueError):audit(f)
        f=fixture();f['queries'][1]['stages'][1]['start_ns']=479
        with self.assertRaises(ValueError):audit(f)

    def test_not_run_is_not_executed_or_successful(self):
        for change in [dict(end_ns=801),dict(cache_result='hit'),dict(status='completed')]:
            f=fixture();f['queries'][3].update(change)
            with self.assertRaises(ValueError):audit(f)

    def test_success_with_unknown_nodes_fails_closed(self):
        f=fixture();f['queries'][2]['status']='completed'
        with self.assertRaises(ValueError):audit(f)

    def test_overruns_retained_even_if_pooled_batch_budget_fits(self):
        f=fixture();f['queries'][2]['stages'][0]['nodes']=3;f['queries'][1]['stages'][1]['nodes']=9
        r=audit(f);self.assertEqual(r['total_measured_nodes'],14)
        self.assertEqual(r['issued_cap_overruns'],1);self.assertFalse(r['within_batch_node_limit'])
        self.assertFalse(r['within_query_node_limits'])

    def test_tt_os_and_cache_identity_cannot_be_conflated(self):
        for change in [dict(tt_reused=True),dict(os_cache_controlled=True),dict(cache_kind='TT'),dict(cache_definition_sha256='unknown')]:
            f=fixture();f.update(change)
            with self.assertRaises(ValueError):audit(f)

    def test_payload_bytes_are_never_claimed_as_peak_memory(self):
        f=fixture();f['cache_payload_bytes']=None;r=audit(f)
        self.assertIsNone(r['cache_payload_bytes']);self.assertFalse(r['payload_is_peak_process_memory'])
        self.assertFalse(r['fixed_quality_or_speed_gain_established'])

    def test_invalid_integer_fields_and_unknown_fields_rejected(self):
        for change in [dict(start_ns=True),dict(cache_payload_bytes=-1),dict(batch_node_limit=1.5),dict(extra=0)]:
            f=fixture();f.update(change)
            with self.assertRaises(ValueError):audit(f)

    def recorder(self):
        return WarmBatchRecorder(batch_id='toy',planned_queries=[dict(query_id='a',node_limit=0),dict(query_id='b',node_limit=0)],
            setup_node_limit=0,cache_definition_sha256='a'*64)

    def test_actual_clock_cache_build_hit_fallback(self):
        b=self.recorder()
        with b.setup('cache_build') as s:s.update(nodes=0,issued_nodes=None);cache={'toy':b'payload'}
        with b.query('a','hit') as q:
            with q.stage('lookup') as s:s.update(nodes=0,issued_nodes=None);self.assertEqual(cache['toy'],b'payload')
        with b.query('b','miss') as q:
            with q.stage('fallback') as s:s.update(nodes=0,issued_nodes=None)
            q.raw['status']='fallback'
        raw,r=b.finish(cache_payload_bytes=7)
        self.assertEqual(r['total_measured_nodes'],0);self.assertTrue(r['all_planned_succeeded'])
        self.assertEqual(r['setup_amortization']['denominator_planned_queries'],2)
        with self.assertRaises(ValueError):b.finish(cache_payload_bytes=7)

    def test_failure_then_not_run_preserves_planned_slots(self):
        b=self.recorder()
        with b.setup('cache_build') as s:s.update(nodes=0,issued_nodes=None)
        with self.assertRaises(TimeoutError):
            with b.query('a','bypass') as q:
                with q.stage('lookup') as s:s.update(nodes=0,issued_nodes=None);raise TimeoutError('synthetic CPU-only timeout')
        b.skip('b');raw,r=b.finish(cache_payload_bytes=0)
        self.assertEqual((r['planned_queries'],r['status_counts']['timeout'],r['status_counts']['not_run']),(2,1,1))
        self.assertEqual(r['total_measured_nodes'],0);self.assertFalse(r['all_planned_succeeded'])

    def test_recorder_disallows_setup_after_query_and_nested_or_reordered_query(self):
        b=self.recorder()
        with b.setup('cache_build') as s:s.update(nodes=0,issued_nodes=None)
        with self.assertRaises(ValueError):
            with b.query('b','hit'):pass
        with b.query('a','hit') as q:
            with q.stage('lookup') as s:
                s.update(nodes=0,issued_nodes=None)
                with self.assertRaises(ValueError):
                    with q.stage('lookup'):pass
                with self.assertRaises(ValueError):b.skip('b')
        with self.assertRaises(ValueError):
            with b.setup('cache_load'):pass
        with self.assertRaises(ValueError):b.finish(cache_payload_bytes=0)


if __name__=='__main__':unittest.main()
