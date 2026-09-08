from __future__ import annotations
import os, tempfile, time, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.simulation.scenarios import Scenario, run_scenario, monte_carlo
from fabops.decision.engine import recommend_dispatch_rule
from fabops.decision.risk import operational_risk_score
from fabops.optimization.scheduler import optimize_parallel_tool_assignment
from fabops.optimization.release_control import optimize_release
from fabops.ingestion.events import FabEvent, normalize_simulation_log
from fabops.state.engine import WaferStateEngine
from fabops.persistence.sqlite import FabRepository
from fabops.analytics.factory_physics import bottleneck_report, little_law_check
from fabops.optimization.rare_fab import optimize_rare_fab
from fabops.optimization.signature_algorithm import select_release_slot as signature_select, ablation as signature_ablation, sensitivity as signature_sensitivity
from fabops.control.bay_control import bay_risk_heatmap
from fabops.semiconductor.physics import operating_curve, kingman_queue
from fabops.semiconductor.amhs import simulate_amhs
from fabops.semiconductor.equipment import equipment_risk
from fabops.semiconductor.yield_model import yield_risk
from fabops.research.benchmark import rare_fab_benchmark
from fabops.research.portfolio_validation import portfolio_validation
from fabops.operations.control_tower import mission_control, lot_control, fab_map
from fabops.operations.master_data import synthetic_tool_state
from fabops.optimization.rolling_horizon import optimize_rolling_schedule
from fabops.experiments.stress_lab import run_stress_mission
from fabops.decision.orchestrator_v3 import orchestrate_decision
from fabops.operations.genealogy import route_catalog, lot_genealogy, queue_time_watch
from fabops.operations.maintenance import maintenance_calendar, setup_matrix
from fabops.operations.yield_genealogy import yield_genealogy
from fabops.operations.amhs_network import amhs_network
from fabops.experiments.experiment_manager import compare_stress_policies
from fabops.semiconductor.chambers import chamber_state, form_batches, reticle_contention, qualification_matrix
from fabops.optimization.integrated_fab import optimize_integrated_schedule, demo_integrated_jobs
from fabops.optimization.stochastic_recovery import optimize_recovery
from fabops.simulation.coupled_twin import run_coupled_twin
from fabops.optimization.multi_operation import optimize_multi_operation, build_lot_operations
from fabops.decision.closed_loop import run_closed_loop_recovery
from fabops.experiments.scaling_v6 import scaling_experiment
from fabops.data_fabric.mes_simulator import generate_mes_stream
from fabops.data_fabric.validators import validate_events
from fabops.data_fabric.replay import replay_manufacturing_state
from fabops.genealogy.wafer_tree import build_wafer_genealogy
from fabops.equipment.digital_thread import build_equipment_threads
from fabops.process_control.spc import analyze_metrology
from fabops import __version__ as APP_VERSION, __release__ as APP_RELEASE
from fabops.governance import certify_lot_decision, append_entry, read_ledger, verify_ledger
from fabops.copilot import build_response as build_copilot_response, status as copilot_status
from empirical.public_data_backbone import data_backbone_status
PROJECT_ROOT=Path(__file__).resolve().parents[3]
FRONTEND_INDEX=PROJECT_ROOT / "frontend" / "index.html"

app=FastAPI(title="Semiconductor Fab Operations Intelligence API",version=APP_VERSION)

@app.middleware("http")
async def request_context(request, call_next):
    request_id=request.headers.get("X-Request-ID") or f"fab-{uuid.uuid4().hex[:16]}"
    started=time.perf_counter()
    response=await call_next(request)
    response.headers["X-Request-ID"]=request_id
    response.headers["X-Response-Time-Ms"]=f"{(time.perf_counter()-started)*1000:.3f}"
    response.headers["X-Decision-Execution"]="HUMAN_GATED"
    return response
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DB_PATH=os.getenv("FABOPS_DB",os.path.join(tempfile.gettempdir(),"fabops_api.db"))
AUDIT_LEDGER_PATH=os.getenv("FABOPS_AUDIT_LEDGER",os.path.join(tempfile.gettempdir(),"fabops_decision_audit.jsonl"))
repo=FabRepository(DB_PATH)

