from fabops.simulation.coupled_twin import run_coupled_twin
from fabops.optimization.multi_operation import optimize_multi_operation, build_lot_operations
from fabops.decision.closed_loop import run_closed_loop_recovery
from fabops.experiments.scaling_v6 import scaling_experiment

def test_coupled_twin_runs_and_emits_semiconductor_events():
    r=run_coupled_twin(24,17,interarrival=4.0,failure_rate=.01)
    assert r.completed>0
    kinds={x["event"] for x in r.event_log}
    assert "operation_start" in kinds or "batch_start" in kinds
    assert r.event_count==len(r.event_log)

def test_coupled_twin_batch_and_rework_fields():
    r=run_coupled_twin(32,19,interarrival=3.5,failure_rate=.01,rework_sensitivity=.35)
    assert r.batch_runs>=1
    assert 0<=r.mean_batch_fill<=1
    assert r.rework_loops>=0 and r.scrap_lots>=0

def test_multi_operation_schedule_preserves_precedence():
    s=optimize_multi_operation(build_lot_operations(3,17),96,17)
    assert s.success
    assert s.precedence_violations==0
    assert s.queue_breaches==0
    assert s.reticle_conflicts==0

def test_closed_loop_recovery_changes_future_state():
    r=run_closed_loop_recovery("PHOTO_OUTAGE",41,28,.30)
    assert r.recovery_policy
    assert r.decision_state=="REVIEW"
    assert r.recovered != r.disrupted

def test_scaling_contract():
    x=scaling_experiment(17)
    assert len(x["twin_scaling"])==4
    assert len(x["schedule_scaling"])==3
    assert all("runtime_s" in r for r in x["schedule_scaling"])
