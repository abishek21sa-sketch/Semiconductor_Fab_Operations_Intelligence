from __future__ import annotations
from collections import defaultdict
import numpy as np

def bottleneck_report(sim_result: dict) -> dict:
    util=sim_result.get("utilization",{})
    ranked=sorted(util.items(), key=lambda kv:kv[1], reverse=True)
    by_group=defaultdict(list)
    for tool,val in util.items(): by_group[tool.split("-")[0]].append(val)
    groups={g:round(float(np.mean(v)),4) for g,v in by_group.items()}
    return {
        "tool_ranking":[{"tool_id":t,"utilization":u} for t,u in ranked],
        "group_utilization":dict(sorted(groups.items(), key=lambda kv:kv[1], reverse=True)),
        "primary_bottleneck":ranked[0][0] if ranked else None,
    }

def little_law_check(sim_result: dict) -> dict:
    makespan=max(float(sim_result.get("makespan",0)),1e-9)
    throughput=float(sim_result.get("throughput",0))/makespan
    ct=float(sim_result.get("avg_cycle_time",0))
    implied=throughput*ct
    observed=float(sim_result.get("avg_wip",0))
    return {"throughput_rate":round(throughput,6),"avg_cycle_time":ct,"observed_avg_wip":observed,
            "little_law_implied_wip":round(implied,3),"absolute_gap":round(abs(implied-observed),3)}
