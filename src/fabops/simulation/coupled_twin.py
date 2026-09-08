from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict
import heapq, random, math
from fabops.operations.genealogy import route_catalog
from fabops.operations.master_data import TOOLS, RETICLES
from fabops.operations.maintenance import maintenance_calendar

@dataclass(frozen=True)
class CoupledTwinResult:
    seed:int; lots:int; completed:int; makespan:float; avg_cycle_time:float; p95_cycle_time:float
    avg_queue_time:float; queue_time_breaches:int; rework_loops:int; scrap_lots:int
    reticle_wait:float; batch_runs:int; mean_batch_fill:float; pm_interruptions:int
    tool_failures:int; on_time_rate:float; event_count:int; bay_wip_peak:dict
    completed_lots:list[dict]; event_log:list[dict]
    def to_dict(self): return asdict(self)

def _percentile(xs,p):
    if not xs:return 0.0
    ys=sorted(xs); k=(len(ys)-1)*p/100; a=int(math.floor(k)); b=int(math.ceil(k))
    return ys[a] if a==b else ys[a]*(b-k)+ys[b]*(k-a)

def _tools():
    return {t.tool_id:t for t in TOOLS}

def run_coupled_twin(lots:int=48,seed:int=17,interarrival:float=3.8,failure_rate:float=.015,
                     rework_sensitivity:float=.22,horizon:float=1500.0)->CoupledTwinResult:
    rng=random.Random(seed); routes=route_catalog(); tools=_tools()
    tool_state={tid:{"available":0.0,"recipe":None,"failures":0} for tid in tools}
    pm=maintenance_calendar(seed,168)["calendar"]
    pm_by_tool={x["tool_id"]:(x["due_in_h"],x["due_in_h"]+x["duration_h"]) for x in pm}
    ret_available={r.reticle_id:0.0 for r in RETICLES}
    batch_bays={"DIFF":6,"CLEAN":4}
    batch_buffers=defaultdict(list)
    queues=defaultdict(list); ev=[]; seq=0; log=[]; completed=[]; peak=defaultdict(int)
    ret_wait_total=0.0; batch_runs=0; batch_fill=[]; pm_hits=0; failures=0; breaches=0; reworks=0; scrap=0
    lot_state={}
    def push(t,kind,payload):
        nonlocal seq
        seq+=1; heapq.heappush(ev,(t,seq,kind,payload))
    t=0.0
    for i in range(lots):
        t += rng.expovariate(1/max(interarrival,.1))
        product="P1" if rng.random()<.55 else "P2"; due=t+(170 if product=="P1" else 185)*rng.uniform(.9,1.25)
        lid=f"V6-{i+1:04d}"
        lot_state[lid]={"lot_id":lid,"product":product,"release":t,"due":due,"seq":0,"queue_enter":t,
                        "queue":0.0,"rework":0,"scrap":False,"history":[]}
        push(t,"release",lid)

    def qualified(bay,recipe):
        return [tid for tid,x in tools.items() if x.bay==bay and recipe in x.recipes]

    def schedule_single(lid,now):
        nonlocal ret_wait_total,pm_hits,failures
        l=lot_state[lid]; op=routes[l["product"]][l["seq"]]; bay,recipe=op["bay"],op["recipe"]
        candidates=qualified(bay,recipe)
        if not candidates:return False
        # choose earliest eligible tool, including PM blackout and recipe-change penalty
        choices=[]
        for tid in candidates:
            st=max(now,tool_state[tid]["available"]); setup=0 if tool_state[tid]["recipe"] in (None,recipe) else 1.5
            if tid in pm_by_tool:
                a,b=pm_by_tool[tid]
                if st < b and st+op["process_time"]+setup > a:
                    st=b; pm_pen=1
                else: pm_pen=0
            else: pm_pen=0
            choices.append((st+setup,tid,setup,pm_pen))
        st,tid,setup,pm_pen=min(choices)
        if pm_pen: pm_hits+=1
        # shared reticle becomes a real resource.
        ret=op.get("reticle")
        if ret:
            before=st; st=max(st,ret_available.get(ret,0.0)); ret_wait_total+=max(0,st-before)
        qwait=max(0,st-l["queue_enter"]); l["queue"]+=qwait
        dur=float(op["process_time"])+setup
        failed=rng.random()<failure_rate
        if failed:
            repair=5+rng.random()*12; dur+=repair; failures+=1; tool_state[tid]["failures"]+=1
        fn=st+dur; tool_state[tid]["available"]=fn; tool_state[tid]["recipe"]=recipe
        if ret: ret_available[ret]=fn
        l["history"].append({"sequence":op["sequence"],"bay":bay,"recipe":recipe,"tool_id":tid,"start":round(st,3),
                             "finish":round(fn,3),"queue_wait":round(qwait,3),"queue_limit":op["queue_time_limit"],
                             "reticle":ret,"setup":setup,"failure":failed})
        log.append({"time":round(st,3),"event":"operation_start","lot_id":lid,"bay":bay,"tool_id":tid,"recipe":recipe,"reticle":ret})
        push(fn,"finish",(lid,qwait))
        return True

    def release_to_step(lid,now):
        l=lot_state[lid]; op=routes[l["product"]][l["seq"]]; l["queue_enter"]=now
        if op["bay"] in batch_bays:
            key=(op["bay"],op["recipe"]); batch_buffers[key].append((lid,now))
            cap=batch_bays[op["bay"]]
            # full batch launches immediately; otherwise timeout launches after 4h.
            if len(batch_buffers[key])>=cap:
                push(now,"batch_launch",key)
            elif len(batch_buffers[key])==1:
                push(now+4.0,"batch_timeout",key)
        else:
            queues[op["bay"]].append(lid); peak[op["bay"]]=max(peak[op["bay"]],len(queues[op["bay"]]))
            push(now,"dispatch",op["bay"])

    while ev:
        now,_,kind,payload=heapq.heappop(ev)
        if now>horizon:break
        if kind=="release":
            lid=payload; log.append({"time":round(now,3),"event":"lot_release","lot_id":lid}); release_to_step(lid,now)
        elif kind=="dispatch":
            bay=payload
            if not queues[bay]:continue
            # critical ratio proxy: smallest due-minus-now first.
            queues[bay].sort(key=lambda lid:(lot_state[lid]["due"]-now,-(3 if int(lid[-4:])%7==0 else 1)))
            remaining=[]
            for lid in list(queues[bay]):
                if not schedule_single(lid,now): remaining.append(lid)
            queues[bay]=remaining
        elif kind in {"batch_launch","batch_timeout"}:
            key=payload; buf=batch_buffers[key]
            if not buf:continue
            bay,recipe=key; cap=batch_bays[bay]
            take=buf[:cap]; batch_buffers[key]=buf[cap:]
            lids=[x[0] for x in take]; ready=max(x[1] for x in take); qwaits={lid:max(0,ready-r) for lid,r in take}
            candidates=qualified(bay,recipe)
            if not candidates:
                for lid,_ in take: queues[bay].append(lid)
                continue
            choices=[]
            for tid in candidates:
                st=max(ready,tool_state[tid]["available"])
                if tid in pm_by_tool:
                    a,b=pm_by_tool[tid]
                    if st<b and st+routes[lot_state[lids[0]]["product"]][lot_state[lids[0]]["seq"]]["process_time"]>a: st=b
                choices.append((st,tid))
            st,tid=min(choices)
            qwaits={lid:max(0,st-r) for lid,r in take}
            p=max(routes[lot_state[lid]["product"]][lot_state[lid]["seq"]]["process_time"] for lid in lids)
            failed=rng.random()<failure_rate
            if failed: p+=5+rng.random()*12; failures+=1; tool_state[tid]["failures"]+=1
            fn=st+p; tool_state[tid]["available"]=fn; tool_state[tid]["recipe"]=recipe
            batch_runs+=1; batch_fill.append(len(lids)/cap)
            for lid in lids:
                l=lot_state[lid]; l["queue"]+=qwaits[lid]
                op=routes[l["product"]][l["seq"]]
                l["history"].append({"sequence":op["sequence"],"bay":bay,"recipe":recipe,"tool_id":tid,"batch":True,
                                     "batch_size":len(lids),"start":round(st,3),"finish":round(fn,3),
                                     "queue_wait":round(qwaits[lid],3),"queue_limit":op["queue_time_limit"],"failure":failed})
                log.append({"time":round(st,3),"event":"batch_start","lot_id":lid,"bay":bay,"tool_id":tid,"batch_size":len(lids)})
                push(fn,"finish",(lid,qwaits[lid]))
            if batch_buffers[key]: push(fn,"batch_timeout",key)
        elif kind=="finish":
            lid,qwait=payload; l=lot_state[lid]
            if l["scrap"]:continue
            op=routes[l["product"]][l["seq"]]
            frac=qwait/max(op["queue_time_limit"],1e-6)
            breached=frac>1.0
            if breached: breaches+=1
            # queue-time damage can cause rework or scrap; this feeds back into WIP.
            excursion=max(0,min(.95,.06 + max(0,frac-.65)*rework_sensitivity + (0.08 if op["bay"]=="PHOTO" else 0)))
            u=rng.random()
            if u<excursion*.10:
                l["scrap"]=True; scrap+=1
                log.append({"time":round(now,3),"event":"lot_scrap","lot_id":lid,"bay":op["bay"],"queue_fraction":round(frac,3)})
                continue
            if u<excursion and l["rework"]<2 and l["seq"]>=3:
                l["rework"]+=1; reworks+=1
                # return 2 operations upstream, preserving a bounded rework loop.
                l["seq"]=max(0,l["seq"]-2)
                log.append({"time":round(now,3),"event":"rework_route","lot_id":lid,"return_sequence":l["seq"]+1})
                release_to_step(lid,now+1.0); continue
            l["seq"]+=1
            log.append({"time":round(now,3),"event":"operation_finish","lot_id":lid,"sequence":op["sequence"],"queue_breach":breached})
            if l["seq"]>=len(routes[l["product"]]):
                l["completion"]=now; completed.append(lid); log.append({"time":round(now,3),"event":"lot_complete","lot_id":lid})
            else:
                release_to_step(lid,now+.4)
    rec=[]
    for lid in completed:
        l=lot_state[lid]; ct=l["completion"]-l["release"]
        rec.append({"lot_id":lid,"product":l["product"],"cycle_time":round(ct,3),"queue_time":round(l["queue"],3),
                    "due":round(l["due"],3),"completion":round(l["completion"],3),"on_time":l["completion"]<=l["due"],
                    "rework_loops":l["rework"],"operations_executed":len(l["history"])})
    cts=[x["cycle_time"] for x in rec]; qs=[x["queue_time"] for x in rec]
    makespan=max((x["completion"] for x in rec),default=0)
    return CoupledTwinResult(seed,lots,len(rec),round(makespan,3),round(sum(cts)/len(cts),3) if cts else 0,
                             round(_percentile(cts,95),3),round(sum(qs)/len(qs),3) if qs else 0,breaches,reworks,scrap,
                             round(ret_wait_total,3),batch_runs,round(sum(batch_fill)/len(batch_fill),3) if batch_fill else 0,
                             pm_hits,failures,round(sum(x["on_time"] for x in rec)/len(rec),4) if rec else 0,
                             len(log),dict(peak),rec,log)
