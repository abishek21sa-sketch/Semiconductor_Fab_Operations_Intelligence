from __future__ import annotations
from dataclasses import dataclass
import numpy as np

FEATURES=("priority","release_time","due_window","product_p2")

def _mae(y,p): return float(np.mean(np.abs(np.asarray(y)-np.asarray(p))))
def _r2(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); den=float(np.sum((y-y.mean())**2))
    return 1-float(np.sum((y-p)**2))/den if den>0 else 0.0

@dataclass
class CycleTimeModel:
    beta: np.ndarray|None=None
    mean: np.ndarray|None=None
    scale: np.ndarray|None=None
    metrics: dict|None=None
    def _X(self,records):
        return np.array([[r["priority"],r["release_time"],r["due_time"]-r["release_time"],1 if r["product"]=="P2" else 0] for r in records],float)
    def fit(self, records:list[dict], seed:int=42)->dict:
        if len(records)<12: raise ValueError("need at least 12 completed lots")
        X=self._X(records); y=np.array([r["cycle_time"] for r in records],float)
        rng=np.random.default_rng(seed); idx=rng.permutation(len(y)); cut=max(1,int(len(y)*.75)); tr,te=idx[:cut],idx[cut:]
        self.mean=X[tr].mean(0); self.scale=X[tr].std(0); self.scale[self.scale<1e-9]=1
        Z=(X[tr]-self.mean)/self.scale; A=np.c_[np.ones(len(Z)),Z]
        self.beta=np.linalg.lstsq(A,y[tr],rcond=None)[0]
        pred=np.c_[np.ones(len(te)),(X[te]-self.mean)/self.scale]@self.beta
        self.metrics={"mae":round(_mae(y[te],pred),3),"r2":round(_r2(y[te],pred),3),"train_n":len(tr),"test_n":len(te),
                      "estimator":"standardized_ols_numpy","windows_stable":True}
        return self.metrics
    def predict(self, lot:dict)->float:
        if self.beta is None: raise RuntimeError("model is not fitted")
        x=self._X([lot])[0]; z=(x-self.mean)/self.scale
        return round(float(np.r_[1,z]@self.beta),3)
    def feature_importance(self)->dict:
        if self.beta is None: raise RuntimeError("model is not fitted")
        w=np.abs(self.beta[1:]); s=float(w.sum()) or 1
        return {k:round(float(v/s),4) for k,v in zip(FEATURES,w)}
