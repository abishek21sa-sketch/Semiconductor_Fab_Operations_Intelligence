from __future__ import annotations
from dataclasses import dataclass, asdict
from fabops.simulation.engine import FabSimulator

@dataclass(frozen=True)
class Recommendation:
    recommended_rule: str
    rationale: list[str]
    evidence: dict
    confidence: str
    def to_dict(self): return asdict(self)

def recommend_dispatch_rule(simulator: FabSimulator, lots, rules=("FIFO","EDD","CR","PRIORITY")) -> Recommendation:
    results={r:simulator.run(lots,r) for r in rules}
    # lexicographic operational objective: tardiness, cycle time, then WIP
    best=min(results.values(),key=lambda x:(x.avg_tardiness,x.avg_cycle_time,x.avg_wip))
    fifo=results.get("FIFO")
    rationale=[f"{best.rule} produced the lowest evaluated tardiness/cycle-time objective across {len(results)} reproducible scenarios."]
    if fifo and best.rule != "FIFO":
        rationale.append(f"Versus FIFO: average tardiness {fifo.avg_tardiness:.2f} -> {best.avg_tardiness:.2f}; average cycle time {fifo.avg_cycle_time:.2f} -> {best.avg_cycle_time:.2f}.")
    evidence={r:{"avg_tardiness":x.avg_tardiness,"avg_cycle_time":x.avg_cycle_time,"on_time_rate":x.on_time_rate,"avg_wip":x.avg_wip} for r,x in results.items()}
    return Recommendation(best.rule,rationale,evidence,"simulation-backed")
