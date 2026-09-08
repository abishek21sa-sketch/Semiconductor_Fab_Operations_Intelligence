from __future__ import annotations
import math
from tenx.engine import run_decision
from campaign.engine import run_campaign
from empirical.backbone import run_empirical_reference

def lifecycle_report():
    d=run_decision(17); c=run_campaign(); e=run_empirical_reference()
    validation=d.get('model_validation',{})
    preds=d.get('predictions') or d.get('prediction') or {}
    vals=[]
    if isinstance(preds,dict):
        for v in preds.values():
            if isinstance(v,(int,float)): vals.append(float(v))
            elif isinstance(v,dict): vals.extend(float(x) for x in v.values() if isinstance(x,(int,float)))
    spread=(max(vals)-min(vals)) if len(vals)>1 else 0.0
    entropy=float(c.get('ranking_entropy', c.get('ranking_entropy_bits', 0.0)) or 0.0)
    drift='WATCH' if entropy>1.4 or spread>0.65 else 'STABLE'
    public_data=d.get('public_data_backbone',{})
    return {'public_data_state':public_data.get('dataset_state'),'public_evidence_gate':d.get('public_evidence_gate'),'model_family':d['ml_family'],'target':d['prediction_target'],'validation':validation,'drift_state':drift,'ranking_entropy':entropy,'prediction_spread':round(spread,5),'retrain_trigger':'retrain hazard model if ranking entropy >1.4 bits or monthly calibration error breaches release band','monitoring':['queue-time calibration by operation','hazard residual by tool family','late-lot recall','prediction-to-RARE-FAB decision impact'],'registry_state':'CHALLENGER_READY' if drift=='WATCH' else 'CHAMPION_ACTIVE','source_mode':e.get('data_mode') or e.get('source_mode')}

def run_agent():
    d=run_decision(17); c=run_campaign(); life=lifecycle_report()
    steps=['load fab WIP + tool/reticle/PM state','score queue-time breach hazard','run QSHIFT lot triage']
    state='REVIEW_RELEASE'
    public_gate=d.get('public_evidence_gate')
    if public_gate=='REFERENCE_MODE_HOLD_FOR_REAL_DATA_CLAIM':
        steps.append('flag external public-data acquisition gap; prohibit real-data performance claim')
        state='REFERENCE_MODE_HOLD'
    if life['drift_state']=='WATCH':
        steps += ['open hazard calibration slice','compare champion vs challenger','HOLD automatic release recommendation']; state='MODEL_REVIEW_HOLD'
    else:
        steps += ['run RARE-FAB risk-aware recovery scenarios','stress PHOTO/ETCH outage alternative','build supervisor shift brief']
    return {'agent':'Fab Shift Intelligence Agent','objective':'protect cycle time and queue-time constraints while preserving throughput','prediction':d.get('prediction') or d.get('predictions'),'decision':d['decision'],'decision_state':state,'chosen_tool_sequence':steps,'why_this_sequence':'hazard prediction determines whether dispatch optimization is trustworthy enough to escalate to RARE-FAB','challenge':d['counterfactual'],'ml_lifecycle':life,'operator_actions':['inspect top 10 QSHIFT lots','review RARE-FAB schedule delta','approve/HOLD release plan'],'human_authority':d['human_authority'],'autonomous_execution':False}
