
from __future__ import annotations
from math import sqrt
from statistics import mean, pstdev

def shewhart(values:list[float],sigma:float=3.0)->dict:
    if len(values)<5: raise ValueError("need at least 5 observations")
    mu=mean(values); sd=pstdev(values) or 1e-9; ucl=mu+sigma*sd; lcl=mu-sigma*sd
    signals=[i for i,x in enumerate(values) if x>ucl or x<lcl]
    return {"mean":round(mu,4),"std":round(sd,4),"ucl":round(ucl,4),"lcl":round(lcl,4),"signals":signals}

def ewma(values:list[float],lam:float=.25)->dict:
    if not values: raise ValueError("values required")
    z=values[0]; series=[z]
    for x in values[1:]:
        z=lam*x+(1-lam)*z; series.append(z)
    baseline=mean(values[:max(3,len(values)//3)])
    drift=series[-1]-baseline
    return {"lambda":lam,"series":[round(x,4) for x in series],"baseline":round(baseline,4),
            "drift":round(drift,4),"state":"DRIFT" if abs(drift)>.8 else "STABLE"}

def cusum(values:list[float],target:float,k:float=.5,h:float=4.0)->dict:
    pos=neg=0.0; signals=[]
    for i,x in enumerate(values):
        pos=max(0,pos+x-target-k); neg=min(0,neg+x-target+k)
        if pos>h or abs(neg)>h: signals.append(i); pos=neg=0.0
    return {"target":target,"signals":signals,"state":"ALARM" if signals else "STABLE"}

def analyze_metrology(values:list[float],target:float=100.0)->dict:
    sh=shewhart(values); ew=ewma(values); cu=cusum(values,target)
    return {"shewhart":sh,"ewma":ew,"cusum":cu,
            "overall_state":"ALARM" if sh["signals"] or cu["signals"] or ew["state"]=="DRIFT" else "STABLE"}
