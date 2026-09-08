from __future__ import annotations
from dataclasses import dataclass, asdict
from math import sin
from fabops.operations.master_data import TOOLS, RETICLES

# A deliberately richer reference route: re-entrant PHOTO/ETCH/INSPECT visits,
# queue-time clocks, reticle dependencies and batch-capable thermal/wet steps.
ROUTES = {
 "P1":[
  ("PHOTO","L1","R-P1-L1",7.5,10.0),("ETCH","E1",None,8.0,16.0),("INSPECT","CD",None,3.0,8.0),
  ("CLEAN","C1",None,5.0,12.0),("DIFF","D1",None,12.0,20.0),("PHOTO","L2","R-P1-L2",8.0,10.0),
  ("ETCH","E2",None,9.0,14.0),("CMP","P1",None,7.0,12.0),("INSPECT","DEFECT",None,4.0,8.0),
  ("MET","M1",None,10.0,16.0),("PHOTO","L3","R-P1-L2",8.5,10.0),("ETCH","E1",None,8.0,14.0),
  ("IMPLANT","I1",None,7.0,12.0),("INSPECT","CD",None,3.0,8.0)
 ],
 "P2":[
  ("PHOTO","L1","R-P2-L1",8.0,10.0),("ETCH","E3",None,9.0,15.0),("CLEAN","C2",None,5.0,12.0),
  ("DIFF","D2",None,13.0,22.0),("INSPECT","CD",None,3.0,8.0),("PHOTO","L3","R-P2-L3",9.0,10.0),
  ("ETCH","E2",None,9.0,14.0),("CMP","P2",None,7.5,12.0),("MET","M2",None,11.0,16.0),
  ("INSPECT","DEFECT",None,4.0,8.0),("PHOTO","L3","R-P2-L3",9.0,10.0),("ETCH","E3",None,9.0,14.0),
  ("IMPLANT","I2",None,7.5,12.0),("INSPECT","CD",None,3.0,8.0)
 ]
}

def route_catalog() -> dict:
    out={}
    for product,ops in ROUTES.items():
        out[product]=[{"sequence":i+1,"bay":b,"recipe":r,"reticle":ret,"process_time":p,"queue_time_limit":q,
                       "reentrant_visit":sum(1 for x in ops[:i] if x[0]==b)+1} for i,(b,r,ret,p,q) in enumerate(ops)]
    return out

def _qualified_tools(bay, recipe):
    return [t.tool_id for t in TOOLS if t.bay==bay and recipe in t.recipes]

def lot_genealogy(lot_id:str="LOT-017", seed:int=17) -> dict:
    digits="".join(c for c in lot_id if c.isdigit())
    idx=int(digits or 17)
    product="P1" if idx%2 else "P2"; route=route_catalog()[product]
    current=(idx*3+seed)%len(route)
    history=[]; clock=idx*.7
    for op in route:
        qage=round(1.2+((idx*op["sequence"]+seed)%17)*.62,2)
        state="COMPLETE" if op["sequence"]<=current else ("CURRENT" if op["sequence"]==current+1 else "PLANNED")
        start=round(clock,2) if state=="COMPLETE" else None
        finish=round(clock+op["process_time"],2) if state=="COMPLETE" else None
        if state=="COMPLETE": clock=finish+qage*.25
        breach=qage>op["queue_time_limit"]*.85 and state in {"CURRENT","PLANNED"}
        history.append({**op,"state":state,"queue_age":qage,"queue_clock_fraction":round(qage/op["queue_time_limit"],3),
                        "queue_time_risk":"BREACH_RISK" if breach else "OK","start":start,"finish":finish,
                        "qualified_tools":_qualified_tools(op["bay"],op["recipe"])})
    return {"lot_id":lot_id,"product":product,"priority":3 if idx%7==0 else 1+(idx%2),
            "wafer_count":25,"current_sequence":current+1,"route_length":len(route),"operations":history,
            "reentrant_bays":["PHOTO","ETCH","INSPECT"],"genealogy_state":"ACTIVE",
            "claim_boundary":"Reference virtual lot genealogy; not MES wafer history."}

def queue_time_watch(seed:int=17,count:int=28) -> list[dict]:
    rows=[]
    for i in range(count):
        lid=f"LOT-{i+1:03d}"; g=lot_genealogy(lid,seed); cur=g["operations"][min(g["current_sequence"]-1,len(g["operations"])-1)]
        frac=cur["queue_clock_fraction"]
        rows.append({"lot_id":lid,"product":g["product"],"bay":cur["bay"],"recipe":cur["recipe"],
                     "queue_age":cur["queue_age"],"limit":cur["queue_time_limit"],"fraction":frac,
                     "state":"BREACH" if frac>=1 else "AT_RISK" if frac>=.75 else "SAFE",
                     "reticle":cur["reticle"],"qualified_tools":cur["qualified_tools"]})
    return sorted(rows,key=lambda x:x["fraction"],reverse=True)
