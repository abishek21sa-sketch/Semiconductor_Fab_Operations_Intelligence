from __future__ import annotations
import traceback
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from fabops.operations.genealogy import route_catalog
from fabops.operations.master_data import TOOLS
from fabops.operations.maintenance import maintenance_calendar

@dataclass(frozen=True)
class MultiOperationSchedule:
    success:bool; objective:float; assignments:list[dict]; lots:int; operations:int
    queue_breaches:int; reticle_conflicts:int; precedence_violations:int; pm_conflicts:int
    horizon:int; message:str
    def to_dict(self): return asdict(self)

def build_lot_operations(lots:int=4,seed:int=17)->list[dict]:
    routes=route_catalog(); jobs=[]
    for li in range(lots):
        product="P1" if (li+seed)%2 else "P2"; release=float((li*3+seed)%8)
        for op in routes[product][:8]:  # rolling horizon only plans the near-term route window
            jobs.append({"job_id":f"L{li+1:02d}-O{op['sequence']:02d}","lot_id":f"LOT-{li+1:03d}","product":product,
                         "sequence":op["sequence"],"bay":op["bay"],"recipe":op["recipe"],"reticle":op["reticle"],
                         "process_time":float(op["process_time"]),"queue_limit":float(op["queue_time_limit"]),
                         "release":release,"priority":3 if li==0 else 1+(li%2)})
    return jobs


def _earliest_free_slot(intervals:list[tuple[int, int]], ready:int, duration:int, horizon:int) -> int|None:
    """Return the first integer slot not covered by any occupied interval."""
    start=max(0, int(ready))
    for occupied_start, occupied_finish in sorted(intervals):
        if start + duration <= occupied_start:
            return start
        if start < occupied_finish and start + duration > occupied_start:
            start=occupied_finish
        if start + duration > horizon:
            return None
    return start if start + duration <= horizon else None


def _greedy_feasible_schedule(jobs:list[dict], tools:list[dict], pm_windows:dict[str, tuple[int, int]], horizon:int):
    """Build a deterministic feasible schedule when MILP reaches its time limit.

    The exact MILP remains the primary optimizer. This bounded fallback is useful in
    a live fab-control surface: it returns a checked, precedence-safe plan instead
    of turning a solver time budget into an operational outage.
    """
    by_lot={}
    for i, job in enumerate(jobs):
        by_lot.setdefault(job["lot_id"], []).append(i)
    for rows in by_lot.values():
        rows.sort(key=lambda i: jobs[i]["sequence"])

    tool_intervals={tool["tool_id"]:[] for tool in tools}
    for tool_id, window in pm_windows.items():
        if tool_id in tool_intervals:
            tool_intervals[tool_id].append(window)
    reticle_intervals={rid:[] for rid in {j.get("reticle") for j in jobs if j.get("reticle")}}
    scheduled={}
    ready=[]
    for lot_id, indices in by_lot.items():
        first=indices[0]
        ready.append((int(jobs[first].get("release", 0)), -int(jobs[first].get("priority", 0)),
                      int(jobs[first].get("queue_limit", horizon)), lot_id, 0, first))

    while ready:
        # Tight queue-time deadlines first; this is the most important protection
        # for re-entrant routes when several lots become available together.
        ready.sort(key=lambda x:(x[0]+x[2], x[0], x[1], x[3]))
        ready_time, _, queue_limit, lot_id, position, job_index=ready.pop(0)
        job=jobs[job_index]
        duration=max(1, int(np.ceil(float(job["process_time"]))))
        options=[]
        for tool in tools:
            if tool["bay"]!=job["bay"] or job["recipe"] not in tool["recipes"]:
                continue
            start=_earliest_free_slot(tool_intervals[tool["tool_id"]], ready_time, duration, horizon)
            if start is None or start > ready_time + queue_limit:
                continue
            rid=job.get("reticle")
            if rid:
                start=_earliest_free_slot(reticle_intervals[rid], start, duration, horizon)
                if start is None or start > ready_time + queue_limit:
                    continue
                # Reticle movement may push the operation into another tool interval.
                start=_earliest_free_slot(tool_intervals[tool["tool_id"]], start, duration, horizon)
                if start is None or start > ready_time + queue_limit:
                    continue
            options.append((start+duration, start, tool, rid))
        if not options:
            return None
        _, start, tool, rid=sorted(options, key=lambda x:(x[0], x[1], x[2]["tool_id"]))[0]
        finish=start+duration
        assignment={**job,"tool_id":tool["tool_id"],"start":start,"finish":finish,
                    "queue_wait":start-ready_time}
        scheduled[job_index]=assignment
        tool_intervals[tool["tool_id"]].append((start, finish))
        if rid:
            reticle_intervals[rid].append((start, finish))

        indices=by_lot[lot_id]
        if position+1 < len(indices):
            next_index=indices[position+1]
            next_job=jobs[next_index]
            ready.append((finish, -int(next_job.get("priority", 0)),
                          int(next_job.get("queue_limit", horizon)), lot_id, position+1, next_index))

    out=[scheduled[index] for index in sorted(scheduled)]
    out.sort(key=lambda x:(x["lot_id"],x["sequence"]))
    return out

