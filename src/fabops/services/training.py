from __future__ import annotations
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.simulation.scenarios import Scenario, run_scenario
from fabops.ai.cycle_time import CycleTimeModel
from fabops.ai.eta import ETAModel
from fabops.ai.bottleneck import BottleneckModel


def build_training_records(replications:int=8,lots_per:int=50)->list[dict]:
    cfg=build_minifab_config(); records=[]
    for seed in range(100,100+replications):
        lots=generate_lots(lots_per,seed,interarrival=6.0)
        res=FabSimulator(cfg,seed=seed,failure_rate=.02,repair_time=10).run(lots,"CR")
        records.extend(res.completed_lots)
    return records

def train_predictive_suite()->dict:
    records=build_training_records()
    cycle=CycleTimeModel(); cycle_metrics=cycle.fit(records,seed=42)
    eta=ETAModel(); eta_metrics=eta.fit(records,seed=42)
    scen=[]
    for i in range(36):
        s=Scenario(name=f"train-{i}",lots=50+(i%4)*10,seed=200+i,interarrival=4.5+(i%5)*.7,
                   failure_rate=(i%4)*.02,repair_time=8+(i%3)*4,rule="CR")
        r=run_scenario(s)
        scen.append({"lots":s.lots,"interarrival":s.interarrival,"failure_rate":s.failure_rate,"repair_time":s.repair_time,
                     "bottleneck":r["bottleneck"]["primary_bottleneck"]})
    bottleneck=BottleneckModel(); bottleneck_metrics=bottleneck.fit(scen,seed=42)
    return {"cycle_time":{"model":cycle,"metrics":cycle_metrics},"eta":{"model":eta,"metrics":eta_metrics},
            "bottleneck":{"model":bottleneck,"metrics":bottleneck_metrics}}
