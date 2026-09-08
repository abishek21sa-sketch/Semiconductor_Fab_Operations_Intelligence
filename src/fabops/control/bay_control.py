from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class BayRisk:
    bay:str; wip:float; utilization:float; queue_age:float; amhs_delay:float; energy_stress:float; maintenance_risk:float; score:float; state:str
    def to_dict(self): return asdict(self)

def bay_risk_heatmap(bays:list[dict]) -> list[dict]:
    out=[]
    for b in bays:
        w=min(float(b.get("wip",0))/max(float(b.get("wip_limit",1)),1e-9),1.5)
        u=min(float(b.get("utilization",0)),1.5); q=min(float(b.get("queue_age",0))/max(float(b.get("queue_limit",1)),1e-9),1.5)
        a=min(float(b.get("amhs_delay",0))/max(float(b.get("amhs_limit",1)),1e-9),1.5); e=min(float(b.get("energy_stress",0)),1.5); m=min(float(b.get("maintenance_risk",0)),1.5)
        score=.25*w+.25*u+.2*q+.12*a+.08*e+.1*m
        state="NOMINAL" if score<.65 else ("WATCH" if score<.9 else "CONSTRAINED")
        out.append(BayRisk(str(b.get("bay","UNKNOWN")),float(b.get("wip",0)),u,float(b.get("queue_age",0)),float(b.get("amhs_delay",0)),e,m,round(score,4),state).to_dict())
    return sorted(out,key=lambda x:x["score"],reverse=True)
