import copy
import unittest
from research.mtdp.jass_benchmark.q3_archived_budget_quality import contrast, index_rows, cell


class GridTests(unittest.TestCase):
    def cells(self, regrets):
        return {('arena',str(i)):dict(owner='g'+str(i),ordinary=True,regret=r,move='a',category='ordinary') for i,r in enumerate(regrets)}

    def specimen(self):
        q=dict(total_budget=100,owner='g',verification_nodes=10,main_nodes={'control':90,'native_full':100},
            best_reference_score=30,optimal_moves=['b'],control_regret=5,control_optimal=0,native_full_regret=5,native_full_optimal=0,
            arms={a:dict(move='a',best_category='ordinary',candidate_category='ordinary',ordinary_regret_centimen=5,
                         score=25,covered=False) for a in ['control','native_full']})
        t=dict(budget=100,owner='g',verification_nodes=10,
               control=dict(nodes=90,depth_ceiling=False,stop='nodes',best_move='a'),
               native=dict(nodes=100,depth_ceiling=False,stop='nodes',best_move='a'))
        return q,t

    def test_self_reference_zero_deltas_no_cheaper_point(self):
        c=self.cells([0,5]);r=contrast(c,c,50000,50000)
        self.assertEqual(r['mean_paired_regret_delta_scan_units'],dict(numerator=0,denominator=1))
        self.assertEqual((r['improved'],r['equal'],r['worse']),(0,2,0))
        self.assertFalse(r['cheaper_with_no_observed_mean_increase'])

    def test_less_nodes_and_worse_mean_fails_descriptive_criterion(self):
        r=contrast(self.cells([5,5]),self.cells([1,1]),10000,50000)
        self.assertEqual(r['node_cost_ratio'],dict(numerator=1,denominator=5))
        self.assertFalse(r['cheaper_with_no_observed_mean_increase'])
        self.assertEqual(r['worse'],2)

    def test_mean_and_per_position_safety_are_distinct(self):
        r=contrast(self.cells([0,4]),self.cells([3,3]),10000,50000)
        self.assertTrue(r['cheaper_with_no_observed_mean_increase'])
        self.assertFalse(r['all_positions_not_worse_observed'])
        self.assertFalse(r['independent_quality_gate_passed'])
        self.assertFalse(r['exact_wdl_preservation_established'])

    def test_more_nodes_not_automatically_cheaper_even_with_better_quality(self):
        r=contrast(self.cells([0,0]),self.cells([4,4]),200000,50000)
        self.assertTrue(r['mean_not_above_reference_observed'])
        self.assertFalse(r['cheaper_with_no_observed_mean_increase'])
        self.assertEqual(r['node_cost_ratio'],dict(numerator=4,denominator=1))

    def test_all_positions_and_owners_must_match(self):
        c=self.cells([1,2]);b=self.cells([1,2]);c.pop(('arena','0'))
        with self.assertRaises(ValueError):contrast(c,b,1,5)
        c=self.cells([1,2]);c['arena','0']['owner']='other'
        with self.assertRaises(ValueError):contrast(c,b,1,5)

    def test_duplicate_or_empty_grid_rejected(self):
        with self.assertRaises(ValueError):index_rows([])
        with self.assertRaises(ValueError):index_rows([dict(event='e',fen='f'),dict(event='e',fen='f')])

    def test_categories_never_coerced_into_numeric_regret(self):
        c=self.cells([1,2]);c['arena','1'].update(ordinary=False,regret=None,category='win')
        r=contrast(c,self.cells([1,2]),10000,50000)
        self.assertEqual(r['nonordinary_pairs'],1)
        self.assertIsNone(r['mean_paired_regret_delta_scan_units'])
        self.assertIsNone(r['cheaper_with_no_observed_mean_increase'])
        self.assertEqual(len(r['rows']),2)

    def test_verification_is_charged_and_covered_means_optimality(self):
        q,t=self.specimen();r=cell(q,t,'control',100)
        self.assertEqual(r['regret'],5)  # covered=False is valid for a nonoptimal move.
        q['arms']['control']['covered']=True
        with self.assertRaises(ValueError):cell(q,t,'control',100)

    def test_missing_node_charge_ceiling_and_wrong_move_rejected(self):
        for change in [dict(nodes=89),dict(depth_ceiling=True),dict(best_move='b')]:
            q,t=self.specimen();t['control'].update(change)
            with self.assertRaises(ValueError):cell(q,t,'control',100)
        q,t=self.specimen();q['verification_nodes']=0;t['verification_nodes']=0
        with self.assertRaises(ValueError):cell(q,t,'control',100)

    def test_regret_optimum_and_reference_fields_reconcile(self):
        for key,value in [('score',24),('ordinary_regret_centimen',-1),('covered',1)]:
            q,t=self.specimen();q['arms']['control'][key]=value
            with self.assertRaises(ValueError):cell(q,t,'control',100)
        q,t=self.specimen();q['optimal_moves']=['a']
        with self.assertRaises(ValueError):cell(q,t,'control',100)

    def test_residual_arms_not_promoted_to_equal_total_budget(self):
        q,t=self.specimen()
        with self.assertRaises(ValueError):cell(q,t,'native_residual',100)


if __name__=='__main__':unittest.main()