def optimize_multi_operation(jobs:list[dict]|None=None,horizon:int=96,seed:int=17,time_limit:float=12.0)->MultiOperationSchedule:
    jobs=jobs or build_lot_operations(4,seed); tools=[t.to_dict() for t in TOOLS]
    pm=maintenance_calendar(seed,horizon)["calendar"]
    pm_windows={x["tool_id"]:(int(round(x["due_in_h"])),int(round(x["due_in_h"]+x["duration_h"])))
                for x in pm if x["due_in_h"]<horizon}
    by_lot={}
    for i,j in enumerate(jobs): by_lot.setdefault(j["lot_id"],[]).append(i)
    for rows in by_lot.values(): rows.sort(key=lambda i:jobs[i]["sequence"])
    candidates=[]
    # Candidate start times are bounded by release and a conservative route-position earliest time.
    for ji,j in enumerate(jobs):
        pos=next(k for k,i in enumerate(by_lot[j["lot_id"]]) if i==ji)
        route_prefix=sum(float(jobs[i]["process_time"]) for i in by_lot[j["lot_id"]][:pos])
        earliest=int(np.floor(float(j["release"])+route_prefix*.55))
        latest=horizon-int(np.ceil(float(j["process_time"])))
        for ti,t in enumerate(tools):
            if t["bay"]!=j["bay"] or j["recipe"] not in t["recipes"]: continue
            p=max(1,int(np.ceil(float(j["process_time"]))))
            for st in range(max(0,earliest),latest+1):
                fn=st+p
                if t["tool_id"] in pm_windows:
                    a,b=pm_windows[t["tool_id"]]
                    if st<b and fn>a: continue
                cost=.03*st + p + .25*(j["recipe"]!=t["recipes"][0])
                candidates.append((ji,ti,st,fn,cost))
    if not candidates:return MultiOperationSchedule(False,float("inf"),[],len(by_lot),len(jobs),len(jobs),0,0,0,horizon,"no candidates")
    n=len(candidates); c=np.array([x[4] for x in candidates],float); rows=[]; lo=[]; hi=[]
    # exactly one assignment
    for ji in range(len(jobs)):
        row=np.zeros(n)
        for k,x in enumerate(candidates):
            if x[0]==ji: row[k]=1
        if row.sum()==0:return MultiOperationSchedule(False,float("inf"),[],len(by_lot),len(jobs),1,0,0,0,horizon,f"no candidate for {jobs[ji]['job_id']}")
        rows.append(row); lo.append(1); hi.append(1)
    # tool non-overlap
    for ti,_ in enumerate(tools):
        for tau in range(horizon):
            row=np.zeros(n)
            for k,x in enumerate(candidates):
                if x[1]==ti and x[2]<=tau<x[3]: row[k]=1
            if row.sum(): rows.append(row); lo.append(-np.inf); hi.append(1)
    # reticle capacity
    for rid in sorted({j["reticle"] for j in jobs if j.get("reticle")}):
        for tau in range(horizon):
            row=np.zeros(n)
            for k,x in enumerate(candidates):
                if jobs[x[0]].get("reticle")==rid and x[2]<=tau<x[3]: row[k]=1
            if row.sum(): rows.append(row); lo.append(-np.inf); hi.append(1)
    # precedence + queue-time: start(next)-finish(prev) in [0, queue_limit(next)]
    for lid,idxs in by_lot.items():
        for a,b in zip(idxs[:-1],idxs[1:]):
            row=np.zeros(n)
            for k,x in enumerate(candidates):
                if x[0]==b: row[k]+=x[2]
                if x[0]==a: row[k]-=x[3]
            rows.append(row); lo.append(0); hi.append(float(jobs[b]["queue_limit"]))
    try:
        res=milp(c,integrality=np.ones(n),bounds=Bounds(np.zeros(n),np.ones(n)),
                 constraints=[LinearConstraint(np.vstack(rows),np.array(lo),np.array(hi))],
                 options={"time_limit":time_limit})
        solver_message=str(res.message)
    except Exception as exc:
        # HiGHS may fail before returning a result when a large sparse model
        # cannot be allocated. Treat that as a solver-status event so the
        # constraint-checked deterministic fallback still protects the API.
        # Print the traceback (not just the message) so solver failures are
        # diagnosable from server logs, not only from the returned message.
        traceback.print_exc()
        res=None
        solver_message=f"solver exception: {type(exc).__name__}: {exc}"
    if res is None or not res.success:
        # HiGHS can spend the complete time budget proving optimality because
        # interchangeable tools generate many equivalent integer solutions. Keep
        # the exact solver as the preferred path, then fall back to a bounded,
        # constraint-checked plan for operational continuity.
        fallback=_greedy_feasible_schedule(jobs,tools,pm_windows,horizon)
        if fallback is None:
            return MultiOperationSchedule(False,float("inf"),[],len(by_lot),len(jobs),0,0,0,0,horizon,solver_message)
        out=fallback
        qbreach=0; precedence=0
        for lid in by_lot:
            rr=[x for x in out if x["lot_id"]==lid]
            for a,b in zip(rr[:-1],rr[1:]):
                wait=b["start"]-a["finish"]
                qbreach+=wait>b["queue_limit"]+1e-9
                precedence+=wait<0
        ret_conf=0
        for rid in sorted({x.get("reticle") for x in out if x.get("reticle")}):
            rr=sorted([x for x in out if x.get("reticle")==rid],key=lambda x:x["start"])
            ret_conf+=sum(rr[i]["start"]<rr[i-1]["finish"] for i in range(1,len(rr)))
        pm_conf=0
        for x in out:
            if x["tool_id"] in pm_windows:
                a,b=pm_windows[x["tool_id"]]
                pm_conf+=x["start"]<b and x["finish"]>a
        if qbreach or precedence or ret_conf or pm_conf:
            return MultiOperationSchedule(False,float("inf"),[],len(by_lot),len(jobs),qbreach,ret_conf,precedence,pm_conf,horizon,"fallback constraint check failed")
        objective=round(sum(float(x["finish"]-x["start"])+.03*float(x["start"]) for x in out),4)
        return MultiOperationSchedule(True,objective,out,len(by_lot),len(out),0,0,0,0,horizon,
                                     f"FALLBACK_FEASIBLE_AFTER_SOLVER_STATUS: {solver_message}")
    out=[]
    for k,v in enumerate(res.x):
        if v>.5:
            ji,ti,st,fn,_=candidates[k]; j=jobs[ji]; t=tools[ti]
            out.append({**j,"tool_id":t["tool_id"],"start":st,"finish":fn})
    out.sort(key=lambda x:(x["lot_id"],x["sequence"]))
    qbreach=0; precedence=0
    for lid in by_lot:
        rr=[x for x in out if x["lot_id"]==lid]
        for a,b in zip(rr[:-1],rr[1:]):
            wait=b["start"]-a["finish"]; b["queue_wait"]=wait
            qbreach+=wait>b["queue_limit"]+1e-9; precedence+=wait<0
    ret_conf=0
    for rid in sorted({x.get("reticle") for x in out if x.get("reticle")}):
        rr=sorted([x for x in out if x.get("reticle")==rid],key=lambda x:x["start"])
        ret_conf+=sum(rr[i]["start"]<rr[i-1]["finish"] for i in range(1,len(rr)))
    pm_conf=0
    for x in out:
        if x["tool_id"] in pm_windows:
            a,b=pm_windows[x["tool_id"]]; pm_conf+=x["start"]<b and x["finish"]>a
    return MultiOperationSchedule(True,round(float(res.fun),4),out,len(by_lot),len(out),qbreach,ret_conf,precedence,pm_conf,horizon,str(res.message))
