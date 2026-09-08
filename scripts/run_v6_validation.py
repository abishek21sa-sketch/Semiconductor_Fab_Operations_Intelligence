from __future__ import annotations
import json
from fabops.api.app import APP_VERSION
from fabops.simulation.coupled_twin import run_coupled_twin
from fabops.optimization.multi_operation import optimize_multi_operation, build_lot_operations
from fabops.decision.closed_loop import run_closed_loop_recovery
from fabops.experiments.scaling_v6 import scaling_experiment

def main():
    twin=run_coupled_twin(48,17,interarrival=3.8,failure_rate=.015,rework_sensitivity=.22)
    sched=optimize_multi_operation(build_lot_operations(3,17),96,17)
    closed=run_closed_loop_recovery("PHOTO_OUTAGE",41,36,.35)
    scale=scaling_experiment(17)
    out={"release":"FLAGSHIP_V6","version":APP_VERSION,
         "coupled_twin":{"lots":twin.lots,"completed":twin.completed,"event_count":twin.event_count,
                         "avg_cycle_time":twin.avg_cycle_time,"p95_cycle_time":twin.p95_cycle_time,
                         "queue_time_breaches":twin.queue_time_breaches,"rework_loops":twin.rework_loops,
                         "scrap_lots":twin.scrap_lots,"reticle_wait":twin.reticle_wait,"batch_runs":twin.batch_runs,
                         "mean_batch_fill":twin.mean_batch_fill,"pm_interruptions":twin.pm_interruptions,"tool_failures":twin.tool_failures},
         "multi_operation_schedule":{"success":sched.success,"lots":sched.lots,"operations":sched.operations,
                                     "queue_breaches":sched.queue_breaches,"reticle_conflicts":sched.reticle_conflicts,
                                     "precedence_violations":sched.precedence_violations,"pm_conflicts":sched.pm_conflicts,
                                     "objective":sched.objective},
         "closed_loop_recovery":{"scenario":closed.scenario,"policy":closed.recovery_policy,
                                 "cycle_time_recovery":closed.cycle_time_recovery,
                                 "queue_breach_recovery":closed.queue_breach_recovery,
                                 "rework_recovery":closed.rework_recovery,"scrap_recovery":closed.scrap_recovery,
                                 "decision_state":closed.decision_state},
         "scaling":scale,
         "claim_boundary":"Reference virtual-fab integration/scaling evidence only; no site performance or production execution claim."}
    print(json.dumps(out,indent=2))
    return out

if __name__=="__main__": main()
