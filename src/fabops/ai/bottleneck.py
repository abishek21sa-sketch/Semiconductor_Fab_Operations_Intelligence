from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class BottleneckModel:
    centroids:dict|None=None; scale:np.ndarray|None=None; metrics:dict|None=None
    def _X(self,rows): return np.array([[r["lots"],r["interarrival"],r["failure_rate"],r["repair_time"]] for r in rows],float)
    def fit(self, scenario_records:list[dict], seed:int=42)->dict:
        if len(scenario_records)<20: raise ValueError("need at least 20 scenarios")
        X=self._X(scenario_records); y=np.array([r["bottleneck"] for r in scenario_records],object)
        rng=np.random.default_rng(seed); idx=rng.permutation(len(y)); cut=max(1,int(len(y)*.75)); tr,te=idx[:cut],idx[cut:]
        self.scale=X[tr].std(0); self.scale[self.scale<1e-9]=1
        self.centroids={str(label):(X[tr][y[tr]==label]/self.scale).mean(0) for label in sorted(set(y[tr].tolist()))}
        pred=[self._predict_vec(X[i])[0] for i in te]; truth=[str(y[i]) for i in te]
        acc=sum(a==b for a,b in zip(pred,truth))/len(truth)
        labels=sorted(set(truth)|set(pred)); f1s=[]
        for lab in labels:
            tp=sum(a==lab and b==lab for a,b in zip(pred,truth)); fp=sum(a==lab and b!=lab for a,b in zip(pred,truth)); fn=sum(a!=lab and b==lab for a,b in zip(pred,truth))
            precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0
            f1s.append(2*precision*recall/(precision+recall) if precision+recall else 0)
        self.metrics={"accuracy":round(acc,3),"macro_f1":round(float(np.mean(f1s)),3),"train_n":len(tr),"test_n":len(te),
                      "estimator":"nearest_centroid_numpy","windows_stable":True}
        return self.metrics
    def _predict_vec(self,x):
        z=x/self.scale; ds={lab:float(np.linalg.norm(z-c)) for lab,c in self.centroids.items()}
        lab=min(ds,key=ds.get); vals=sorted(ds.values()); margin=(vals[1]-vals[0])/(vals[1]+1e-9) if len(vals)>1 else 1
        return lab,max(.5,min(.999,.5+.5*margin))
    def predict(self,lots:int,interarrival:float,failure_rate:float,repair_time:float)->dict:
        if self.centroids is None: raise RuntimeError("model is not fitted")
        lab,conf=self._predict_vec(np.array([lots,interarrival,failure_rate,repair_time],float))
        return {"predicted_bottleneck":lab,"confidence":round(conf,4)}
