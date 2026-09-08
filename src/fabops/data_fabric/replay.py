
from __future__ import annotations
from collections import defaultdict
from fabops.data_fabric.events import ManufacturingEvent, ManufacturingEventType

def replay_manufacturing_state(events:list[ManufacturingEvent])->dict:
    lots={}; tools={}; wafers={}; alarms=[]
    for e in sorted(events,key=lambda x:(x.timestamp,x.event_id)):
        if e.lot_id:
            lot=lots.setdefault(e.lot_id,{"lot_id":e.lot_id,"state":"UNKNOWN","tool_id":None,"operation_seq":0,"last_timestamp":0.0})
            lot["last_timestamp"]=e.timestamp
            if e.operation_seq: lot["operation_seq"]=e.operation_seq
            if e.event_type==ManufacturingEventType.LOT_RELEASE: lot["state"]="RELEASED"
            elif e.event_type==ManufacturingEventType.MOVE_START: lot["state"]="IN_TRANSIT"
            elif e.event_type==ManufacturingEventType.MOVE_COMPLETE: lot["state"]="QUEUED"
            elif e.event_type==ManufacturingEventType.PROCESS_START: lot["state"]="PROCESSING"; lot["tool_id"]=e.tool_id
            elif e.event_type==ManufacturingEventType.PROCESS_COMPLETE: lot["state"]="QUEUED"; lot["tool_id"]=None
            elif e.event_type==ManufacturingEventType.REWORK_ROUTE: lot["state"]="REWORK"
        if e.tool_id:
            tool=tools.setdefault(e.tool_id,{"tool_id":e.tool_id,"state":"UP","current_lot":None,"last_timestamp":0.0})
            tool["last_timestamp"]=e.timestamp
            if e.event_type==ManufacturingEventType.TOOL_DOWN: tool["state"]="DOWN"
            elif e.event_type==ManufacturingEventType.TOOL_UP: tool["state"]="UP"
            elif e.event_type==ManufacturingEventType.PM_START: tool["state"]="PM"
            elif e.event_type==ManufacturingEventType.PM_COMPLETE: tool["state"]="UP"
            elif e.event_type==ManufacturingEventType.PROCESS_START: tool["state"]="BUSY"; tool["current_lot"]=e.lot_id
            elif e.event_type==ManufacturingEventType.PROCESS_COMPLETE: tool["state"]="UP"; tool["current_lot"]=None
        if e.wafer_id:
            w=wafers.setdefault(e.wafer_id,{"wafer_id":e.wafer_id,"lot_id":e.lot_id,"metrology":[],"scrapped":False})
            if e.event_type==ManufacturingEventType.METROLOGY_RESULT: w["metrology"].append(e.payload)
            if e.event_type==ManufacturingEventType.WAFER_SCRAP: w["scrapped"]=True
        if e.event_type==ManufacturingEventType.ALARM_TRIGGER:
            alarms.append({"timestamp":e.timestamp,"tool_id":e.tool_id,"payload":e.payload})
    return {"lots":lots,"tools":tools,"wafers":wafers,"alarms":alarms,
            "counts":{"lots":len(lots),"tools":len(tools),"wafers":len(wafers),"alarms":len(alarms)}}
