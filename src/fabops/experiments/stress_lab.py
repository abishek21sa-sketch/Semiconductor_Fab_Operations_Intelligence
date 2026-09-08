from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import mean
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator

@dataclass(frozen=True)
class StressResult:
    scenario:str; baseline:dict; stressed:dict; delta:dict; severity:str; recommendations:list[str]
    def to_dict(self): return asdict(self)

def run_stress_mission(kind:str="PHOTO_OUTAGE",magnitude:float=.25,seed:int=31,lots:int=80) -> StressResult:
    kind=kind.upper(); mag=max(0,min(float(magnitude),1))
    base=FabSimulator(build_minifab_config(),seed=seed,failure_rate=.015,repair_time=8).run(generate_lots(lots,seed,5.5),"CR").to_dict()
    failure=.015; repair=8; inter=5.5; rule="CR"
    if kind in {"PHOTO_OUTAGE","TOOL_OUTAGE"}: failure=.02+.16*mag; repair=8+28*mag
    elif kind=="DEMAND_SURGE": inter=max(1.8,5.5*(1-.55*mag))
    elif kind=="AMHS_DEGRADATION": failure=.015+.05*mag; repair=8+12*mag
    elif kind=="YIELD_EXCURSION": failure=.02+.08*mag; repair=8+10*mag
    elif kind=="HOT_LOT_SURGE": rule="PRIORITY"; inter=max(2.2,5.5*(1-.35*mag))
    stressed=FabSimulator(build_minifab_config(),seed=seed,failure_rate=failure,repair_time=repair).run(generate_lots(lots,seed,inter),rule).to_dict()
    keys=("avg_cycle_time","p95_cycle_time","avg_tardiness","on_time_rate","avg_wip")
    delta={k:round(float(stressed[k])-float(base[k]),4) for k in keys}
    score=max(0,delta["avg_cycle_time"])/max(base["avg_cycle_time"],1)+max(0,delta["avg_tardiness"])/max(base["avg_tardiness"],1)+max(0,-delta["on_time_rate"])
    severity="CRITICAL" if score>.55 else "HIGH" if score>.25 else "MODERATE" if score>.08 else "LOW"
    rec=["Re-run RARE-FAB release plan with stressed capacity envelope","Protect bottleneck qualification coverage and defer non-critical setups"]
    if kind=="DEMAND_SURGE": rec.append("Tighten CONWIP release limits until WIP operating point stabilizes")
    if "OUTAGE" in kind: rec.append("Move eligible work to qualified alternates and exploit PM opportunity on blocked upstream tools")
    return StressResult(kind,{k:base[k] for k in keys},{k:stressed[k] for k in keys},delta,severity,rec)
