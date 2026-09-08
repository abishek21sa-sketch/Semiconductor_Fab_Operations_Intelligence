from __future__ import annotations
import copy, heapq, random
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
from fabops.domain.models import FabConfig, Lot, Tool, ToolStatus
from fabops.simulation.dispatch import select_lot

@dataclass(frozen=True)
class SimulationResult:
    rule: str
    makespan: float
    throughput: int
    avg_cycle_time: float
    p95_cycle_time: float
    avg_tardiness: float
    on_time_rate: float
    avg_wip: float
    utilization: dict[str,float]
    completed_lots: list[dict]
    event_log: list[dict]

    def to_dict(self):
        return asdict(self)

class FabSimulator:
    def __init__(self, config: FabConfig, seed: int = 42, failure_rate: float = 0.0, repair_time: float = 12.0):
        self.base_config=config
        self.seed=seed
        self.failure_rate=failure_rate
        self.repair_time=repair_time

    def run(self, lots: list[Lot], rule: str="FIFO", horizon: float|None=None) -> SimulationResult:
        rng=random.Random(self.seed)
        lots=copy.deepcopy(lots)
        tools=[copy.deepcopy(t) for t in self.base_config.tools]
        routes=self.base_config.routes
        queues=defaultdict(list)
        events=[]; seq=0; log=[]; now=0.0; completed=[]
        wip_area=0.0; last_event=0.0; in_system=0

        def push(time, kind, payload):
            nonlocal seq
            seq+=1; heapq.heappush(events,(time,seq,kind,payload))
        for lot in lots: push(lot.release_time,"release",lot)

        def dispatch_group(group, now):
            nonlocal seq
            idle=[t for t in tools if t.tool_group==group and t.status==ToolStatus.IDLE and t.available_at<=now+1e-9]
            q=queues[group]
            while idle and q:
                # candidate must be qualified for at least one idle tool
                qualified=[l for l in q if any(routes[l.product].operations[l.step_index].recipe in t.qualified_recipes for t in idle)]
                if not qualified: break
                lot=select_lot(qualified,now,lambda p:routes[p],rule)
                op=routes[lot.product].operations[lot.step_index]
                tool=next(t for t in idle if op.recipe in t.qualified_recipes)
                q.remove(lot); idle.remove(tool)
                lot.total_queue_time += max(0.0, now-lot.queue_enter_time)
                if lot.start_time is None: lot.start_time=now
                setup=self.base_config.setup_time if tool.current_recipe not in (None,op.recipe) else 0.0
                duration=op.process_time+setup
                # stochastic disruption is intentionally explicit and reproducible
                failed=rng.random() < self.failure_rate
                if failed: duration += self.repair_time
                tool.status=ToolStatus.BUSY; tool.available_at=now+duration
                tool.busy_time += op.process_time; tool.setup_time += setup
                tool.current_recipe=op.recipe
                lot.history.append({"step":op.step,"tool":tool.tool_id,"start":now,"finish":now+duration,"recipe":op.recipe,"failure":failed})
                log.append({"time":now,"event":"start","lot_id":lot.lot_id,"tool_id":tool.tool_id,"step":op.step,"recipe":op.recipe,"rule":rule})
                push(now+duration,"finish",(lot,tool))

        while events:
            now,_,kind,payload=heapq.heappop(events)
            if horizon is not None and now>horizon: break
            wip_area += in_system*(now-last_event); last_event=now
            if kind=="release":
                lot=payload; in_system+=1; lot.queue_enter_time=now
                op=routes[lot.product].operations[lot.step_index]; queues[op.tool_group].append(lot)
                log.append({"time":now,"event":"release","lot_id":lot.lot_id,"product":lot.product})
                dispatch_group(op.tool_group,now)
            elif kind=="finish":
                lot,tool=payload; tool.status=ToolStatus.IDLE
                op=routes[lot.product].operations[lot.step_index]
                log.append({"time":now,"event":"finish","lot_id":lot.lot_id,"tool_id":tool.tool_id,"step":op.step,"recipe":op.recipe,
                            "route_complete": lot.step_index + 1 >= len(routes[lot.product].operations)})
                lot.step_index+=1
                if lot.step_index>=len(routes[lot.product].operations):
                    lot.completion_time=now; completed.append(lot); in_system-=1
                else:
                    lot.queue_enter_time=now
                    nxt=routes[lot.product].operations[lot.step_index]
                    queues[nxt.tool_group].append(lot)
                dispatch_group(tool.tool_group,now)
                if not lot.completed: dispatch_group(routes[lot.product].operations[lot.step_index].tool_group,now)

        makespan=max((l.completion_time or 0.0 for l in completed),default=0.0)
        cts=[l.completion_time-l.release_time for l in completed]
        tard=[max(0.0,l.completion_time-l.due_time) for l in completed]
        util={t.tool_id: round(t.busy_time/max(makespan,1e-9),4) for t in tools}
        completed_records=[{
            "lot_id":l.lot_id,"product":l.product,"priority":l.priority,"release_time":l.release_time,
            "due_time":l.due_time,"completion_time":round(l.completion_time,3),
            "cycle_time":round(l.completion_time-l.release_time,3),"queue_time":round(l.total_queue_time,3),
            "tardiness":round(max(0,l.completion_time-l.due_time),3),"on_time":l.completion_time<=l.due_time
        } for l in completed]
        return SimulationResult(
            rule=rule,makespan=round(makespan,3),throughput=len(completed),
            avg_cycle_time=round(float(np.mean(cts)) if cts else 0,3),
            p95_cycle_time=round(float(np.percentile(cts,95)) if cts else 0,3),
            avg_tardiness=round(float(np.mean(tard)) if tard else 0,3),
            on_time_rate=round(sum(x==0 for x in tard)/len(tard),4) if tard else 0,
            avg_wip=round(wip_area/max(now,1e-9),3),utilization=util,
            completed_lots=completed_records,event_log=log)
