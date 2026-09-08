from __future__ import annotations
from fabops.operations.master_data import synthetic_tool_state

def maintenance_calendar(seed:int=17,horizon_hours:int=168) -> dict:
    tools=synthetic_tool_state(seed); rows=[]
    for i,t in enumerate(tools):
        due=round(4+((i*13+seed)%max(horizon_hours-4,8)),1)
        duration=round(2+(i%4)*1.5,1)
        production_loss=round((t["utilization"]*duration)*(1+.4*t["queue"]),2)
        opportunity=round(max(0,1-t["utilization"])*.35 + t["pm_urgency"]*.65,3)
        action="EXECUTE_WINDOW" if t["pm_urgency"]>.72 and opportunity>.45 else ("PREPARE" if t["pm_urgency"]>.55 else "MONITOR")
        rows.append({"tool_id":t["tool_id"],"bay":t["bay"],"status":t["status"],"due_in_h":due,"duration_h":duration,
                     "pm_urgency":t["pm_urgency"],"availability":t["availability"],"queue":t["queue"],
                     "production_loss_proxy":production_loss,"opportunity_score":opportunity,"action":action})
    rows.sort(key=lambda x:(x["due_in_h"],-x["pm_urgency"]))
    return {"horizon_hours":horizon_hours,"calendar":rows,
            "due_24h":sum(x["due_in_h"]<=24 for x in rows),"execute_windows":sum(x["action"]=="EXECUTE_WINDOW" for x in rows)}

def setup_matrix(bay:str="PHOTO") -> dict:
    families={"PHOTO":["L1","L2","L3","L4"],"ETCH":["E1","E2","E3"],"DIFF":["D1","D2"],"CLEAN":["C1","C2"],
              "CMP":["P1","P2"],"MET":["M1","M2"],"IMPLANT":["I1","I2"],"INSPECT":["CD","DEFECT"]}
    fs=families.get(bay.upper(),["A","B"])
    matrix=[]
    for a in fs:
        row=[]
        for b in fs:
            row.append(0 if a==b else round(1.5+abs(fs.index(a)-fs.index(b))*1.25,2))
        matrix.append(row)
    return {"bay":bay.upper(),"families":fs,"changeover_hours":matrix}
