from __future__ import annotations
from statistics import mean
from time import perf_counter
from fabops.simulation.coupled_twin import run_coupled_twin
from fabops.optimization.multi_operation import optimize_multi_operation, build_lot_operations

def scaling_experiment(seed:int=17)->dict:
    twin_rows=[]
    for n in (24,48,72,96):
        vals=[]; runtimes=[]
        for rep in range(3):
            t0=perf_counter(); r=run_coupled_twin(n,seed+rep,interarrival=4.0,failure_rate=.015); runtimes.append(perf_counter()-t0)
            vals.append(r)
        twin_rows.append({"lots":n,"mean_cycle_time":round(mean(x.avg_cycle_time for x in vals),3),
                          "mean_queue_breaches":round(mean(x.queue_time_breaches for x in vals),2),
                          "mean_rework":round(mean(x.rework_loops for x in vals),2),
                          "mean_runtime_s":round(mean(runtimes),4),
                          "completion_rate":round(mean(x.completed/x.lots for x in vals),4)})
    schedule_rows=[]
    for n in (2,3,4):
        jobs=build_lot_operations(n,seed)
        t0=perf_counter(); s=optimize_multi_operation(jobs,96,seed,time_limit=(6.0 if n<=3 else 3.0)); rt=perf_counter()-t0
        schedule_rows.append({"lots":n,"operations":len(jobs),"success":s.success,"runtime_s":round(rt,4),
                              "queue_breaches":s.queue_breaches,"reticle_conflicts":s.reticle_conflicts,
                              "precedence_violations":s.precedence_violations})
    return {"twin_scaling":twin_rows,"schedule_scaling":schedule_rows,
            "claim_boundary":"Reference computational scaling only; not production throughput or capacity evidence."}
