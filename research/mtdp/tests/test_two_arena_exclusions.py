"""Synthetic whole-arena exclusion extension; no new cohort is used."""
import copy
import pytest
from research.mtdp.jass_benchmark import two_arena_exclusions as gate


def fixture():
    r={'confirmed_fens':['old'],'public_game_ids':['known'],'normalized_token_sequence_sha256':['old-token']}
    h={'confirmed_fens':['old','old-prefix'],'fingerprints':['old-trajectory']}
    e={'confirmed_fens':['new','new-quarantine-prefix'],'fingerprints':['new-trajectory','old-trajectory'],
       'game_audit':{'p:1':{'status':'indexed','trajectory_sha256':'new-trajectory'},'p:2':{'status':'quarantined','confirmed_prefix_positions':1}},
       'status_counts':{'indexed':1,'quarantined':1}}
    return r,h,e


def test_old_exclusions_quarantined_prefixes_and_whole_ids_preserved():
    r,h,e=fixture();v=gate.combine(r,h,e,['new1','new2'],['new-token','quarantined-token'])
    assert v['confirmed_fens']==['new','new-quarantine-prefix','old','old-prefix']
    assert v['public_game_ids']==['known','new1','new2']
    assert 'quarantined-token' in v['normalized_token_sequence_sha256']
    assert v['fingerprints']==['new-trajectory','old-trajectory']
    assert v['added_complete_trajectories_already_historical']==1


def test_missing_old_fen_or_duplicate_public_id_is_rejected():
    r,h,e=fixture();h['confirmed_fens']=[]
    with pytest.raises(ValueError,match='lost'):gate.combine(r,h,e,['new'],['t'])
    r,h,e=fixture()
    with pytest.raises(ValueError,match='repeats'):gate.combine(r,h,e,['new','new'],['t'])


def test_quarantine_never_certifies_a_full_trajectory():
    r,h,e=fixture();e['game_audit']['p:2']['trajectory_sha256']='invented'
    with pytest.raises(ValueError,match='quarantined'):gate.combine(r,h,e,['new'],['t'])


def test_sets_are_sorted_and_old_inputs_are_not_mutated():
    r,h,e=fixture();before=copy.deepcopy((r,h,e))
    a=gate.combine(r,h,e,['z','a'],['z','a'])
    b=gate.combine(r,h,e,['a','z'],['a','z'])
    assert a==b and (r,h,e)==before
