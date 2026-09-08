from __future__ import annotations
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class QueuePhysics:
    utilization: float
    ca2: float
    cs2: float
    effective_process_time: float
    approx_wait: float
    cycle_time: float
    critical_wip: float
    bottleneck_rate: float
    def to_dict(self): return asdict(self)

def kingman_queue(utilization:float, mean_process:float, ca2:float=1.0, cs2:float=1.0) -> QueuePhysics:
    """Factory-Physics queue approximation; fails closed near/above saturation."""
    if mean_process<=0: raise ValueError("mean_process must be positive")
    rho=max(0.0,float(utilization))
    if rho>=1: wait=float("inf")
    else: wait=((ca2+cs2)/2.0)*(rho/(1-rho))*mean_process
    ct=mean_process+wait
    rate=1.0/mean_process
    return QueuePhysics(rho,ca2,cs2,mean_process,wait,ct,rate*mean_process,rate)

def operating_curve(wip_values:list[float], raw_process_time:float, bottleneck_rate:float) -> list[dict]:
    if raw_process_time<=0 or bottleneck_rate<=0: raise ValueError("positive raw_process_time and bottleneck_rate required")
    critical=raw_process_time*bottleneck_rate
    out=[]
    for w in wip_values:
        th=min(bottleneck_rate, max(0.0,w)/raw_process_time)
        ct=(w/th) if th>0 else raw_process_time
        out.append({"wip":float(w),"throughput":round(th,6),"cycle_time":round(ct,6),"critical_wip":round(critical,6)})
    return out
