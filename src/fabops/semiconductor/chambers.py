from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict
from fabops.operations.master_data import TOOLS, RETICLES

@dataclass(frozen=True)
class ChamberState:
    chamber_id:str; tool_id:str; bay:str; recipe:str|None; status:str; available_at:float
    def to_dict(self): return asdict(self)

def chamber_state(seed:int=17)->list[dict]:
    rows=[]
    for i,t in enumerate(TOOLS):
        n=max(1,int(t.chambers))
        for c in range(n):
            util=((seed+i*7+c*11)%100)/100
            status="DOWN" if (seed+i*13+c*5)%61==0 else ("BUSY" if util>.43 else "IDLE")
            recipe=t.recipes[(seed+i+c)%len(t.recipes)] if status!="DOWN" else None
            rows.append(ChamberState(f"{t.tool_id}-CH{c+1}",t.tool_id,t.bay,recipe,status,round((i+c)%7*1.5,2)).to_dict())
    return rows

def form_batches(lots:list[dict], tools:list[dict]|None=None, max_wait:float=6.0)->dict:
    tools=tools or [t.to_dict() for t in TOOLS]
    batch_tools={t["bay"]:max(1,int(t.get("batch_capacity",1))) for t in tools if int(t.get("batch_capacity",1))>1}
    groups=defaultdict(list)
    for lot in lots:
        bay=lot.get("bay"); recipe=lot.get("recipe")
        if bay in batch_tools: groups[(bay,recipe)].append(lot)
    batches=[]; unbatched=[]
    for (bay,recipe),rows in groups.items():
        rows=sorted(rows,key=lambda x:(float(x.get("ready_time",0)),x.get("lot_id","")))
        cap=batch_tools[bay]
        i=0
        while i<len(rows):
            anchor=float(rows[i].get("ready_time",0)); batch=[rows[i]]; i+=1
            while i<len(rows) and len(batch)<cap and float(rows[i].get("ready_time",0))-anchor<=max_wait:
                batch.append(rows[i]); i+=1
            batches.append({"batch_id":f"{bay}-{recipe}-B{len(batches)+1:03d}","bay":bay,"recipe":recipe,
                            "lot_ids":[x["lot_id"] for x in batch],"size":len(batch),"capacity":cap,
                            "ready_time":round(max(float(x.get("ready_time",0)) for x in batch),2),
                            "fill_rate":round(len(batch)/cap,3)})
    batch_ids={lid for b in batches for lid in b["lot_ids"]}
    unbatched=[x for x in lots if x.get("lot_id") not in batch_ids]
    return {"batches":batches,"unbatched":unbatched,
            "mean_fill_rate":round(sum(b["fill_rate"] for b in batches)/len(batches),3) if batches else 0.0}

def reticle_contention(requests:list[dict], horizon:float=24.0)->dict:
    by=defaultdict(list)
    for r in requests:
        rid=r.get("reticle")
        if rid: by[rid].append(r)
    rows=[]; conflicts=0
    for rid,reqs in by.items():
        reqs=sorted(reqs,key=lambda x:float(x.get("ready_time",0)))
        clock=0.0
        for r in reqs:
            start=max(clock,float(r.get("ready_time",0))); dur=float(r.get("duration",2))
            wait=max(0,start-float(r.get("ready_time",0))); clock=start+dur
            conflict=wait>0; conflicts+=int(conflict)
            rows.append({"reticle":rid,"lot_id":r.get("lot_id"),"start":round(start,2),"finish":round(clock,2),
                         "wait":round(wait,2),"conflict":conflict,"within_horizon":clock<=horizon})
    return {"assignments":rows,"conflicts":conflicts,"reticles_used":len(by),
            "max_wait":round(max((x["wait"] for x in rows),default=0),2)}

def qualification_matrix()->dict:
    matrix={}
    for t in TOOLS:
        matrix[t.tool_id]={"bay":t.bay,"recipes":list(t.recipes),"chambers":t.chambers,"batch_capacity":t.batch_capacity}
    return {"tools":matrix,"reticles":[r.to_dict() for r in RETICLES]}
