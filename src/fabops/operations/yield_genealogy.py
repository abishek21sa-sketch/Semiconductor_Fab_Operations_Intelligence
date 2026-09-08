from __future__ import annotations
from math import exp, sin

def yield_genealogy(seed:int=17,count:int=24) -> dict:
    lots=[]; total_rework=0; total_scrap=0
    for i in range(count):
        product="P1" if i%2==0 else "P2"; dd=.012+.018*abs(sin((i+seed)*.47)); area=1.0+(i%4)*.08
        base=exp(-dd*area); excursion=max(0,min(.98,.10+.65*abs(sin((i+seed)*.31)) + (.12 if i%11==0 else 0)))
        pred=max(.45,min(.995,base*(1-.18*excursion))); wafers=25; good=round(wafers*pred,1)
        rework=round((wafers-good)*(.55 if excursion>.5 else .25),1); scrap=round(max(0,wafers-good-rework),1)
        total_rework+=rework; total_scrap+=scrap
        disposition="HOLD_ENGINEERING" if excursion>.72 else ("REWORK_ROUTE" if excursion>.48 else "CONTINUE")
        lots.append({"lot_id":f"LOT-{i+1:03d}","product":product,"predicted_yield":round(pred,4),
                     "excursion_probability":round(excursion,4),"expected_good_wafers":good,"rework_wafers":rework,
                     "scrap_wafers":scrap,"disposition":disposition,"return_bay":"CLEAN" if disposition=="REWORK_ROUTE" else None})
    return {"lots":lots,"mean_predicted_yield":round(sum(x["predicted_yield"] for x in lots)/len(lots),4),
            "rework_load_wafers":round(total_rework,1),"expected_scrap_wafers":round(total_scrap,1),
            "engineering_holds":sum(x["disposition"]=="HOLD_ENGINEERING" for x in lots)}
