from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parents[1]
def domain_diagnostics():
 p=ROOT/'docs/validation/portfolio_release_validation.json'; j=json.loads(p.read_text())['research_validation']; pc=j['paired_comparison']; ab=j['risk_neutral_ablation']; sens=j['sensitivity']
 best=min(sens,key=lambda x:x['cvar_loss']); neutral=[x for x in sens if x['risk_aversion']==0.0]
 return {'analysis':'fab tail-risk and risk-aversion sensitivity','metrics':{'rare_vs_fifo_mean_loss_improvement':pc['mean_improvement'],'rare_vs_fifo_cvar90_reduction':round(pc['fifo_cvar90']-pc['rare_cvar90'],4),'tail_gain_vs_risk_neutral':ab['tail_delta_neutral_minus_risk_aware'],'paired_dominance_rate':pc['dominance_rate']},'best_reference_setting':best,'decision_signal':'Use risk-aware release control when tail-risk gain is material; retain FIFO as a transparent baseline.','evidence_boundary':j['claim_boundary']}