class SimRequest(BaseModel):
    lots:int=Field(40,ge=5,le=500); rule:str="FIFO"; seed:int=7
    interarrival:float=Field(6.0,gt=0,le=100); failure_rate:float=Field(0.0,ge=0,le=.5); repair_time:float=Field(12.0,ge=0,le=500)
class ScenarioRequest(SimRequest):
    name:str="operator-scenario"; replications:int=Field(20,ge=2,le=100)
class AssignmentRequest(BaseModel): jobs:list[dict]; tools:list[str]
class ReleaseRequest(BaseModel): lots:list[dict]; capacity:dict[str,float]
class IngestRequest(BaseModel): events:list[FabEvent]
class CopilotRequest(BaseModel): message:str=Field(min_length=1,max_length=2000)

@app.get("/copilot/status")
def copilot_runtime_status():
    return copilot_status()

@app.post("/copilot/chat")
def copilot_chat(req: CopilotRequest):
    return build_copilot_response(req.message, {
        "evidence": "FabOps V7.2 reference virtual fab, deterministic scheduling, queue-time, yield/SPC, genealogy, and public-data model provenance",
        "mode": "human-gated review",
    })

@app.get("/", include_in_schema=False)
def operator_console():
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=503, detail="Operator console asset is missing")
    return FileResponse(FRONTEND_INDEX)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health(): return {"status":"ok","service":"fabops","version":APP_VERSION,"release":APP_RELEASE,"database":DB_PATH,"human_gated_decisions":True,"autonomous_execution":False}


@app.get("/governance/signature")
def governance_signature():
    """Expose the executable RARE-FAB CVaR release decision and counterfactuals."""
    lot = {"id": "L1", "due_slot": 10, "queue_risk": .4}
    slots = [8, 12]
    scenarios = [{"queue": .5}, {"queue": 2.0}, {"queue": 5.0}]
    return {"status": "HUMAN_GATED_REFERENCE", "signature_algorithm": "RARE-FAB", "decision": signature_select(lot, slots, scenarios), "baseline": signature_ablation(lot, slots, scenarios), "sensitivity": signature_sensitivity(lot, slots, scenarios, .75), "objective": "minimize nominal lateness plus CVaR tail loss", "counterfactual": "risk-aversion ablation", "evidence_artifact": "artifacts/fortune50_capability_benchmark.json", "autonomous_execution": False}

@app.get("/fab/config")
def config():
    cfg=build_minifab_config()
    return {"products":list(cfg.routes),"tool_count":len(cfg.tools),"tool_groups":sorted(set(t.tool_group for t in cfg.tools)),
            "routes":{p:[{"step":o.step,"group":o.tool_group,"recipe":o.recipe,"process_time":o.process_time} for o in r.operations] for p,r in cfg.routes.items()}}

def _run(req:SimRequest):
    cfg=build_minifab_config(); lots=generate_lots(req.lots,req.seed,req.interarrival)
    return FabSimulator(cfg,seed=req.seed,failure_rate=req.failure_rate,repair_time=req.repair_time).run(lots,req.rule)

@app.post("/simulate")
def simulate(req:SimRequest):
    try:
        out=_run(req).to_dict(); out["bottleneck"]=bottleneck_report(out); out["little_law"]=little_law_check(out); out["risk"]=operational_risk_score(out)
        return out
    except ValueError as e: raise HTTPException(400,str(e))

@app.post("/simulate/persist")
def simulate_persist(req:SimRequest):
    res=_run(req); events=normalize_simulation_log(res.event_log); inserted=repo.append_events(events)
    snap=WaferStateEngine().reconstruct(repo.read_events())
    return {"inserted_events":inserted,"snapshot":snap.to_dict(),"metrics":res.to_dict()}

@app.post("/scenarios/run")
def scenario_run(req:ScenarioRequest):
    s=Scenario(req.name,req.lots,req.seed,req.interarrival,req.failure_rate,req.repair_time,req.rule)
    out=run_scenario(s); repo.record_scenario(out["run_id"],req.name,out); return out

@app.post("/scenarios/monte-carlo")
def scenario_mc(req:ScenarioRequest):
    s=Scenario(req.name,req.lots,req.seed,req.interarrival,req.failure_rate,req.repair_time,req.rule)
    return monte_carlo(s,req.replications)

