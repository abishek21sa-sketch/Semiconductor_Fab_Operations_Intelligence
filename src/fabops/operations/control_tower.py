from __future__ import annotations
from collections import defaultdict
from math import ceil
from fabops.operations.master_data import BAY_SEQUENCE, synthetic_tool_state, tool_master, reticle_master
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator


def mission_control(seed:int=17,lots:int=90) -> dict:
    sim=FabSimulator(build_minifab_config(),seed=seed,failure_rate=.025,repair_time=10).run(generate_lots(lots,seed,5.5),"CR")
    tools=synthetic_tool_state(seed)
    by_bay=defaultdict(list)
    for t in tools: by_bay[t["bay"]].append(t)
    bays=[]
    for b in BAY_SEQUENCE:
        ts=by_bay[b]; util=sum(x["utilization"] for x in ts)/max(len(ts),1); q=sum(x["queue"] for x in ts)
        score=.50*util+.025*q+.20*max((x["pm_urgency"] for x in ts),default=0)
        state="CONSTRAINED" if score>.92 else "WATCH" if score>.68 else "NOMINAL"
        bays.append({"bay":b,"utilization":round(util,4),"queue":q,"risk_score":round(score,4),"state":state,
                     "tools":len(ts),"down":sum(x["status"]=="DOWN" for x in ts),"pm_due":sum(x["status"]=="PM_DUE" for x in ts)})
    alerts=[]
    for b in bays:
        if b["state"]!="NOMINAL": alerts.append({"severity":"CRITICAL" if b["state"]=="CONSTRAINED" else "WARNING","asset":b["bay"],"message":f'{b["bay"]} pressure elevated: util {b["utilization"]:.0%}, queue {b["queue"]}'})
    return {"mode":"REFERENCE_REPLAY","kpis":{"wip":round(sim.avg_wip,1),"throughput":sim.throughput,"cycle_time":sim.avg_cycle_time,
            "p95_cycle_time":sim.p95_cycle_time,"on_time_rate":sim.on_time_rate,"tardiness":sim.avg_tardiness},"bays":bays,
            "alerts":alerts[:6],"tool_state":tools,"reticles":reticle_master(),"claim_boundary":"Synthetic/reference operations state; not site telemetry."}


def lot_control(seed:int=17,count:int=36) -> list[dict]:
    lots=generate_lots(count,seed,4.8); route=build_minifab_config().routes
    rows=[]
    for i,l in enumerate(lots):
        ops=route[l.product].operations; idx=(i*3+seed)%len(ops); op=ops[idx]
        progress=idx/len(ops); queue_age=round(1.5+((i*7+seed)%19)*.85,2); slack=round(l.due_time-l.release_time-(idx+1)*8-queue_age,2)
        risk=min(.99,max(.03,.35+(queue_age/30)+(0.18 if l.priority>=3 else 0)-.15*progress))
        rows.append({"lot_id":l.lot_id,"product":l.product,"priority":l.priority,"step":op.step,"bay":("PHOTO" if op.tool_group=="LITHO" else op.tool_group),"recipe":op.recipe,
                     "progress":round(progress,3),"queue_age":queue_age,"due_time":round(l.due_time,2),"slack":slack,"tardiness_risk":round(risk,3),
                     "predicted_finish":round(l.release_time+(idx+1)*8+queue_age+25*(1-progress),2),"hold":"ENGINEERING" if i%23==0 else None,
                     "hot":l.priority>=3})
    return rows


def fab_map(seed:int=17) -> dict:
    tower=mission_control(seed,70)
    links=[]
    for a,b in zip(BAY_SEQUENCE[:-1],BAY_SEQUENCE[1:]): links.append({"from":a,"to":b,"flow":12+((len(a)+len(b)+seed)%17),"congestion":round(.2+((seed+len(a)*3)%8)/10,2)})
    links += [{"from":"INSPECT","to":"PHOTO","flow":9,"congestion":.61,"type":"REENTRANT"},{"from":"CMP","to":"PHOTO","flow":7,"congestion":.48,"type":"REENTRANT"}]
    return {"bays":tower["bays"],"tools":tower["tool_state"],"links":links,"reticles":tower["reticles"]}
