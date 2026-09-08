from __future__ import annotations

def operational_risk_score(sim:dict)->dict:
    ontime=float(sim.get("on_time_rate",0)); tard=float(sim.get("avg_tardiness",0)); wip=float(sim.get("avg_wip",0))
    maxutil=max(sim.get("utilization",{}).values(),default=0)
    score=min(100.0, 45*(1-ontime)+min(25,tard/20)+min(15,wip/20)+15*maxutil)
    level="low" if score<30 else "moderate" if score<55 else "high" if score<75 else "critical"
    drivers=[]
    if ontime<.8: drivers.append("on_time_delivery")
    if maxutil>.85: drivers.append("bottleneck_utilization")
    if tard>100: drivers.append("tardiness")
    if wip>100: drivers.append("wip")
    return {"score":round(score,2),"level":level,"drivers":drivers}
