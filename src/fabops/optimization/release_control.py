from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

@dataclass(frozen=True)
class ReleasePlan:
    success:bool
    selected_lots:list[str]
    total_weight:float
    total_load:dict[str,float]
    message:str
    def to_dict(self): return asdict(self)

def optimize_release(lots:list[dict], capacity:dict[str,float]) -> ReleasePlan:
    """Binary CONWIP-style release control under aggregate tool-group workload caps."""
    if not lots: return ReleasePlan(True,[],0.0,{g:0.0 for g in capacity},"nothing to release")
    groups=sorted(capacity); n=len(lots)
    c=np.array([-float(l.get("weight",1.0)) for l in lots])
    A=np.zeros((len(groups),n))
    for gi,g in enumerate(groups):
        for i,l in enumerate(lots): A[gi,i]=float(l.get("workload",{}).get(g,0.0))
    cons=LinearConstraint(A,-np.inf*np.ones(len(groups)),np.array([capacity[g] for g in groups],float))
    res=milp(c,integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),constraints=[cons],options={"time_limit":5})
    if not res.success: return ReleasePlan(False,[],0.0,{},res.message)
    chosen=[lots[i]["lot_id"] for i,x in enumerate(res.x) if x>.5]
    load={g:round(sum(float(l.get("workload",{}).get(g,0)) for l,x in zip(lots,res.x) if x>.5),3) for g in groups}
    return ReleasePlan(True,chosen,round(-float(res.fun),3),load,res.message)
