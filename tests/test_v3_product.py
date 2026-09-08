from fabops.operations.control_tower import mission_control, lot_control, fab_map
from fabops.operations.master_data import synthetic_tool_state
from fabops.optimization.rolling_horizon import optimize_rolling_schedule
from fabops.experiments.stress_lab import run_stress_mission
from fabops.decision.orchestrator_v3 import orchestrate_decision


def test_mission_control_has_operational_depth():
    out=mission_control(17,60)
    assert len(out['bays'])==8
    assert len(out['tool_state'])>=18
    assert out['kpis']['throughput']==60
    assert out['mode']=='REFERENCE_REPLAY'


def test_lot_control_contains_routing_and_risk():
    rows=lot_control(17,30)
    assert len(rows)==30
    assert {'lot_id','bay','recipe','progress','queue_age','tardiness_risk','predicted_finish'} <= set(rows[0])
    assert any(r['hot'] for r in rows)


def test_fab_map_reentrant_links():
    out=fab_map(17)
    assert len(out['bays'])==8
    assert any(x.get('type')=='REENTRANT' for x in out['links'])
    assert out['reticles']


def test_tool_state_has_pm_and_qualification():
    rows=synthetic_tool_state(17)
    assert any(t['pm_urgency']>.5 for t in rows)
    assert all(t['recipes'] for t in rows)


def test_rolling_scheduler_respects_qualification():
    tools=[{'tool_id':'T1','bay':'PHOTO','recipes':['L1'],'setup_family':'L1'},{'tool_id':'T2','bay':'PHOTO','recipes':['L2'],'setup_family':'L2'}]
    jobs=[{'job_id':'J1','lot_id':'L1','bay':'PHOTO','recipe':'L1','process_time':5,'due':10,'priority':2}, {'job_id':'J2','lot_id':'L2','bay':'PHOTO','recipe':'L2','process_time':6,'due':20,'priority':1}]
    out=optimize_rolling_schedule(jobs,tools,40)
    assert out.success
    m={x['job_id']:x['tool_id'] for x in out.assignments}
    assert m=={'J1':'T1','J2':'T2'}


def test_stress_lab_changes_twin_metrics():
    out=run_stress_mission('PHOTO_OUTAGE',.5,31,50)
    assert out.scenario=='PHOTO_OUTAGE'
    assert out.delta['avg_cycle_time'] != 0 or out.delta['avg_tardiness'] != 0
    assert out.recommendations


def test_integrated_decision_is_human_gated():
    out=orchestrate_decision('DEMAND_SURGE',.4,31)
    assert out.state=='REVIEW'
    assert out.actions
    assert out.human_gate=='FAB_SHIFT_SUPERVISOR'
    assert all(a['execute']=='REQUIRES_APPROVAL' for a in out.actions)
