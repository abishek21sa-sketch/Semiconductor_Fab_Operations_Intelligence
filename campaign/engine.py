from collections import Counter
import math
from tenx.engine import _run_decision_core
from empirical.backbone import run_empirical_reference
SEEDS=[3,7,11,19,29,41,53]
def _entropy(vals):
    c=Counter(vals); n=len(vals); return -sum((v/n)*math.log2(v/n) for v in c.values())
def run_campaign():
    runs=[_run_decision_core(s) for s in SEEDS]; choices=[r['decision']['release_priority'] for r in runs]; c=Counter(choices); modal,n=c.most_common(1)[0]
    emp=run_empirical_reference(); m=emp.get('domain_diagnostics',{}).get('metrics',{})
    ent=_entropy(choices); stability=n/len(runs); tail=float(m.get('rare_vs_fifo_cvar90_reduction',0)); tailrn=float(m.get('tail_gain_vs_risk_neutral',0))
    state='REVIEW_RELEASE_PLAN' if stability>=0.57 and tail>0 else 'HOLD_FOR_SUPERVISOR_REVIEW'
    return {'campaign':'Rolling-Horizon Fab Campaign','campaign_identity':'ranking entropy + tail-risk recovery frontier','scenario_count':len(runs),'scenario_seeds':SEEDS,'state':state,'ranking_entropy_bits':round(ent,5),'modal_release_priority':modal,'modal_share':round(stability,4),'tail_risk_evidence':{'cvar90_reduction_vs_fifo':tail,'tail_gain_vs_risk_neutral':tailrn},'scenario_matrix':[{'seed':s,'release_priority':r['decision']['release_priority'],'ranking':r['decision']['ranking'],'brier':r['model_validation']['value']} for s,r in zip(SEEDS,runs)],'ai_synthesis':{'why':f'{modal} is modal in {n}/{len(runs)} seeded fab states; ranking entropy={ent:.3f} bits.','challenge':'If ranking entropy rises or tail-risk gain disappears, do not treat the release queue as stable.','recommended_operator_action':'Review the modal priority and disruption-sensitive alternatives in RARE-FAB before release.','abstention_conditions':['unstable ranking','negative tail-risk gain','stale fab state','tool qualification conflict']},'action_queue':['review modal lot and queue-time exposure','stress tool/reticle disruption in RARE-FAB','approve or HOLD release queue','record supervisor disposition'],'human_authority':'FAB_SHIFT_SUPERVISOR','autonomous_execution':False,'empirical_provenance':{'mode':emp.get('data_mode'),'promotion':emp.get('empirical_promotion')}}