@app.post("/recommend/dispatch")
def recommend(req:SimRequest):
    cfg=build_minifab_config(); lots=generate_lots(req.lots,req.seed,req.interarrival)
    out=recommend_dispatch_rule(FabSimulator(cfg,seed=req.seed,failure_rate=req.failure_rate,repair_time=req.repair_time),lots).to_dict()
    repo.record_decision("dispatch_rule",req.model_dump(),out); return out

@app.post("/optimize/assignment")
def assignment(req:AssignmentRequest): return optimize_parallel_tool_assignment(req.jobs,req.tools).to_dict()

@app.post("/optimize/release")
def release(req:ReleaseRequest):
    out=optimize_release(req.lots,req.capacity).to_dict(); repo.record_decision("release_control",req.model_dump(),out); return out

@app.post("/events/ingest")
def ingest(req:IngestRequest): return {"received":len(req.events),"inserted":repo.append_events(req.events)}

@app.get("/state/snapshot")
def state_snapshot(as_of:float|None=None): return WaferStateEngine().reconstruct(repo.read_events(as_of),as_of).to_dict()

@app.get("/decisions")
def decisions(limit:int=20): return repo.list_decisions(min(max(limit,1),100))


class RareFabRequest(BaseModel):
    lots:list[dict]; slots:list[dict]; scenarios:list[dict]; alpha:float=Field(.90,gt=0,lt=1); risk_aversion:float=Field(.35,ge=0,le=10)

@app.post("/optimize/rare-fab")
def rare_fab(req:RareFabRequest):
    out=optimize_rare_fab(req.lots,req.slots,req.scenarios,req.alpha,req.risk_aversion).to_dict()
    repo.record_decision("rare_fab_v2",req.model_dump(),out)
    return out

@app.post("/control/bay-risk")
def bay_control(bays:list[dict]): return {"view":"FAB_BAY_RISK_HEATMAP","bays":bay_risk_heatmap(bays),"human_gate":"fab_shift_supervisor"}

@app.post("/semiconductor/amhs")
def amhs(moves:list[dict],vehicles:int=3): return simulate_amhs(moves,vehicles).to_dict()

@app.post("/semiconductor/equipment-risk")
def equipment(tool:dict): return equipment_risk(tool).to_dict()

@app.post("/semiconductor/yield-risk")
def yield_endpoint(payload:dict): return yield_risk(int(payload.get("wafer_count",25)),float(payload.get("defect_density",.02)),float(payload.get("area",1)),float(payload.get("process_z",0)),float(payload.get("rework_fraction",.35))).to_dict()

@app.get("/factory-physics/operating-curve")
def fp_curve(raw_process_time:float=48,bottleneck_rate:float=.08,max_wip:int=20):
    return {"curve":operating_curve(list(range(1,max_wip+1)),raw_process_time,bottleneck_rate)}

@app.get("/research/rare-fab-benchmark")
def rare_benchmark(replications:int=20,lot_count:int=12,seed:int=17):
    return rare_fab_benchmark(seed,min(max(replications,2),100),min(max(lot_count,4),40))


class StressRequest(BaseModel):
    scenario:str="PHOTO_OUTAGE"
    magnitude:float=Field(.25,ge=0,le=1)
    seed:int=31
    lots:int=Field(80,ge=20,le=300)

class ScheduleRequest(BaseModel):
    jobs:list[dict]
    tools:list[dict]
    horizon:float=Field(96.0,gt=1,le=720)


@app.get("/research/portfolio-validation")
def research_portfolio_validation(seed:int=117, replications:int=8, lot_count:int=12):
    return portfolio_validation(seed=seed, replications=replications, lot_count=lot_count)

@app.get("/research/public-data")
def research_public_data():
    """Read-only public benchmark evidence and model-selection provenance."""
    return data_backbone_status()

@app.get("/v3/mission-control")
def v3_mission_control(seed:int=17,lots:int=90):
    return mission_control(seed,min(max(lots,20),200))

@app.get("/v3/fab-map")
def v3_fab_map(seed:int=17): return fab_map(seed)

@app.get("/v3/lots")
def v3_lots(seed:int=17,count:int=36): return {"lots":lot_control(seed,min(max(count,10),120))}

