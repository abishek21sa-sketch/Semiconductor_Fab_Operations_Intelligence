from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.simulation.scenarios import Scenario, monte_carlo
from fabops.decision.engine import recommend_dispatch_rule
from fabops.analytics.factory_physics import bottleneck_report, little_law_check
from fabops.decision.risk import operational_risk_score
from fabops.services.training import train_predictive_suite
from fabops.ingestion.events import normalize_simulation_log
from fabops.state.engine import WaferStateEngine
from fabops.optimization.release_control import optimize_release
from fabops.optimization.scheduler import optimize_parallel_tool_assignment

OUT=ROOT/"docs"/"validation"/"validation_results.json"
OUT.parent.mkdir(parents=True,exist_ok=True)

cfg=build_minifab_config(); lots=generate_lots(120,seed=11,interarrival=5.5)
sim=FabSimulator(cfg,seed=11,failure_rate=0.03,repair_time=10)
rec=recommend_dispatch_rule(sim,lots)
reference=sim.run(lots,"CR")
ref=reference.to_dict()

suite=train_predictive_suite()
models={name:{"metrics":obj["metrics"]} for name,obj in suite.items()}
models["cycle_time"]["feature_importance"]=suite["cycle_time"]["model"].feature_importance()

canonical=normalize_simulation_log(reference.event_log)
snapshot=WaferStateEngine().reconstruct(canonical).to_dict()

assignment=optimize_parallel_tool_assignment([
    {"job_id":"J1","process_time":9,"slack":-5,"qualified_tools":["LITHO-01","LITHO-02"]},
    {"job_id":"J2","process_time":6,"slack":3,"qualified_tools":["LITHO-01"]},
    {"job_id":"J3","process_time":7,"slack":-2,"qualified_tools":["LITHO-02"]},
],["LITHO-01","LITHO-02"]).to_dict()
release=optimize_release([
    {"lot_id":"HOT-1","weight":10,"workload":{"LITHO":8,"ETCH":4,"DIFF":7}},
    {"lot_id":"STD-1","weight":5,"workload":{"LITHO":6,"ETCH":5,"DIFF":6}},
    {"lot_id":"STD-2","weight":5,"workload":{"LITHO":5,"ETCH":4,"DIFF":6}},
    {"lot_id":"LOW-1","weight":2,"workload":{"LITHO":4,"ETCH":3,"DIFF":4}},
],{"LITHO":14,"ETCH":10,"DIFF":14}).to_dict()
mc=monte_carlo(Scenario("validation-disruption",lots=70,seed=19,interarrival=5.8,failure_rate=.04,repair_time=12,rule="CR"),replications=12)

payload={
  "release":"v0.9.0",
  "evidence_boundary":"All quantitative results are generated from the included synthetic MiniFab-inspired benchmark and are not real-fab performance claims.",
  "reference_run":{
      "rule":reference.rule,"throughput":reference.throughput,"makespan":reference.makespan,
      "avg_cycle_time":reference.avg_cycle_time,"p95_cycle_time":reference.p95_cycle_time,
      "avg_tardiness":reference.avg_tardiness,"on_time_rate":reference.on_time_rate,"avg_wip":reference.avg_wip,
      "bottleneck":bottleneck_report(ref),"little_law":little_law_check(ref),"operational_risk":operational_risk_score(ref)
  },
  "dispatch_recommendation":rec.to_dict(),
  "monte_carlo":mc,
  "predictive_models":models,
  "state_reconstruction":{"canonical_events":len(canonical),"lots":len(snapshot["lots"]),"tools":len(snapshot["tools"]),"wip":snapshot["wip"],"anomalies":snapshot["anomalies"][:10]},
  "optimization":{"parallel_tool_assignment":assignment,"release_control":release},
}
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
