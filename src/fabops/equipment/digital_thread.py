
from __future__ import annotations
from collections import defaultdict
from fabops.data_fabric.events import ManufacturingEvent, ManufacturingEventType

def build_equipment_threads(events:list[ManufacturingEvent])->dict:
    state=defaultdict(lambda:{"state":"UP","process_count":0,"down_events":0,"pm_events":0,"recipes":set(),"chambers":set(),"alarms":0})
    for e in events:
        if not e.tool_id: continue
        s=state[e.tool_id]
        if e.recipe_id: s["recipes"].add(e.recipe_id)
        if e.chamber_id: s["chambers"].add(e.chamber_id)
        if e.event_type==ManufacturingEventType.PROCESS_START: s["state"]="BUSY"; s["process_count"]+=1
        elif e.event_type==ManufacturingEventType.PROCESS_COMPLETE: s["state"]="UP"
        elif e.event_type==ManufacturingEventType.TOOL_DOWN: s["state"]="DOWN"; s["down_events"]+=1
        elif e.event_type==ManufacturingEventType.TOOL_UP: s["state"]="UP"
        elif e.event_type==ManufacturingEventType.PM_START: s["state"]="PM"; s["pm_events"]+=1
        elif e.event_type==ManufacturingEventType.PM_COMPLETE: s["state"]="UP"
        elif e.event_type==ManufacturingEventType.ALARM_TRIGGER: s["alarms"]+=1
    out={}
    for tool,s in state.items():
        health=max(0.0,1-.10*s["down_events"]-.035*s["alarms"]-.01*max(0,s["process_count"]-25))
        out[tool]={**s,"recipes":sorted(s["recipes"]),"chambers":sorted(s["chambers"]),"health_score":round(health,3),
                   "failure_probability":round(min(.95,.03+.12*s["down_events"]+.04*s["alarms"]),3)}
    return {"tools":out,"count":len(out)}
