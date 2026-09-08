from fabops.semiconductor.chambers import chamber_state, form_batches, reticle_contention, qualification_matrix
from fabops.optimization.integrated_fab import optimize_integrated_schedule, demo_integrated_jobs
from fabops.optimization.stochastic_recovery import optimize_recovery

def test_chamber_model_expands_tools():
    rows=chamber_state(17)
    assert len(rows) >= 19
    assert all("chamber_id" in x and "tool_id" in x for x in rows)

def test_batch_formation_respects_capacity():
    lots=[{"lot_id":f"L{i}","bay":"DIFF","recipe":"D1","ready_time":i} for i in range(8)]
    out=form_batches(lots,max_wait=10)
    assert out["batches"]
    assert all(b["size"]<=b["capacity"] for b in out["batches"])

def test_reticle_contention_serializes_requests():
    req=[{"lot_id":"L1","reticle":"R-P1-L1","ready_time":0,"duration":3},
         {"lot_id":"L2","reticle":"R-P1-L1","ready_time":1,"duration":3}]
    out=reticle_contention(req,12)
    assert out["conflicts"]==1
    a=out["assignments"]
    assert a[1]["start"]>=a[0]["finish"]

def test_integrated_schedule_hard_constraints():
    out=optimize_integrated_schedule(demo_integrated_jobs(17,10),48,17)
    assert out.success
    assert out.queue_breaches==0
    assert out.reticle_conflicts==0
    assert len(out.assignments)==10

def test_stochastic_recovery_selects_action():
    out=optimize_recovery()
    assert out.success
    assert out.action!="NONE"
    assert out.cvar>=0 and out.expected_loss>=0

def test_qualification_matrix_has_batch_and_chambers():
    q=qualification_matrix()
    assert q["tools"]["DIFF-01"]["batch_capacity"]==6
    assert q["tools"]["MET-01"]["chambers"]==3
