from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class EquipmentRisk:
    tool_id:str; availability:float; pm_urgency:float; setup_pressure:float; qualification_coverage:float; risk_score:float; recommended_action:str
    def to_dict(self): return asdict(self)

def equipment_risk(tool:dict) -> EquipmentRisk:
    mtbf=max(float(tool.get("mtbf",100)),1e-6); mttr=max(float(tool.get("mttr",5)),0); avail=mtbf/(mtbf+mttr)
    hours_to_pm=float(tool.get("hours_to_pm",72)); pm=max(0.0,min(1.0,(24-hours_to_pm)/24))
    setups=float(tool.get("setups_next_shift",0)); setup=min(1.0,setups/8.0)
    q=float(tool.get("qualified_recipe_fraction",1.0)); q=max(0,min(1,q))
    risk=.45*(1-avail)+.25*pm+.15*setup+.15*(1-q)
    action="RUN" if risk<.2 else ("REVIEW_PM_WINDOW" if pm>=max(setup,1-q) else "PROTECT_CAPACITY")
    return EquipmentRisk(str(tool.get("tool_id","UNKNOWN")),round(avail,4),round(pm,4),round(setup,4),round(q,4),round(risk,4),action)