@app.get("/v3/tools")
def v3_tools(seed:int=17): return {"tools":synthetic_tool_state(seed)}

@app.post("/v3/schedule")
def v3_schedule(req:ScheduleRequest):
    out=optimize_rolling_schedule(req.jobs,req.tools,req.horizon).to_dict()
    repo.record_decision("rolling_horizon_schedule_v3",req.model_dump(),out)
    return out

@app.post("/v3/stress")
def v3_stress(req:StressRequest):
    out=run_stress_mission(req.scenario,req.magnitude,req.seed,req.lots).to_dict()
    repo.record_scenario(f"stress-{req.seed}-{req.scenario}",req.scenario,out)
    return out

@app.post("/v3/decision")
def v3_decision(req:StressRequest):
    out=orchestrate_decision(req.scenario,req.magnitude,req.seed).to_dict()
    repo.record_decision("integrated_decision_v3",req.model_dump(),out)
    return out

@app.get("/v3/demo-schedule")
def v3_demo_schedule(seed:int=17):
    tools=synthetic_tool_state(seed)
    jobs=[]
    recipes={"PHOTO":["L1","L2","L3"],"ETCH":["E1","E2","E3"],"CMP":["P1","P2"],"MET":["M1","M2"]}
    n=0
    for bay,rs in recipes.items():
        for k in range(4):
            n+=1; jobs.append({"job_id":f"J{n:02d}","lot_id":f"LOT-{n:03d}","bay":bay,"recipe":rs[(k+seed)%len(rs)],
                "setup_family":rs[k%len(rs)],"process_time":6+(n%5)*1.5,"setup_time":2.0,"due":20+n*3.5,"priority":1+(n%3)})
    return optimize_rolling_schedule(jobs,tools,96).to_dict()


class SupervisorDisposition(BaseModel):
    decision_id:int|None=None
    disposition:str=Field("APPROVE", pattern="^(APPROVE|REJECT|DEFER)$")
    actor:str="FAB_SHIFT_SUPERVISOR"
    note:str=""
    payload:dict={}

@app.get("/v4/routes")
def v4_routes(): return {"routes":route_catalog(),"products":list(route_catalog())}

@app.get("/v4/lot/{lot_id}/genealogy")
def v4_genealogy(lot_id:str,seed:int=17): return lot_genealogy(lot_id,seed)

@app.get("/v4/queue-time-watch")
def v4_queue_time(seed:int=17,count:int=28): return {"lots":queue_time_watch(seed,min(max(count,8),100))}

@app.get("/v4/maintenance-calendar")
def v4_maintenance(seed:int=17,horizon_hours:int=168): return maintenance_calendar(seed,min(max(horizon_hours,24),720))

@app.get("/v4/setup-matrix/{bay}")
def v4_setup_matrix(bay:str): return setup_matrix(bay)

@app.get("/v4/yield-genealogy")
def v4_yield(seed:int=17,count:int=24): return yield_genealogy(seed,min(max(count,8),100))

@app.get("/v4/amhs-network")
def v4_amhs_network(seed:int=17): return amhs_network(seed)

@app.get("/v4/experiment/compare")
def v4_experiment(seed:int=31,lots:int=80,magnitude:float=.35):
    out=compare_stress_policies(seed,min(max(lots,20),200),min(max(magnitude,0),1))
    repo.record_scenario(out["experiment_id"],"V4_MULTI_STRESS",out)
    return out

@app.get("/v4/scenario-history")
def v4_scenario_history(limit:int=30): return repo.list_scenarios(min(max(limit,1),100))

@app.post("/v4/supervisor-disposition")
def v4_supervisor_disposition(req:SupervisorDisposition):
    action_id=repo.record_supervisor_action(req.decision_id,req.disposition,req.actor,req.note,req.payload)
    return {"action_id":action_id,"state":"RECORDED","human_gate":True,**req.model_dump()}

@app.get("/v4/supervisor-history")
def v4_supervisor_history(limit:int=30): return repo.list_supervisor_actions(min(max(limit,1),100))

