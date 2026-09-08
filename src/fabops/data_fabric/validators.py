
from __future__ import annotations
from collections import Counter
from fabops.data_fabric.events import ManufacturingEvent, ManufacturingEventType

LOT_REQUIRED={
 ManufacturingEventType.LOT_RELEASE,ManufacturingEventType.MOVE_START,ManufacturingEventType.MOVE_COMPLETE,
 ManufacturingEventType.PROCESS_START,ManufacturingEventType.PROCESS_COMPLETE,ManufacturingEventType.METROLOGY_RESULT,
 ManufacturingEventType.WAFER_SCRAP,ManufacturingEventType.REWORK_ROUTE
}

def validate_events(events:list[ManufacturingEvent])->dict:
    ids=[e.event_id for e in events]
    duplicates=[k for k,v in Counter(ids).items() if v>1]
    anomalies=[]
    last=-1.0
    for e in sorted(events,key=lambda x:(x.timestamp,x.event_id)):
        if e.event_type in LOT_REQUIRED and not e.lot_id:
            anomalies.append({"event_id":e.event_id,"issue":"missing_lot"})
        if e.timestamp < last:
            anomalies.append({"event_id":e.event_id,"issue":"timestamp_regression"})
        last=max(last,e.timestamp)
    return {"events":len(events),"duplicates":duplicates,"anomalies":anomalies,"valid":not duplicates and not anomalies}
