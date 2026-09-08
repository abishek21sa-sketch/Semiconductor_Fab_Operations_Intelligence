from __future__ import annotations
from dataclasses import dataclass, asdict
from fabops.simulation.coupled_twin import run_coupled_twin
from fabops.optimization.stochastic_recovery import ACTIONS, optimize_recovery

@dataclass(frozen=True)
class ClosedLoopRecovery:
    scenario:str; baseline:dict; disrupted:dict; prior_policy:str; recovery_policy:str; recovered:dict
    cycle_time_recovery:float; queue_breach_recovery:int; rework_recovery:int; scrap_recovery:int
    candidate_policies:list[dict]; decision_state:str; human_gate:str
    def to_dict(self): return asdict(self)

def _summary(r):
    return {"completed":r.completed,"avg_cycle_time":r.avg_cycle_time,"p95_cycle_time":r.p95_cycle_time,
            "queue_time_breaches":r.queue_time_breaches,"rework_loops":r.rework_loops,"scrap_lots":r.scrap_lots,
            "reticle_wait":r.reticle_wait,"batch_runs":r.batch_runs,"pm_interruptions":r.pm_interruptions,
            "tool_failures":r.tool_failures,"on_time_rate":r.on_time_rate}

def _apply(action,args):
    x=dict(args)
    if action=="HOLD_RELEASE":
        x["interarrival"]*=1.20
    elif action=="ALT_ROUTE":
        x["failure_rate"]*=.58
    elif action=="PULL_PM_FORWARD":
        x["failure_rate"]*=.68
    elif action=="PROTECT_RETICLE":
        x["rework_sensitivity"]*=.72; x["failure_rate"]*=.90
    elif action=="BALANCED_RECOVERY":
        x["failure_rate"]*=.70; x["rework_sensitivity"]*=.76; x["interarrival"]*=1.08
    return x

def _loss(r):
    # Operational score used only for policy comparison inside the same reference twin.
    incomplete=max(0,r.lots-r.completed)
    return r.avg_cycle_time + .35*r.p95_cycle_time + 12*r.queue_time_breaches + 5*r.rework_loops + 28*r.scrap_lots + 20*incomplete

def run_closed_loop_recovery(scenario:str="PHOTO_OUTAGE",seed:int=41,lots:int=36,magnitude:float=.35)->ClosedLoopRecovery:
    scenario=scenario.upper(); mag=max(0,min(float(magnitude),1))
    base_args={"lots":lots,"seed":seed,"interarrival":4.2,"failure_rate":.012,"rework_sensitivity":.20}
    disrupted=dict(base_args)
    if scenario=="PHOTO_OUTAGE": disrupted["failure_rate"]=.025+.07*mag
    elif scenario=="DEMAND_SURGE": disrupted["interarrival"]=max(2.0,4.2*(1-.55*mag))
    elif scenario=="YIELD_EXCURSION": disrupted["rework_sensitivity"]=.20+.75*mag
    elif scenario=="AMHS_DEGRADATION":
        disrupted["failure_rate"]=.018+.035*mag; disrupted["interarrival"]=4.2*(1-.15*mag)
    elif scenario=="RETICLE_SHORTAGE":
        disrupted["failure_rate"]=.018+.025*mag; disrupted["rework_sensitivity"]=.20+.15*mag

    baseline=run_coupled_twin(**base_args)
    shock=run_coupled_twin(**disrupted)

    vectors={
      "PHOTO_OUTAGE":{"outage":.9*mag,"demand":.15,"amhs":.15,"yield_risk":.1,"reticle":.25},
      "DEMAND_SURGE":{"outage":.15,"demand":.95*mag,"amhs":.45*mag,"yield_risk":.1,"reticle":.15},
      "YIELD_EXCURSION":{"outage":.1,"demand":.15,"amhs":.1,"yield_risk":.95*mag,"reticle":.1},
      "AMHS_DEGRADATION":{"outage":.15,"demand":.25,"amhs":.95*mag,"yield_risk":.1,"reticle":.15},
      "RETICLE_SHORTAGE":{"outage":.2,"demand":.2,"amhs":.15,"yield_risk":.1,"reticle":.95*mag},
    }
    prior=optimize_recovery([vectors.get(scenario,vectors["PHOTO_OUTAGE"])],alpha=.9,risk_aversion=.45)

    candidates=[]
    for action in ACTIONS:
        r=run_coupled_twin(**_apply(action,disrupted))
        candidates.append({"action":action,"loss":round(_loss(r),3),"result":_summary(r)})
    candidates.sort(key=lambda x:(x["loss"],x["action"]))
    chosen=candidates[0]; recovery_summary=chosen["result"]
    shock_summary=_summary(shock)
    return ClosedLoopRecovery(
        scenario,_summary(baseline),shock_summary,prior.action,chosen["action"],recovery_summary,
        round(shock.avg_cycle_time-recovery_summary["avg_cycle_time"],3),
        shock.queue_time_breaches-recovery_summary["queue_time_breaches"],
        shock.rework_loops-recovery_summary["rework_loops"],
        shock.scrap_lots-recovery_summary["scrap_lots"],
        candidates,"REVIEW","FAB_SHIFT_SUPERVISOR"
    )
