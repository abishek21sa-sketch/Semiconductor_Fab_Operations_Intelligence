from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from fabops.experiments.stress_lab import run_stress_mission

MISSIONS=("PHOTO_OUTAGE","DEMAND_SURGE","AMHS_DEGRADATION","YIELD_EXCURSION","HOT_LOT_SURGE")

def compare_stress_policies(seed:int=31,lots:int=80,magnitude:float=.35) -> dict:
    runs=[]
    for i,m in enumerate(MISSIONS):
        r=run_stress_mission(m,magnitude,seed+i,lots).to_dict()
        score=(max(0,r["delta"]["avg_cycle_time"])+max(0,r["delta"]["avg_tardiness"])+max(0,r["delta"]["avg_wip"])*5)
        runs.append({**r,"impact_score":round(score,3)})
    runs.sort(key=lambda x:x["impact_score"],reverse=True)
    return {"experiment_id":f"EXP-{seed}-{lots}-{int(magnitude*100)}","created_at":datetime.now(timezone.utc).isoformat(),
            "missions":runs,"worst_case":runs[0]["scenario"],"replication_design":"paired deterministic reference seeds",
            "claim_boundary":"Reference stress experiment; not site-calibrated."}
