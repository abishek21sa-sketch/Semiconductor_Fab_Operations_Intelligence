from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
import numpy as np
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.analytics.factory_physics import bottleneck_report

@dataclass(frozen=True)
class Scenario:
    name:str
    lots:int=80
    seed:int=7
    interarrival:float=6.0
    failure_rate:float=0.0
    repair_time:float=12.0
    rule:str="CR"


def run_scenario(s:Scenario)->dict:
    cfg=build_minifab_config(); lots=generate_lots(s.lots,s.seed,s.interarrival)
    res=FabSimulator(cfg,seed=s.seed,failure_rate=s.failure_rate,repair_time=s.repair_time).run(lots,s.rule)
    out=res.to_dict(); out["scenario"]=asdict(s); out["bottleneck"]=bottleneck_report(out)
    out["run_id"]=hashlib.sha256(json.dumps(asdict(s),sort_keys=True).encode()).hexdigest()[:16]
    return out

def monte_carlo(s:Scenario, replications:int=20)->dict:
    results=[]
    for i in range(replications):
        si=Scenario(**{**asdict(s),"seed":s.seed+i})
        results.append(run_scenario(si))
    metrics={}
    for key in ("avg_cycle_time","avg_tardiness","on_time_rate","avg_wip","makespan"):
        vals=np.array([r[key] for r in results],float)
        metrics[key]={"mean":round(float(vals.mean()),3),"std":round(float(vals.std(ddof=1)) if len(vals)>1 else 0,3),
                      "p05":round(float(np.percentile(vals,5)),3),"p95":round(float(np.percentile(vals,95)),3)}
    return {"scenario":asdict(s),"replications":replications,"metrics":metrics,
            "bottleneck_frequency":_freq([r["bottleneck"]["primary_bottleneck"] for r in results])}

def _freq(values):
    out={}
    for v in values: out[v]=out.get(v,0)+1
    return dict(sorted(out.items(),key=lambda kv:kv[1],reverse=True))
