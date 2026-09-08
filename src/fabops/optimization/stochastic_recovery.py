from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

ACTIONS=("HOLD_RELEASE","ALT_ROUTE","PULL_PM_FORWARD","PROTECT_RETICLE","BALANCED_RECOVERY")

@dataclass(frozen=True)
class RecoveryPlan:
    success:bool; action:str; expected_loss:float; cvar:float; objective:float; scenario_losses:list[float]; alpha:float; risk_aversion:float
    def to_dict(self): return asdict(self)

def _loss(action:str,s:dict)->float:
    outage=float(s.get("outage",0)); demand=float(s.get("demand",0)); amhs=float(s.get("amhs",0)); yield_risk=float(s.get("yield_risk",0)); reticle=float(s.get("reticle",0))
    base=70*outage+55*demand+45*amhs+65*yield_risk+50*reticle
    effects={
      "HOLD_RELEASE": -30*demand-18*amhs+8*yield_risk,
      "ALT_ROUTE": -32*outage-16*reticle+8*amhs,
      "PULL_PM_FORWARD": -26*outage+6*demand,
      "PROTECT_RETICLE": -34*reticle-10*outage+5*demand,
      "BALANCED_RECOVERY": -18*outage-16*demand-12*amhs-14*yield_risk-15*reticle+5
    }
    return max(0,base+effects[action])

def optimize_recovery(scenarios:list[dict]|None=None,alpha:float=.90,risk_aversion:float=.45)->RecoveryPlan:
    scenarios=scenarios or [
      {"outage":.8,"demand":.2,"amhs":.3,"yield_risk":.1,"reticle":.5},
      {"outage":.3,"demand":.8,"amhs":.6,"yield_risk":.2,"reticle":.2},
      {"outage":.4,"demand":.4,"amhs":.9,"yield_risk":.3,"reticle":.3},
      {"outage":.2,"demand":.3,"amhs":.2,"yield_risk":.85,"reticle":.2},
      {"outage":.55,"demand":.35,"amhs":.3,"yield_risk":.2,"reticle":.9},
    ]
    losses=np.array([[_loss(a,s) for s in scenarios] for a in ACTIONS],float)
    A=len(ACTIONS); S=len(scenarios)
    # variables x[A], eta, z[S]; exact one action, CVaR epigraph with big-M.
    n=A+1+S; c=np.zeros(n)
    c[:A]=losses.mean(axis=1)
    c[A]=risk_aversion
    c[A+1:]=risk_aversion/(max(1e-6,1-alpha)*S)
    integrality=np.zeros(n); integrality[:A]=1
    lb=np.zeros(n); ub=np.full(n,np.inf); ub[:A]=1; ub[A]=losses.max()*2+1
    rows=[]; lo=[]; hi=[]
    row=np.zeros(n); row[:A]=1; rows.append(row); lo.append(1); hi.append(1)
    M=float(losses.max()*3+100)
    for s in range(S):
        # z_s >= loss[a,s] - eta if action a selected
        for a in range(A):
            row=np.zeros(n); row[A+1+s]=1; row[A]=1; row[a]=-M
            rows.append(row); lo.append(losses[a,s]-M); hi.append(np.inf)
    res=milp(c,integrality=integrality,bounds=Bounds(lb,ub),constraints=[LinearConstraint(np.vstack(rows),lo,hi)])
    if not res.success:
        return RecoveryPlan(False,"NONE",float("inf"),float("inf"),float("inf"),[],alpha,risk_aversion)
    a=int(np.argmax(res.x[:A])); ls=losses[a].tolist(); expected=float(np.mean(ls))
    q=np.quantile(ls,alpha,method="higher"); tail=[x for x in ls if x>=q]; cvar=float(np.mean(tail))
    return RecoveryPlan(True,ACTIONS[a],round(expected,3),round(cvar,3),round(expected+risk_aversion*cvar,3),
                        [round(x,3) for x in ls],alpha,risk_aversion)
