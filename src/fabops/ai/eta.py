from __future__ import annotations
from dataclasses import dataclass
import numpy as np

def _mae(y,p): return float(np.mean(np.abs(np.asarray(y)-np.asarray(p))))

@dataclass
class ETAModel:
    beta:np.ndarray|None=None; mean:np.ndarray|None=None; scale:np.ndarray|None=None; metrics:dict|None=None
    def fit(self, records:list[dict], seed:int=42)->dict:
        if len(records)<20: raise ValueError("need at least 20 records")
        X=np.array([[r["priority"],r["release_time"],r["queue_time"],1 if r["product"]=="P2" else 0] for r in records],float)
        y=np.array([r["completion_time"] for r in records],float)
        groups=np.array([int(r["lot_id"].split("-")[-1])//5 for r in records])
        ug=np.unique(groups); rng=np.random.default_rng(seed); ug=rng.permutation(ug); nte=max(1,int(np.ceil(len(ug)*.25)))
        test_groups=set(ug[:nte].tolist()); te=np.array([g in test_groups for g in groups]); tr=~te
        self.mean=X[tr].mean(0); self.scale=X[tr].std(0); self.scale[self.scale<1e-9]=1
        A=np.c_[np.ones(tr.sum()),(X[tr]-self.mean)/self.scale]; self.beta=np.linalg.lstsq(A,y[tr],rcond=None)[0]
        pred=np.c_[np.ones(te.sum()),(X[te]-self.mean)/self.scale]@self.beta; naive=np.full(te.sum(),float(y[tr].mean()))
        self.metrics={"mae":round(_mae(y[te],pred),3),"naive_mae":round(_mae(y[te],naive),3),
                      "train_n":int(tr.sum()),"test_n":int(te.sum()),"validation":"grouped_holdout",
                      "estimator":"standardized_ols_numpy","windows_stable":True}
        return self.metrics
    def predict(self, record:dict)->float:
        if self.beta is None: raise RuntimeError("model is not fitted")
        x=np.array([record["priority"],record["release_time"],record["queue_time"],1 if record["product"]=="P2" else 0],float)
        return round(float(np.r_[1,(x-self.mean)/self.scale]@self.beta),3)
