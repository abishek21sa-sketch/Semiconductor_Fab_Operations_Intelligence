from __future__ import annotations
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class YieldDecision:
    predicted_yield:float; excursion_probability:float; expected_good_wafers:float; rework_load:float; disposition:str
    def to_dict(self): return asdict(self)

def yield_risk(wafer_count:int, defect_density:float, area:float=1.0, process_z:float=0.0, rework_fraction:float=.35) -> YieldDecision:
    base=math.exp(-max(defect_density,0)*max(area,0)); excursion=1/(1+math.exp(-(abs(process_z)-2.5)*2))
    y=max(0,min(1,base*(1-.35*excursion))); good=wafer_count*y; rework=max(0,wafer_count-good)*rework_fraction
    disp="RELEASE" if excursion<.35 else ("ENGINEERING_REVIEW" if excursion<.75 else "HOLD_LOT")
    return YieldDecision(round(y,4),round(excursion,4),round(good,2),round(rework,2),disp)