@app.get("/v4/platform")
def v4_platform(seed:int=17):
    mc=mission_control(seed,90); maint=maintenance_calendar(seed,168); y=yield_genealogy(seed,24); net=amhs_network(seed)
    q=queue_time_watch(seed,28)
    return {"release":"FLAGSHIP_V4","version":APP_VERSION,"mode":"REFERENCE_REPLAY",
            "assets":{"bays":len(mc["bays"]),"tools":len(mc["tool_state"]),"routes":len(route_catalog()),
                      "reticles":len(mc["reticles"]),"oht_vehicles":len(net["vehicles"])},
            "risk":{"queue_time_at_risk":sum(x["state"]!="SAFE" for x in q),"pm_due_24h":maint["due_24h"],
                    "yield_engineering_holds":y["engineering_holds"],"amhs_congested_edges":net["congested_edges"]},
            "workspaces":["MISSION","FAB_TOPOLOGY","LOT_GENEALOGY","QUEUE_TIME","TOOL_PM","RARE_FAB","SCHEDULING",
                          "AMHS_NETWORK","YIELD_REWORK","DIGITAL_TWIN","DECISION_CENTER","EXPERIMENTS","RESEARCH_EVIDENCE"],
            "claim_boundary":"Reference virtual fab operations platform; no site telemetry or production control claim."}


class IntegratedScheduleRequest(BaseModel):
    jobs:list[dict]|None=None
    horizon:int=Field(48,ge=12,le=168)
    seed:int=17

class BatchRequest(BaseModel):
    lots:list[dict]
    max_wait:float=Field(6.0,ge=0,le=48)

class ReticleRequest(BaseModel):
    requests:list[dict]
    horizon:float=Field(24.0,gt=0,le=168)

class RecoveryRequest(BaseModel):
    scenarios:list[dict]|None=None
    alpha:float=Field(.90,gt=.5,lt=.999)
    risk_aversion:float=Field(.45,ge=0,le=5)

@app.get("/v5/chambers")
def v5_chambers(seed:int=17):
    rows=chamber_state(seed)
    return {"chambers":rows,"count":len(rows),"down":sum(x["status"]=="DOWN" for x in rows),
            "busy":sum(x["status"]=="BUSY" for x in rows)}

@app.get("/v5/qualification-matrix")
def v5_qualification(): return qualification_matrix()

@app.post("/v5/batches")
def v5_batches(req:BatchRequest): return form_batches(req.lots,max_wait=req.max_wait)

@app.post("/v5/reticle-contention")
def v5_reticle(req:ReticleRequest): return reticle_contention(req.requests,req.horizon)

@app.get("/v5/demo-integrated-schedule")
def v5_demo_integrated_schedule(seed:int=17,horizon:int=48):
    return optimize_integrated_schedule(None,min(max(horizon,12),96),seed).to_dict()

@app.post("/v5/integrated-schedule")
def v5_integrated_schedule(req:IntegratedScheduleRequest):
    out=optimize_integrated_schedule(req.jobs,req.horizon,req.seed).to_dict()
    repo.record_decision("integrated_queue_pm_reticle_schedule_v5",req.model_dump(),out)
    return out

@app.post("/v5/stochastic-recovery")
def v5_stochastic_recovery(req:RecoveryRequest):
    out=optimize_recovery(req.scenarios,req.alpha,req.risk_aversion).to_dict()
    repo.record_decision("stochastic_recovery_cvar_v5",req.model_dump(),out)
    return out

@app.get("/v5/platform")
def v5_platform(seed:int=17):
    ch=chamber_state(seed); sched=optimize_integrated_schedule(None,48,seed).to_dict(); recovery=optimize_recovery().to_dict()
    return {"release":"FLAGSHIP_V5","version":APP_VERSION,
            "engine":{"chambers":len(ch),"tools":19,"batch_capable_tools":sum(1 for t in qualification_matrix()["tools"].values() if t["batch_capacity"]>1),
                      "reticles":len(qualification_matrix()["reticles"]),"integrated_schedule_success":sched["success"],
                      "queue_breaches":sched["queue_breaches"],"reticle_conflicts":sched["reticle_conflicts"],
                      "stochastic_recovery_action":recovery["action"]},
            "windows_runtime":{"predictive_estimators":"NUMPY_ONLY","pytest_native_faulthandler":"DISABLED_IN_ACCEPTANCE"},
            "claim_boundary":"Reference virtual-fab engine; no live site telemetry or production execution claim."}


