from __future__ import annotations
import json, tempfile, gc
from pathlib import Path

from fabops.ingestion.events import FabEvent, FabEventType
from fabops.persistence.sqlite import FabRepository

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def main():
    from fabops.api.app import APP_VERSION, APP_RELEASE
    from fabops.simulation.coupled_twin import run_coupled_twin
    from fabops.optimization.multi_operation import optimize_multi_operation, build_lot_operations
    from fabops.decision.closed_loop import run_closed_loop_recovery
    from fabops.semiconductor.chambers import chamber_state
    from fabops.operations.genealogy import lot_genealogy, queue_time_watch
    from fabops.data_fabric.mes_simulator import generate_mes_stream
    from fabops.data_fabric.validators import validate_events
    from fabops.data_fabric.replay import replay_manufacturing_state
    from fabops.genealogy.wafer_tree import build_wafer_genealogy
    from fabops.equipment.digital_thread import build_equipment_threads

    require(APP_VERSION=="7.2.0",f"unexpected app version {APP_VERSION}")

    twin=run_coupled_twin(28,17,interarrival=4.0,failure_rate=.012)
    require(twin.completed>0,"coupled twin completed no lots")
    require(twin.event_count>0,"coupled twin emitted no events")
    require(twin.batch_runs>0,"batch engine did not execute")

    # Small deterministic acceptance instance; larger cases remain research/scaling probes.
    sched=optimize_multi_operation(build_lot_operations(2,17),96,17)
    require(sched.success,"multi-operation scheduler failed")
    require(sched.precedence_violations==0,"precedence violation")
    require(sched.queue_breaches==0,"queue-time violation")
    require(sched.reticle_conflicts==0,"reticle conflict")
    require(sched.pm_conflicts==0,"PM conflict")

    recovery=run_closed_loop_recovery("PHOTO_OUTAGE",41,28,.30)
    require(recovery.decision_state=="REVIEW","closed-loop decision gate missing")
    require(recovery.recovered!=recovery.disrupted,"recovery did not change future state")

    genealogy=lot_genealogy("LOT-017",17)
    require(genealogy["route_length"]>=14,"genealogy route too shallow")
    require(len(chamber_state(17))>=27,"chamber model incomplete")
    require(len(queue_time_watch(17,20))==20,"queue-time watch incomplete")

    # V7 manufacturing data fabric.
    events=generate_mes_stream(12,6,71)
    require(validate_events(events)["valid"],"V7 manufacturing event validation failed")
    state=replay_manufacturing_state(events)
    require(state["counts"]["lots"]==12,"V7 MES replay lot count mismatch")
    wafer=build_wafer_genealogy(events)
    require(wafer["wafer_count"]>0,"V7 wafer genealogy empty")
    equipment=build_equipment_threads(events)
    require(equipment["count"]>0,"V7 equipment digital thread empty")

    # Persistence contract, isolated from runtime DB and Windows lock-safe.
    db=Path(tempfile.gettempdir())/"fabops_windows_acceptance_v7.db"
    try:
        if db.exists(): db.unlink()
    except PermissionError:
        pass

    repository=FabRepository(db)
    event=FabEvent(event_id="ACC-1",event_type=FabEventType.LOT_RELEASED,timestamp=1.0,lot_id="ACC-LOT",payload={})
    require(repository.append_events([event])==1,"event persistence failed")
    require(len(repository.read_events())==1,"event replay failed")
    del repository
    gc.collect()
    try:
        if db.exists(): db.unlink()
    except PermissionError:
        pass

    out={"release":APP_RELEASE,"version":APP_VERSION,"status":"PASS",
         "coupled_twin":{"completed":twin.completed,"events":twin.event_count,"batch_runs":twin.batch_runs,
                         "queue_breaches":twin.queue_time_breaches,"rework_loops":twin.rework_loops},
         "multi_operation_schedule":{"operations":sched.operations,"precedence_violations":sched.precedence_violations,
                                     "queue_breaches":sched.queue_breaches,"reticle_conflicts":sched.reticle_conflicts,
                                     "pm_conflicts":sched.pm_conflicts},
         "closed_loop":{"scenario":recovery.scenario,"policy":recovery.recovery_policy,
                        "cycle_time_recovery":recovery.cycle_time_recovery,"state":recovery.decision_state},
         "data_fabric":{"events":len(events),"lots":state["counts"]["lots"],"wafers":wafer["wafer_count"],
                        "tools":equipment["count"]},
         "runtime_contract":"Official Windows acceptance uses deterministic functional contracts plus real HTTP smoke."}
    print(json.dumps(out,indent=2))
    print("WINDOWS_FUNCTIONAL_ACCEPTANCE=PASS")

if __name__=="__main__":
    main()
