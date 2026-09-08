from __future__ import annotations
from dataclasses import dataclass, asdict
import heapq

@dataclass(frozen=True)
class TransportResult:
    completed:int; mean_transfer_time:float; p95_transfer_time:float; max_queue:int; vehicle_utilization:float
    def to_dict(self): return asdict(self)

def simulate_amhs(moves:list[dict], vehicles:int=3, base_travel:float=2.0, congestion_factor:float=.12) -> TransportResult:
    """Deterministic AMHS queue proxy for inter-bay move contention."""
    if vehicles<1: raise ValueError("vehicles must be >=1")
    avail=[0.0]*vehicles; heapq.heapify(avail); durations=[]; maxq=0; busy=0.0
    ordered=sorted(moves,key=lambda x:float(x.get("request_time",0)))
    for idx,m in enumerate(ordered):
        req=float(m.get("request_time",0)); free=heapq.heappop(avail); start=max(req,free)
        q=sum(1 for a in avail if a>req) + (1 if free>req else 0); maxq=max(maxq,q)
        distance=max(float(m.get("distance",1.0)),.1); service=base_travel*distance*(1+congestion_factor*q)
        finish=start+service; heapq.heappush(avail,finish); busy+=service; durations.append(finish-req)
    if not durations: return TransportResult(0,0,0,0,0)
    s=sorted(durations); p=s[min(len(s)-1,int(.95*(len(s)-1)))]
    horizon=max(avail) if avail else 0
    return TransportResult(len(durations),round(sum(durations)/len(durations),4),round(p,4),maxq,round(busy/max(horizon*vehicles,1e-9),4))
