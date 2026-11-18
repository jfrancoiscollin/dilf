import copy
import pytest
from research.mtdp.jass_benchmark.named_signature_annotation import annotate


def fixture():
    fen='W:W31:B1'
    m={'benchmark_targets':[{'target_fen':fen,'target_games':['g:1'],'source_fens':{'L':'W:W31:B2','LCB':'W:W31:B2'}}]}
    row={'fen':fen,'games':['g:1'],'optimal_sets_overlap':False,
         'a_to_b':{'ordinary_regret_centimen':7,'best_centimen':7,'transferred_centimen':0}}
    c={'schema':'mtdp-named-source16-sensitivity-v1','source_depth':16,'target_depth':16,
       'geometry':{a:{'rows':[copy.deepcopy(row)]} for a in ('L','LCB')}}
    return m,c


def test_exact_existing_quiet_signature_label_and_disagreement_cost():
    m,c=fixture();r=annotate(m,c)['LCB']
    assert len(r['rows'])==1 and r['rows'][0]['same_full_quiet_signature']
    assert r['strata']['true']['mean_regret']==7 and r['strata']['true']['positive_cost_mean']==7
    assert r['strata']['true']['optimal_sets_disjoint']==1


def test_population_or_ownership_cannot_be_redefined():
    m,c=fixture();c['geometry']['L']['rows'][0]['games']=['different']
    with pytest.raises(ValueError,match='ownership'):annotate(m,c)
    m,c=fixture();c['geometry']['LCB']['rows']=[]
    with pytest.raises(ValueError,match='population'):annotate(m,c)


def test_undefined_signature_never_counts_as_equal_none():
    m,c=fixture();m['benchmark_targets'][0]['source_fens']['L']='W:WK31:B2'
    with pytest.raises(ValueError,match='undefined'):annotate(m,c)
