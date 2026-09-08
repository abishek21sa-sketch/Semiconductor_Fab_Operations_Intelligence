from __future__ import annotations
import random, statistics, time
from fabops.optimization.rare_fab import optimize_rare_fab

def _cvar(xs:list[float],alpha=.9):
    q=sorted(xs)[min(len(xs)-1,int(alpha*(len(xs)-1)))]; tail=[x for x in xs if x>=q]; return sum(tail)/len(tail)

def rare_fab_benchmark(seed:int=17, replications:int=40, lot_count:int=12) -> dict:
    """Common-random-number synthetic challenge harness with ablation and falsification fields."""
    rng=random.Random(seed); paired=[]; rare_losses=[]; base_losses=[]; runtimes=[]
    for r in range(replications):
        lots=[]
        for i in range(lot_count):
            lots.append({"lot_id":f"L{i:03}","priority":1+(i%3),"due_slot":i%4,"queue_risk":rng.uniform(.2,1.2),"amhs_moves":1+i%4,
                         "energy_kwh":rng.uniform(1,4),"maintenance_interaction":rng.random(),"qualification_risk":rng.random()*.5,
                         "wip_units":1,"workload":{"PHOTO":1+(i%2),"ETCH":.6+(i%3)*.2}})
        slots=[{"slot":t,"wip_limit":ceil,"capacity":{"PHOTO":ceil*1.7,"ETCH":ceil*1.5},"base_penalty":t*.1} for t,ceil in enumerate([4,4,4,4])]
        scenarios=[]
        for k in range(18):
            hot=rng.randrange(len(slots)); pressure=[rng.uniform(.8,1.2) for _ in slots]; pressure[hot]*=rng.uniform(1.7,2.8)
            scenarios.append({"queue":rng.uniform(.8,1.8),"amhs":rng.uniform(.8,2.0),"energy":rng.uniform(.8,1.8),"maintenance":rng.uniform(.7,1.9),"qualification":rng.uniform(.8,1.6),"slot_pressure":pressure})
        t=time.perf_counter(); plan=optimize_rare_fab(lots,slots,scenarios,.9,.35); runtimes.append(time.perf_counter()-t)
        rare=statistics.mean(plan.scenario_losses)
        # FIFO baseline under the same slot WIP feasibility: preserve lot order and fill slots in order.
        base=[]
        from fabops.optimization.rare_fab import _cost
        fifo_slots=[min(i//4, len(slots)-1) for i in range(len(lots))]
        for st in scenarios:
            base.append(sum(_cost(l,fifo_slots[i],st) for i,l in enumerate(lots)))
        b=statistics.mean(base); rare_losses.append(rare); base_losses.append(b); paired.append(b-rare)
    dominance=sum(x>0 for x in paired)/len(paired)
    return {"evidence_class":"REFERENCE_SYNTHETIC_BENCHMARK","replications":replications,"lot_count":lot_count,"seed":seed,
            "paired_mean_improvement":round(statistics.mean(paired),4),"dominance_rate":round(dominance,4),
            "rare_fab_mean_loss":round(statistics.mean(rare_losses),4),"baseline_mean_loss":round(statistics.mean(base_losses),4),
            "rare_fab_cvar90":round(_cvar(rare_losses,.9),4),"baseline_cvar90":round(_cvar(base_losses,.9),4),
            "mean_runtime_s":round(statistics.mean(runtimes),6),"falsification_pass": dominance>.5 and statistics.mean(paired)>0,
            "claim_boundary":"Synthetic benchmark mechanics only; not site performance or novelty proof."}
