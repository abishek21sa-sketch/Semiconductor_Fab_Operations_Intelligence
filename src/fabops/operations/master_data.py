from __future__ import annotations
from dataclasses import dataclass, asdict
from math import sin
from typing import Iterable

BAY_SEQUENCE=("PHOTO","ETCH","DIFF","CLEAN","CMP","MET","IMPLANT","INSPECT")

@dataclass(frozen=True)
class ToolMaster:
    tool_id:str; bay:str; family:str; recipes:tuple[str,...]; chambers:int=1; batch_capacity:int=1
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class Reticle:
    reticle_id:str; product:str; layer:str; qualified_tools:tuple[str,...]; status:str="AVAILABLE"
    def to_dict(self): return asdict(self)

TOOLS=(
    ToolMaster("PHOTO-01","PHOTO","SCANNER",("L1","L2","L3")), ToolMaster("PHOTO-02","PHOTO","SCANNER",("L1","L2","L3")),
    ToolMaster("PHOTO-03","PHOTO","SCANNER",("L2","L3","L4")), ToolMaster("TRACK-01","PHOTO","TRACK",("COAT","DEV"),2),
    ToolMaster("ETCH-01","ETCH","PLASMA",("E1","E2"),2), ToolMaster("ETCH-02","ETCH","PLASMA",("E1","E3"),2),
    ToolMaster("ETCH-03","ETCH","PLASMA",("E2","E3"),2), ToolMaster("DIFF-01","DIFF","FURNACE",("D1","D2"),1,6),
    ToolMaster("DIFF-02","DIFF","FURNACE",("D1","D2"),1,6), ToolMaster("CLEAN-01","CLEAN","WET",("C1","C2"),1,4),
    ToolMaster("CLEAN-02","CLEAN","WET",("C1","C2"),1,4), ToolMaster("CMP-01","CMP","POLISHER",("P1","P2")),
    ToolMaster("CMP-02","CMP","POLISHER",("P1","P2")), ToolMaster("MET-01","MET","PVD",("M1","M2"),3),
    ToolMaster("MET-02","MET","PVD",("M1","M2"),3), ToolMaster("IMPL-01","IMPLANT","IMPLANTER",("I1","I2")),
    ToolMaster("IMPL-02","IMPLANT","IMPLANTER",("I1","I2")), ToolMaster("INSP-01","INSPECT","METROLOGY",("CD","DEFECT")),
    ToolMaster("INSP-02","INSPECT","METROLOGY",("CD","DEFECT")),
)
RETICLES=(
    Reticle("R-P1-L1","P1","L1",("PHOTO-01","PHOTO-02")), Reticle("R-P1-L2","P1","L2",("PHOTO-01","PHOTO-02","PHOTO-03")),
    Reticle("R-P2-L1","P2","L1",("PHOTO-01","PHOTO-02")), Reticle("R-P2-L3","P2","L3",("PHOTO-02","PHOTO-03")),
)

def tool_master() -> list[dict]: return [t.to_dict() for t in TOOLS]
def reticle_master() -> list[dict]: return [r.to_dict() for r in RETICLES]

def bay_capacity() -> dict[str,int]:
    return {b:sum(max(1,t.batch_capacity) for t in TOOLS if t.bay==b) for b in BAY_SEQUENCE}

def synthetic_tool_state(seed:int=17) -> list[dict]:
    rows=[]
    for i,t in enumerate(TOOLS):
        utilization=max(.18,min(.98,.58+.24*sin((i+seed)*.73)+(0.12 if t.bay in {"PHOTO","ETCH"} else 0)))
        pm=max(0,min(1,.18+.43*((i*7+seed)%11)/10 + (.25 if t.tool_id=="PHOTO-03" else 0)))
        status="DOWN" if (i+seed)%29==0 else ("PM_DUE" if pm>.72 else ("BUSY" if utilization>.62 else "IDLE"))
        rows.append({**t.to_dict(),"status":status,"utilization":round(utilization,4),"pm_urgency":round(pm,4),
                     "setup_family":t.recipes[(i+seed)%len(t.recipes)],"availability":round(1-.11*pm-(.08 if status=="DOWN" else 0),4),
                     "queue":int(round(utilization*9+(3 if t.bay=="PHOTO" else 0)))})
    return rows
