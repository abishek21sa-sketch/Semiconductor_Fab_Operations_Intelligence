from __future__ import annotations
import math, json
from dataclasses import dataclass
import numpy as np

class CoxHazardLearner:
    """Small Cox PH learner implemented in-repository with partial-likelihood gradient ascent."""
    def __init__(self, steps=180, lr=.035, l2=.01): self.steps,self.lr,self.l2=steps,lr,l2
    def fit(self,X,t,event):
        X=np.asarray(X,float); t=np.asarray(t,float); event=np.asarray(event,int)
        self.mu=X.mean(0); self.sd=X.std(0)+1e-9; Z=(X-self.mu)/self.sd; b=np.zeros(Z.shape[1])
        for _ in range(self.steps):
            xb=np.clip(Z@b,-18,18); ex=np.exp(xb); g=np.zeros_like(b); n=max(1,int(event.sum()))
            for i in np.where(event==1)[0]:
                mask=t>=t[i]; denom=ex[mask].sum()+1e-12
                g += Z[i] - (Z[mask]*ex[mask,None]).sum(0)/denom
            b += self.lr*(g/n-self.l2*b)
        self.beta=b; xb=np.clip(Z@b,-18,18); ex=np.exp(xb); self.base=[]; ch=0.0
        for ti in sorted(set(t[event==1])):
            d=((t==ti)&(event==1)).sum(); risk=ex[t>=ti].sum()+1e-12; ch += d/risk; self.base.append((float(ti),float(ch)))
        return self
    def risk(self,x,horizon):
        z=(np.asarray(x,float)-self.mu)/self.sd; mult=math.exp(float(np.clip(z@self.beta,-18,18))); h0=0.0
        for t,h in self.base:
            if t<=horizon: h0=h
        return 1-math.exp(-h0*mult)

class QSHIFT:
    """Queue-Slack Hazard Integrated Fab Triage. No external optimizer; deterministic authored policy."""
    def score(self,lot):
        slack=float(lot['due_slack_h']); risk=float(lot['predicted_breach_risk']); age=float(lot['queue_age_h']); crit=float(lot.get('criticality',1))
        urgency=1/(1+math.exp(slack/5.0)); starvation=1-math.exp(-max(age,0)/18.0)
        # starvation floor grows sharply for very old lots, preventing silent starvation.
        starvation_guard=max(0.0,(age-30.0)/20.0)
        return 4.0*risk + 2.2*urgency + 1.6*starvation + 1.4*starvation_guard + .35*crit
    def rank(self,lots): return sorted([{**x,'qshift_score':self.score(x)} for x in lots],key=lambda x:(-x['qshift_score'],x['due_slack_h'],x['lot_id']))

def _training(seed=17,n=180):
    r=np.random.default_rng(seed); X=[]; t=[]; e=[]
    for _ in range(n):
        q=r.uniform(0,42); util=r.uniform(.45,1.08); re=r.uniform(0,.6); pm=r.uniform(0,1); amhs=r.uniform(0,1)
        lin=-2.3+.055*q+2.1*max(util-.72,0)+1.2*re+.8*pm+.7*amhs; p=1/(1+math.exp(-lin)); ev=int(r.random()<p)
        tt=r.uniform(2,18) if ev else r.uniform(12,48); X.append([q,util,re,pm,amhs]); t.append(tt); e.append(ev)
    return np.array(X),np.array(t),np.array(e)

def _run_decision_core(seed=23):
    X,t,e=_training(seed); model=CoxHazardLearner().fit(X,t,e); Xh,th,eh=_training(seed+101,70); ph=np.array([model.risk(x,12) for x in Xh]); yh=((eh==1)&(th<=12)).astype(float); brier=float(np.mean((ph-yh)**2))
    lots=[
      {'lot_id':'L-ETCH-17','queue_age_h':31,'utilization':.96,'rework':.15,'pm_risk':.2,'amhs_risk':.45,'due_slack_h':5,'criticality':2},
      {'lot_id':'L-PHOTO-08','queue_age_h':14,'utilization':1.03,'rework':.4,'pm_risk':.65,'amhs_risk':.25,'due_slack_h':10,'criticality':3},
      {'lot_id':'L-DIFF-04','queue_age_h':8,'utilization':.72,'rework':.05,'pm_risk':.1,'amhs_risk':.1,'due_slack_h':1,'criticality':1},]
    for lot in lots: lot['predicted_breach_risk']=model.risk([lot['queue_age_h'],lot['utilization'],lot['rework'],lot['pm_risk'],lot['amhs_risk']],12)
    ranked=QSHIFT().rank(lots); edf=min(lots,key=lambda x:x['due_slack_h'])
    return {'project':'Semiconductor Fab Operations Intelligence','ml_family':'Cox proportional-hazards survival learning','prediction_target':'12-hour queue-time breach probability','model_validation':{'metric':'Brier score','value':brier,'direction':'lower_is_better','split':'independent synthetic holdout'},'predictions':[{k:x[k] for k in ('lot_id','predicted_breach_risk')} for x in lots], 'original_algorithm':'QSHIFT-v1','decision':{'release_priority':ranked[0]['lot_id'],'ranking':[x['lot_id'] for x in ranked]},'counterfactual':{'naive_policy':'earliest due slack','choice':edf['lot_id'],'disagrees':edf['lot_id']!=ranked[0]['lot_id']},'uncertainty':'Cox model is reference-trained; production calibration requires fab history.','or_escalation':'Send ranked/high-risk set to RARE-FAB stochastic scheduling + CVaR release control.','tool_trace':['fit survival hazard model','predict lot breach probabilities','rank with QSHIFT','challenge EDF','escalate to RARE-FAB'],'limitations':['synthetic/reference training in bundled demo','not connected to production MES'], 'abstention_conditions':['missing queue state','hazard calibration drift','stale MES snapshot'],'user_aid':['review top-risk lot passport','compare QSHIFT vs EDF','approve/hold RARE-FAB release plan'],'human_authority':'FAB_SHIFT_SUPERVISOR','autonomous_execution':False}


def run_decision(seed=None):
    from empirical.backbone import run_empirical_reference
    import inspect
    sig=inspect.signature(_run_decision_core)
    if seed is None:
        out=_run_decision_core()
    else:
        out=_run_decision_core(seed)
    emp=run_empirical_reference()
    out["empirical_backbone"]=emp
    from empirical.public_data_backbone import integrate_decision
    out=integrate_decision(out)
    out.setdefault("tool_trace",[]).insert(0,"resolve empirical data provenance and source mode")
    out.setdefault("user_aid",[]).append("open empirical case study and entity/history drilldowns before approval")
    return out
