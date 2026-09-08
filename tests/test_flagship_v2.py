from fabops.optimization.rare_fab import optimize_rare_fab
from fabops.control.bay_control import bay_risk_heatmap
from fabops.semiconductor.physics import kingman_queue, operating_curve
from fabops.semiconductor.amhs import simulate_amhs
from fabops.semiconductor.equipment import equipment_risk
from fabops.semiconductor.yield_model import yield_risk
from fabops.research.benchmark import rare_fab_benchmark

def sample():
    lots=[{"lot_id":f"L{i}","priority":1+i%2,"due_slot":i%3,"queue_risk":.4+i*.1,"amhs_moves":1+i%3,"energy_kwh":2+i*.2,"maintenance_interaction":.1,"qualification_risk":.05,"workload":{"PHOTO":1,"ETCH":.5}} for i in range(6)]
    slots=[{"slot":i,"wip_limit":3,"capacity":{"PHOTO":3,"ETCH":2}} for i in range(3)]
    scenarios=[{"queue":1,"amhs":1,"energy":1},{"queue":1.5,"amhs":1.8,"energy":1.3,"maintenance":1.2}]
    return lots,slots,scenarios

def test_rare_fab_feasible_and_all_assigned():
    a,b,c=sample(); p=optimize_rare_fab(a,b,c)
    assert p.success and len(p.assignments)==len(a)
    assert all(v<=3 for v in p.slot_load.values())
    assert p.human_gate.endswith("REVIEW_REQUIRED")

def test_rare_fab_invalid_alpha():
    a,b,c=sample()
    try: optimize_rare_fab(a,b,c,alpha=1)
    except ValueError: pass
    else: raise AssertionError("expected alpha validation")

def test_bay_heatmap_orders_risk():
    x=bay_risk_heatmap([{"bay":"PHOTO","wip":12,"wip_limit":10,"utilization":.96,"queue_age":9,"queue_limit":8,"amhs_delay":4,"amhs_limit":3}, {"bay":"CMP","wip":2,"wip_limit":10,"utilization":.3,"queue_age":1,"queue_limit":8,"amhs_delay":.2,"amhs_limit":3}])
    assert x[0]["bay"]=="PHOTO" and x[0]["state"] in {"WATCH","CONSTRAINED"}

def test_factory_physics_monotonic_curve():
    q=kingman_queue(.8,10,1,1); assert q.approx_wait>0
    c=operating_curve([1,2,3],10,.2); assert c[2]["throughput"]>=c[0]["throughput"]

def test_amhs_congestion():
    moves=[{"request_time":0,"distance":1} for _ in range(10)]
    r=simulate_amhs(moves,vehicles=1); assert r.max_queue>=1 and r.mean_transfer_time>2

def test_equipment_and_yield_gates():
    e=equipment_risk({"tool_id":"PHOTO-1","mtbf":20,"mttr":10,"hours_to_pm":2,"qualified_recipe_fraction":.5,"setups_next_shift":8})
    assert e.risk_score>.2
    y=yield_risk(25,.02,1,4.0); assert y.disposition=="HOLD_LOT"

def test_benchmark_has_claim_boundary():
    r=rare_fab_benchmark(replications=3,lot_count=6); assert r["evidence_class"]=="REFERENCE_SYNTHETIC_BENCHMARK" and "not site" in r["claim_boundary"].lower()
