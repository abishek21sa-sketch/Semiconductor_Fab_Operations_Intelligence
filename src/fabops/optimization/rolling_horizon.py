from __future__ import annotations
from dataclasses import dataclass, asdict
import time
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

@dataclass(frozen=True)
class RollingSchedule:
    success:bool; objective:float; assignments:list[dict]; tool_load:dict[str,float]; tardy_jobs:int; runtime_s:float; message:str
    def to_dict(self): return asdict(self)

def optimize_rolling_schedule(jobs:list[dict], tools:list[dict], horizon:float=96.0, time_limit:float=8.0) -> RollingSchedule:
    """Bounded parallel-tool assignment MILP with qualification, due-date and setup-family proxies.
    Start times are recovered by deterministic list scheduling after the assignment MILP.
    """
    t0=time.perf_counter(); pairs=[]
    for i,j in enumerate(jobs):
        for k,t in enumerate(tools):
            if j.get("bay")!=t.get("bay"): continue
            if j.get("recipe") not in t.get("recipes",[]): continue
            p=float(j.get("process_time",8)); setup=0 if j.get("setup_family")==t.get("setup_family") else float(j.get("setup_time",2))
            due=float(j.get("due",horizon)); pri=float(j.get("priority",1)); cost=p+setup+max(0,p+setup-due)*pri*4
            pairs.append((i,k,cost,p,setup))
    if not jobs or not pairs: return RollingSchedule(False,float("inf"),[],{},len(jobs),0,"no qualified assignment pairs")
    n=len(pairs); c=np.array([x[2] for x in pairs],float); A=[]; lo=[]; hi=[]
    for i in range(len(jobs)):
        row=np.zeros(n); found=False
        for q,p in enumerate(pairs):
            if p[0]==i: row[q]=1; found=True
        if not found: return RollingSchedule(False,float("inf"),[],{},len(jobs),round(time.perf_counter()-t0,6),f"job {jobs[i].get('job_id',i)} has no qualified tool")
        A.append(row); lo.append(1); hi.append(1)
    for k,t in enumerate(tools):
        row=np.zeros(n)
        for q,p in enumerate(pairs):
            if p[1]==k: row[q]=p[3]+p[4]
        A.append(row); lo.append(-np.inf); hi.append(horizon)
    res=milp(c,integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),constraints=[LinearConstraint(np.vstack(A),lo,hi)],options={"time_limit":time_limit})
    if not res.success: return RollingSchedule(False,float("inf"),[],{},len(jobs),round(time.perf_counter()-t0,6),str(res.message))
    chosen=[]
    for q,v in enumerate(res.x):
        if v>.5:
            i,k,_,p,setup=pairs[q]; chosen.append((jobs[i],tools[k],p,setup))
    # Recover a feasible non-overlapping sequence by tool, EDD/priority.
    out=[]; load={}; tardy=0
    for tool in tools:
        seq=[x for x in chosen if x[1].get("tool_id")==tool.get("tool_id")]
        seq.sort(key=lambda x:(float(x[0].get("due",horizon)),-float(x[0].get("priority",1))))
        clock=0.0
        for j,t,p,setup in seq:
            start=clock; finish=start+p+setup; clock=finish; due=float(j.get("due",horizon)); tard=max(0,finish-due); tardy+=tard>0
            out.append({"job_id":j.get("job_id"),"lot_id":j.get("lot_id"),"tool_id":t.get("tool_id"),"bay":j.get("bay"),"recipe":j.get("recipe"),
                        "start":round(start,2),"finish":round(finish,2),"process_time":p,"setup_time":setup,"due":due,"tardiness":round(tard,2)})
        load[tool.get("tool_id")]=round(clock,2)
    out.sort(key=lambda x:(x["start"],x["tool_id"]))
    return RollingSchedule(True,round(float(res.fun),4),out,load,int(tardy),round(time.perf_counter()-t0,6),str(res.message))
