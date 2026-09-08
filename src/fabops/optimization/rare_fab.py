from __future__ import annotations
from dataclasses import dataclass, asdict
from math import ceil
import time
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

@dataclass(frozen=True)
class RareFabPlan:
    success: bool
    alpha: float
    risk_aversion: float
    objective: float
    nominal_cost: float
    var_threshold: float
    cvar_loss: float
    assignments: list[dict]
    slot_load: dict[str, float]
    scenario_losses: list[float]
    runtime_s: float
    solver_message: str
    evidence_class: str = "REFERENCE_SYNTHETIC_BENCHMARK"
    human_gate: str = "FAB_SHIFT_SUPERVISOR_REVIEW_REQUIRED"
    def to_dict(self): return asdict(self)

def _slot_pressure(stress:dict, slot:int) -> float:
    """Return scenario pressure for a candidate release slot.

    Scenarios may provide a scalar, list/tuple, or mapping.  This is the key coupling
    between an uncertain fab state and the release decision: a PHOTO/AMHS/qualification
    shock can make one release window materially worse than another.
    """
    raw=stress.get("slot_pressure",1.0)
    if isinstance(raw,(list,tuple)):
        if not raw: return 1.0
        return max(.2,float(raw[min(max(slot,0),len(raw)-1)]))
    if isinstance(raw,dict):
        value=raw.get(slot,raw.get(str(slot),1.0))
        return max(.2,float(value))
    return max(.2,float(raw))

def _cost(lot:dict, slot:int, stress:dict) -> float:
    release=float(slot)
    due=float(lot.get("due_slot", max(slot+1, 1)))
    priority=max(float(lot.get("priority",1.0)), 1.0)
    tard=max(0.0, release-due)
    pressure=_slot_pressure(stress,slot)
    # Scenario severity is decision-dependent through slot pressure.  High-risk lots
    # therefore have a reason to avoid vulnerable release windows under CVaR.
    queue=float(lot.get("queue_risk",0.0))*float(stress.get("queue",1.0))*pressure
    amhs=float(lot.get("amhs_moves",1.0))*float(stress.get("amhs",1.0))*(.75+.25*pressure)
    energy=float(lot.get("energy_kwh",1.0))*float(stress.get("energy",1.0))*(.9+.1*pressure)
    maint=float(lot.get("maintenance_interaction",0.0))*float(stress.get("maintenance",1.0))*(.7+.3*pressure)
    qual=float(lot.get("qualification_risk",0.0))*float(stress.get("qualification",1.0))*(.65+.35*pressure)
    return 8.0*priority*tard + 2.5*queue + 1.5*amhs + 0.8*energy + 2.0*maint + 4.0*qual + 0.15*release

def optimize_rare_fab(lots:list[dict], slots:list[dict], scenarios:list[dict], alpha:float=.90, risk_aversion:float=.35, time_limit:float=10.0) -> RareFabPlan:
    """Two-stage-style release master with CVaR recourse proxy.

    Binary x[i,t] assigns each candidate lot to exactly one release slot. Scenario losses
    couple service/tardiness, queue, AMHS, energy, maintenance and qualification stress.
    Only the first receding-horizon release action should be executed operationally.
    """
    start=time.perf_counter()
    if not lots or not slots:
        return RareFabPlan(True,alpha,risk_aversion,0,0,0,0,[],{},[],0,"nothing to optimize")
    if not scenarios: scenarios=[{"name":"nominal"}]
    if not (0 < alpha < 1): raise ValueError("alpha must be in (0,1)")
    n,m,s=len(lots),len(slots),len(scenarios); xN=n*m; eta_idx=xN; u0=xN+1; N=xN+1+s
    nominal=np.zeros(xN)
    scen=np.zeros((s,xN))
    for i,lot in enumerate(lots):
        for t,slot in enumerate(slots):
            j=i*m+t
            nominal[j]=_cost(lot,t,{}) + float(slot.get("base_penalty",0.0))
            for k,st in enumerate(scenarios):
                scen[k,j]=_cost(lot,t,st)+float(slot.get("base_penalty",0.0))*float(st.get("capacity",1.0))
    c=np.zeros(N); c[:xN]=nominal/max(n,1); c[eta_idx]=risk_aversion; c[u0:]=risk_aversion/((1-alpha)*s)
    A=[]; lb=[]; ub=[]
    # each lot exactly once
    for i in range(n):
        row=np.zeros(N); row[i*m:(i+1)*m]=1; A.append(row); lb.append(1); ub.append(1)
    # slot workload and WIP capacity by resource dimension
    resources=sorted({r for slot in slots for r in slot.get("capacity",{})})
    for t,slot in enumerate(slots):
        for r in resources:
            row=np.zeros(N)
            for i,lot in enumerate(lots): row[i*m+t]=float(lot.get("workload",{}).get(r,0.0))
            A.append(row); lb.append(-np.inf); ub.append(float(slot.get("capacity",{}).get(r,np.inf)))
        row=np.zeros(N)
        for i,lot in enumerate(lots): row[i*m+t]=float(lot.get("wip_units",1.0))
        A.append(row); lb.append(-np.inf); ub.append(float(slot.get("wip_limit",len(lots))))
    # CVaR u[k] >= scenario_loss(x)-eta
    for k in range(s):
        row=np.zeros(N); row[:xN]=scen[k]; row[eta_idx]=-1; row[u0+k]=-1
        A.append(row); lb.append(-np.inf); ub.append(0)
    lower=np.r_[np.zeros(xN), -np.inf, np.zeros(s)]
    upper=np.r_[np.ones(xN), np.inf, np.full(s,np.inf)]
    res=milp(c, integrality=np.r_[np.ones(xN),np.zeros(1+s)], bounds=Bounds(lower,upper),
             constraints=[LinearConstraint(np.vstack(A),np.array(lb),np.array(ub))], options={"time_limit":time_limit})
    runtime=time.perf_counter()-start
    if not res.success:
        return RareFabPlan(False,alpha,risk_aversion,float("inf"),0,0,0,[],{},[],round(runtime,6),str(res.message))
    x=res.x[:xN].reshape(n,m); assignments=[]
    for i,lot in enumerate(lots):
        t=int(np.argmax(x[i])); assignments.append({"lot_id":lot["lot_id"],"slot":slots[t].get("slot",t),"slot_index":t,"execute_now":t==0})
    losses=[float(scen[k]@res.x[:xN]) for k in range(s)]
    q=float(np.quantile(losses,alpha,method="higher")); tail=[z for z in losses if z>=q]
    slot_load={}
    for t,slot in enumerate(slots):
        slot_load[str(slot.get("slot",t))]=round(sum(float(lots[i].get("wip_units",1)) for i in range(n) if x[i,t]>.5),3)
    return RareFabPlan(True,alpha,risk_aversion,round(float(res.fun),5),round(float(nominal@res.x[:xN]),5),round(float(res.x[eta_idx]),5),
                       round(float(np.mean(tail)),5),assignments,slot_load,[round(v,5) for v in losses],round(runtime,6),str(res.message))
