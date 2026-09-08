
from dataclasses import dataclass
@dataclass
class FabRisk:
    score: float
    level: str
    drivers: list

def score_lot(queue_pressure, yield_risk, equipment_risk, delivery_risk):
    score=0.25*queue_pressure+0.30*yield_risk+0.25*equipment_risk+0.20*delivery_risk
    level="HIGH" if score>=70 else ("MEDIUM" if score>=40 else "LOW")
    drivers=[]
    for n,v in [("queue_pressure",queue_pressure),("yield_risk",yield_risk),("equipment_risk",equipment_risk),("delivery_risk",delivery_risk)]:
        drivers.append({"factor":n,"impact":round(v,2)})
    drivers=sorted(drivers,key=lambda x:x["impact"],reverse=True)
    return FabRisk(round(score,2),level,drivers)
