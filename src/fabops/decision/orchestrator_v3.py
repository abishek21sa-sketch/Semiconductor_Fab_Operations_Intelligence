from __future__ import annotations
from dataclasses import dataclass, asdict
from fabops.experiments.stress_lab import run_stress_mission
from fabops.operations.control_tower import mission_control

@dataclass(frozen=True)
class DecisionPacket:
    decision_id:str; state:str; severity:str; problem:str; actions:list[dict]; evidence:list[dict]; human_gate:str; claim_boundary:str
    def to_dict(self): return asdict(self)

def orchestrate_decision(scenario:str="PHOTO_OUTAGE",magnitude:float=.25,seed:int=31) -> DecisionPacket:
    stress=run_stress_mission(scenario,magnitude,seed).to_dict(); tower=mission_control(seed,80)
    constrained=[b for b in tower["bays"] if b["state"]!="NOMINAL"]
    actions=[]
    for rank,text in enumerate(stress["recommendations"],1):
        impact=max(0,abs(stress["delta"].get("avg_tardiness",0))/(rank+1))
        actions.append({"rank":rank,"action":text,"expected_tardiness_recovery":round(impact,2),"confidence":"SIMULATION_BACKED" if rank==1 else "ANALYTICAL",
                        "execute":"REQUIRES_APPROVAL"})
    evidence=[{"type":"STRESS_TWIN","metric":"avg_cycle_time_delta","value":stress["delta"]["avg_cycle_time"]},
              {"type":"STRESS_TWIN","metric":"avg_tardiness_delta","value":stress["delta"]["avg_tardiness"]},
              {"type":"FAB_STATE","metric":"constrained_bays","value":[x["bay"] for x in constrained]}]
    return DecisionPacket(f"DEC-{seed}-{scenario}","REVIEW",stress["severity"],f"{scenario} magnitude={magnitude:.2f}",actions,evidence,
                          "FAB_SHIFT_SUPERVISOR","Reference/synthetic decision evidence only; no autonomous execution or site-performance claim.")