class CoupledTwinRequest(BaseModel):
    lots:int=Field(48,ge=12,le=160)
    seed:int=17
    interarrival:float=Field(3.8,gt=.5,le=20)
    failure_rate:float=Field(.015,ge=0,le=.25)
    rework_sensitivity:float=Field(.22,ge=0,le=2)

class MultiOpRequest(BaseModel):
    lots:int=Field(4,ge=2,le=6)
    horizon:int=Field(96,ge=48,le=168)
    seed:int=17

class ClosedLoopRequest(BaseModel):
    scenario:str="PHOTO_OUTAGE"
    seed:int=41
    lots:int=Field(36,ge=20,le=100)
    magnitude:float=Field(.35,ge=0,le=1)

@app.post("/v6/coupled-twin")
def v6_coupled_twin(req:CoupledTwinRequest):
    out=run_coupled_twin(req.lots,req.seed,req.interarrival,req.failure_rate,req.rework_sensitivity).to_dict()
    repo.record_scenario(f"v6-twin-{req.seed}-{req.lots}","V6_COUPLED_TWIN",out)
    return out

@app.get("/v6/coupled-twin/demo")
def v6_coupled_demo(seed:int=17,lots:int=48):
    return run_coupled_twin(min(max(lots,12),120),seed).to_dict()

@app.post("/v6/multi-operation-schedule")
def v6_multi_schedule(req:MultiOpRequest):
    jobs=build_lot_operations(req.lots,req.seed)
    out=optimize_multi_operation(jobs,req.horizon,req.seed).to_dict()
    repo.record_decision("multi_operation_schedule_v6",req.model_dump(),out)
    return out

@app.get("/v6/multi-operation-schedule/demo")
def v6_multi_schedule_demo(seed:int=17,lots:int=4,horizon:int=96):
    return optimize_multi_operation(build_lot_operations(min(max(lots,2),6),seed),min(max(horizon,48),168),seed).to_dict()

@app.post("/v6/closed-loop-recovery")
def v6_closed_loop(req:ClosedLoopRequest):
    out=run_closed_loop_recovery(req.scenario,req.seed,req.lots,req.magnitude).to_dict()
    repo.record_decision("closed_loop_recovery_v6",req.model_dump(),out)
    return out

@app.get("/v6/scaling")
def v6_scaling(seed:int=17): return scaling_experiment(seed)

@app.get("/v6/platform")
def v6_platform(seed:int=17):
    twin=run_coupled_twin(32,seed)
    sched=optimize_multi_operation(build_lot_operations(3,seed),96,seed)
    closed=run_closed_loop_recovery("PHOTO_OUTAGE",seed+24,28,.25)
    return {"release":"FLAGSHIP_V6","version":APP_VERSION,
            "integration":{"coupled_twin_completed":twin.completed,"coupled_twin_events":twin.event_count,
                           "batch_runs":twin.batch_runs,"rework_loops":twin.rework_loops,
                           "multi_operation_schedule":sched.success,"scheduled_operations":sched.operations,
                           "precedence_violations":sched.precedence_violations,"queue_breaches":sched.queue_breaches,
                           "closed_loop_policy":closed.recovery_policy,"closed_loop_state":closed.decision_state},
            "claim_boundary":"Reference virtual-fab integration evidence; no site telemetry or production execution claim."}


@app.get("/v7/mes-stream")
def v7_mes_stream(lots:int=20,wafers_per_lot:int=6,seed:int=71):
    events=generate_mes_stream(min(max(lots,2),100),min(max(wafers_per_lot,1),25),seed)
    return {"events":[e.model_dump(mode="json") for e in events],"validation":validate_events(events)}

@app.get("/v7/state-replay")
def v7_state_replay(lots:int=20,wafers_per_lot:int=6,seed:int=71):
    events=generate_mes_stream(min(max(lots,2),100),min(max(wafers_per_lot,1),25),seed)
    return replay_manufacturing_state(events)

@app.get("/v7/wafer-genealogy")
def v7_wafer_genealogy(lots:int=20,wafers_per_lot:int=6,seed:int=71):
    events=generate_mes_stream(min(max(lots,2),100),min(max(wafers_per_lot,1),25),seed)
    return build_wafer_genealogy(events)

