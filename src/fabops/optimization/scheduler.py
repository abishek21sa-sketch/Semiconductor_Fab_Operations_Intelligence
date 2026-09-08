from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

@dataclass(frozen=True)
class AssignmentResult:
    success: bool
    objective: float
    assignments: list[dict]
    message: str
    def to_dict(self): return asdict(self)

def optimize_parallel_tool_assignment(jobs: list[dict], tools: list[str]) -> AssignmentResult:
    """MILP: assign ready operations to parallel qualified tools minimizing load + tardiness proxy.

    This is intentionally a bounded rolling-horizon optimizer, suitable as a decision service,
    not a claim of full-fab global optimality.
    """
    if not jobs or not tools:
        return AssignmentResult(True,0.0,[],"nothing to assign")
    n,m=len(jobs),len(tools)
    # x_ij binary, plus z=max assigned processing load
    c=np.zeros(n*m+1); c[-1]=1.0
    for i,j in enumerate(jobs):
        urgency=max(0.0, float(j.get("slack",0))*-1)
        for k in range(m): c[i*m+k]=0.01*urgency
    integrality=np.zeros(n*m+1); integrality[:n*m]=1
    lb=np.zeros(n*m+1); ub=np.ones(n*m+1); ub[-1]=np.inf
    constraints=[]
    # every job exactly one tool
    A=np.zeros((n,n*m+1))
    for i in range(n): A[i,i*m:(i+1)*m]=1
    constraints.append(LinearConstraint(A,np.ones(n),np.ones(n)))
    # qualification by upper bounds
    for i,j in enumerate(jobs):
        qualified=set(j.get("qualified_tools",tools))
        for k,t in enumerate(tools):
            if t not in qualified: ub[i*m+k]=0
    # each tool load <= z
    Aload=np.zeros((m,n*m+1))
    for k in range(m):
        for i,j in enumerate(jobs): Aload[k,i*m+k]=float(j["process_time"])
        Aload[k,-1]=-1
    constraints.append(LinearConstraint(Aload,-np.inf*np.ones(m),np.zeros(m)))
    res=milp(c,integrality=integrality,bounds=Bounds(lb,ub),constraints=constraints,options={"time_limit":5.0})
    if not res.success:
        return AssignmentResult(False,float("inf"),[],res.message)
    x=res.x[:n*m].reshape(n,m)
    assignments=[]
    for i,j in enumerate(jobs):
        k=int(np.argmax(x[i])); assignments.append({"job_id":j["job_id"],"tool_id":tools[k],"process_time":j["process_time"]})
    return AssignmentResult(True,round(float(res.fun),4),assignments,res.message)
