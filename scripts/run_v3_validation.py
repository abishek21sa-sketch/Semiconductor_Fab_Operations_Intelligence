from __future__ import annotations
import json
from pathlib import Path
from fabops.operations.control_tower import mission_control, fab_map, lot_control
from fabops.optimization.rolling_horizon import optimize_rolling_schedule
from fabops.operations.master_data import synthetic_tool_state
from fabops.experiments.stress_lab import run_stress_mission
from fabops.decision.orchestrator_v3 import orchestrate_decision
from fabops.research.benchmark import rare_fab_benchmark

root=Path(__file__).resolve().parents[1]
tower=mission_control(23,90)
fm=fab_map(23)
lots=lot_control(23,50)
tools=synthetic_tool_state(23)
jobs=[]; recipes={'PHOTO':['L1','L2','L3'],'ETCH':['E1','E2'],'CMP':['P1','P2'],'MET':['M1','M2']}; n=0
for bay,rs in recipes.items():
    for k in range(3):
        n+=1; jobs.append({'job_id':f'V{n:02d}','lot_id':f'LOT-V{n:03d}','bay':bay,'recipe':rs[k%len(rs)],'setup_family':rs[(k+1)%len(rs)],'process_time':6+k*2,'setup_time':2,'due':18+n*4,'priority':1+n%3})
sched=optimize_rolling_schedule(jobs,tools,96).to_dict()
stress=run_stress_mission('PHOTO_OUTAGE',.40,37,80).to_dict()
decision=orchestrate_decision('PHOTO_OUTAGE',.40,37).to_dict()
bench=rare_fab_benchmark(19,20,12)
out={
 'release':'FLAGSHIP_V3', 'production_validated':False,
 'platform':{'workspaces':10,'virtual_bays':len(tower['bays']),'tool_assets':len(tower['tool_state']),'reticles':len(tower['reticles']),'lot_rows_validated':len(lots),'reentrant_links':sum(x.get('type')=='REENTRANT' for x in fm['links'])},
 'mission_control':{'kpis':tower['kpis'],'constrained_bays':[b['bay'] for b in tower['bays'] if b['state']!='NOMINAL'],'alerts':len(tower['alerts'])},
 'rolling_schedule':{'success':sched['success'],'jobs':len(sched['assignments']),'tardy_jobs':sched['tardy_jobs'],'runtime_s':sched['runtime_s'],'tools_used':sum(v>0 for v in sched['tool_load'].values())},
 'stress_mission':{'scenario':stress['scenario'],'severity':stress['severity'],'delta':stress['delta'],'recommendation_count':len(stress['recommendations'])},
 'decision_packet':{'state':decision['state'],'severity':decision['severity'],'actions':len(decision['actions']),'evidence_items':len(decision['evidence']),'human_gate':decision['human_gate']},
 'rare_fab':{'replications':bench['replications'],'dominance_rate':bench['dominance_rate'],'rare_cvar90':bench['rare_fab_cvar90'],'baseline_cvar90':bench['baseline_cvar90'],'falsification_pass':bench['falsification_pass']},
 'claim_boundary':'Reference virtual-fab evidence only. No live MES, site performance, novelty, autonomous execution, or realized-impact claim.'
}
path=root/'docs'/'validation'/'v3_validation.json'; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
