from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from fabops.operations.master_data import TOOLS
from fabops.operations.maintenance import maintenance_calendar

@dataclass(frozen=True)
class IntegratedSchedule:
    success:bool; objective:float; assignments:list[dict]; queue_breaches:int; reticle_conflicts:int
    pm_avoided:int; horizon:int; runtime_message:str
    def to_dict(self): return asdict(self)

def _tool_dicts():
    return [t.to_dict() for t in TOOLS]

def demo_integrated_jobs(seed:int=17,count:int=12)->list[dict]:
    recipes={"PHOTO":["L1","L2","L3"],"ETCH":["E1","E2","E3"],"DIFF":["D1","D2"],"CLEAN":["C1","C2"],
             "CMP":["P1","P2"],"MET":["M1","M2"],"IMPLANT":["I1","I2"],"INSPECT":["CD","DEFECT"]}
    bays=list(recipes)
    jobs=[]
    for i in range(count):
        bay=bays[(i+seed)%len(bays)]; rs=recipes[bay]; recipe=rs[(i*3+seed)%len(rs)]
        ready=(i*2+seed)%18; qlim=8+((i+seed)%5)*3; proc=2+((i*5+seed)%7)
        ret=None
        if bay=="PHOTO":
            ret="R-P1-L1" if recipe=="L1" else ("R-P1-L2" if recipe in {"L2","L3"} else None)
        jobs.append({"job_id":f"OP-{i+1:03d}","lot_id":f"LOT-{i+1:03d}","bay":bay,"recipe":recipe,
                     "ready_time":float(ready),"queue_limit":float(qlim),"process_time":float(proc),
                     "due":float(ready+qlim+proc+6),"priority":3 if i%7==0 else 1+(i%2),"reticle":ret})
    return jobs

def optimize_integrated_schedule(jobs:list[dict]|None=None, horizon:int=48, seed:int=17, time_limit:float=8.0)->IntegratedSchedule:
    jobs=jobs or demo_integrated_jobs(seed,12); tools=_tool_dicts(); pm=maintenance_calendar(seed,horizon)["calendar"]
    pm_windows={x["tool_id"]:(int(max(0,round(x["due_in_h"]))),int(max(0,round(x["due_in_h"]+x["duration_h"]))))
                for x in pm if x["due_in_h"]<horizon}
    candidates=[]
    for ji,j in enumerate(jobs):
        latest=int(min(horizon-float(j["process_time"]),float(j["ready_time"])+float(j["queue_limit"])))
        earliest=int(max(0,np.ceil(float(j["ready_time"]))))
        for ti,t in enumerate(tools):
            if t["bay"]!=j["bay"] or j["recipe"] not in t["recipes"]: continue
            p=max(1,int(np.ceil(float(j["process_time"]))))
            for st in range(earliest,max(earliest,latest)+1):
                fn=st+p
                if fn>horizon: continue
                if t["tool_id"] in pm_windows:
                    a,b=pm_windows[t["tool_id"]]
                    if st < b and fn > a: continue
                tard=max(0,fn-float(j["due"]))
                queue=max(0,st-float(j["ready_time"]))
                setup_pen=0.35 if j["recipe"]!=t["recipes"][0] else 0
                cost=p + 3*tard*float(j["priority"]) + .35*queue + setup_pen
                candidates.append((ji,ti,st,fn,cost,p))
    if not jobs or not candidates:
        return IntegratedSchedule(False,float("inf"),[],len(jobs),0,0,horizon,"no feasible candidates")
    n=len(candidates); c=np.array([x[4] for x in candidates],float); rows=[]; lo=[]; hi=[]
    # exactly one start for each operation
    for ji in range(len(jobs)):
        row=np.zeros(n)
        for k,x in enumerate(candidates):
            if x[0]==ji: row[k]=1
        if row.sum()==0:
            return IntegratedSchedule(False,float("inf"),[],1,0,0,horizon,f"no feasible queue-time assignment for {jobs[ji]['job_id']}")
        rows.append(row); lo.append(1); hi.append(1)
    # each chamber/tool handles at most one operation at a time
    for ti,_ in enumerate(tools):
        for tau in range(horizon):
            row=np.zeros(n)
            for k,x in enumerate(candidates):
                if x[1]==ti and x[2]<=tau<x[3]: row[k]=1
            if row.sum(): rows.append(row); lo.append(-np.inf); hi.append(1)
    # each reticle handles at most one PHOTO lot at a time
    rets=sorted({j.get("reticle") for j in jobs if j.get("reticle")})
    for rid in rets:
        for tau in range(horizon):
            row=np.zeros(n)
            for k,x in enumerate(candidates):
                j=jobs[x[0]]
                if j.get("reticle")==rid and x[2]<=tau<x[3]: row[k]=1
            if row.sum(): rows.append(row); lo.append(-np.inf); hi.append(1)
    res=milp(c,integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),
             constraints=[LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi))],
             options={"time_limit":time_limit})
    if not res.success:
        return IntegratedSchedule(False,float("inf"),[],len(jobs),0,0,horizon,str(res.message))
    out=[]
    for k,v in enumerate(res.x):
        if v>.5:
            ji,ti,st,fn,_,p=candidates[k]; j=jobs[ji]; t=tools[ti]
            qwait=st-float(j["ready_time"]); breach=qwait>float(j["queue_limit"])+1e-9
            out.append({"job_id":j["job_id"],"lot_id":j["lot_id"],"bay":j["bay"],"recipe":j["recipe"],
                        "tool_id":t["tool_id"],"reticle":j.get("reticle"),"start":st,"finish":fn,
                        "queue_wait":round(qwait,2),"queue_limit":j["queue_limit"],"queue_breach":breach,
                        "due":j["due"],"tardiness":round(max(0,fn-j["due"]),2)})
    # reticle constraints are explicit; count should be zero.
    ret_conf=0
    for rid in rets:
        rr=sorted([x for x in out if x["reticle"]==rid],key=lambda x:x["start"])
        ret_conf+=sum(rr[i]["start"]<rr[i-1]["finish"] for i in range(1,len(rr)))
    pm_avoided=sum(1 for x in out if x["tool_id"] in pm_windows)
    return IntegratedSchedule(True,round(float(res.fun),4),sorted(out,key=lambda x:(x["start"],x["tool_id"])),
                              sum(x["queue_breach"] for x in out),ret_conf,pm_avoided,horizon,str(res.message))