@app.get("/v7/equipment-thread")
def v7_equipment_thread(lots:int=20,wafers_per_lot:int=6,seed:int=71):
    events=generate_mes_stream(min(max(lots,2),100),min(max(wafers_per_lot,1),25),seed)
    return build_equipment_threads(events)

@app.get("/v7/process-health")
def v7_process_health(lots:int=30,wafers_per_lot:int=8,seed:int=71):
    events=generate_mes_stream(min(max(lots,5),100),min(max(wafers_per_lot,3),25),seed)
    vals=[float(e.payload["value"]) for e in events if e.event_type.value=="metrology_result" and e.payload.get("metric")=="cd_nm"]
    if len(vals)<5:
        vals=[100.0,100.1,99.9,100.2,100.0]
    return {"observations":len(vals),"analysis":analyze_metrology(vals,100.0)}

@app.get("/v7/platform")
def v7_platform(seed:int=71):
    events=generate_mes_stream(30,8,seed)
    validation=validate_events(events)
    state=replay_manufacturing_state(events)
    genealogy=build_wafer_genealogy(events)
    equipment=build_equipment_threads(events)
    vals=[float(e.payload["value"]) for e in events if e.event_type.value=="metrology_result" and e.payload.get("metric")=="cd_nm"]
    spc=analyze_metrology(vals or [100,100.1,99.9,100.2,100.0],100.0)
    return {"release":APP_RELEASE,"version":APP_VERSION,
            "data_fabric":{"events":len(events),"valid":validation["valid"],"lots":state["counts"]["lots"],
                           "wafers":genealogy["wafer_count"],"tools":equipment["count"]},
            "process_control":{"observations":len(vals),"state":spc["overall_state"]},
            "capabilities":["CANONICAL_EVENTS","MES_REPLAY","WAFER_GENEALOGY","EQUIPMENT_DIGITAL_THREAD","SPC"],
            "claim_boundary":"Reference manufacturing data fabric and synthetic MES replay; no live fab connection claim."}

from fabops.intelligence.lot_passport import build_lot_passport
from fabops.agents.decision_synthesizer import synthesize

@app.get("/v72/lot-passport")
def v72_lot_passport(lot_id:str="MESLOT-0042"):
    return build_lot_passport(lot_id)

@app.get("/v72/decision-center")
def v72_decision_center(lot_id:str="MESLOT-0042"):
    passport=build_lot_passport(lot_id)
    return synthesize(passport)

@app.get("/v72/risk-analysis")
def v72_risk_analysis(lot_id:str="MESLOT-0042"):
    return build_lot_passport(lot_id)["risk"]

@app.get("/v72/decision-certificate")
def v72_decision_certificate(lot_id:str="MESLOT-0042"):
    return certify_lot_decision(lot_id)

class AuditedDecisionCertificateRequest(BaseModel):
    lot_id:str="MESLOT-0042"
    queue:float=Field(0,ge=0,le=100)
    yield_risk:float=Field(0,ge=0,le=100)
    equipment:float=Field(0,ge=0,le=100)
    delivery:float=Field(0,ge=0,le=100)

@app.post("/v72/decision-certificate/audited")
def v72_audited_decision_certificate(req:AuditedDecisionCertificateRequest):
    certificate=certify_lot_decision(req.lot_id,queue=req.queue,yield_risk=req.yield_risk,equipment=req.equipment,delivery=req.delivery)
    ledger=append_entry(AUDIT_LEDGER_PATH,event_type="LOT_DECISION_CERTIFIED",payload={
        "lot_id":req.lot_id,"certificate_sha256":certificate["certificate_sha256"],
        "decision_state":certificate["decision_state"],"recommendation":certificate["recommendation"],
        "autonomous_execution_allowed":False,
    })
    return {"certificate":certificate,"audit_entry":ledger,"audit_ledger_valid":verify_ledger(AUDIT_LEDGER_PATH)["valid"]}

@app.get("/governance/audit/verify")
def governance_audit_verify():
    return verify_ledger(AUDIT_LEDGER_PATH)

@app.get("/governance/audit/events")
def governance_audit_events(limit:int=20):
    rows=read_ledger(AUDIT_LEDGER_PATH)
    return {"items":rows[-min(max(limit,1),100):],"verification":verify_ledger(AUDIT_LEDGER_PATH)}
