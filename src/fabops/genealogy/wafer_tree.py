
from __future__ import annotations
from collections import defaultdict
from fabops.data_fabric.events import ManufacturingEvent, ManufacturingEventType

def build_wafer_genealogy(events:list[ManufacturingEvent])->dict:
    lots=defaultdict(lambda:{"operations":[],"wafers":{}})
    for e in sorted(events,key=lambda x:(x.timestamp,x.event_id)):
        if not e.lot_id: continue
        lot=lots[e.lot_id]
        if e.event_type in {ManufacturingEventType.PROCESS_START,ManufacturingEventType.PROCESS_COMPLETE}:
            lot["operations"].append({"timestamp":e.timestamp,"type":e.event_type.value,"sequence":e.operation_seq,
                                      "tool_id":e.tool_id,"chamber_id":e.chamber_id,"recipe_id":e.recipe_id})
        if e.wafer_id:
            wafer=lot["wafers"].setdefault(e.wafer_id,{"wafer_id":e.wafer_id,"metrology":[],"scrapped":False})
            if e.event_type==ManufacturingEventType.METROLOGY_RESULT: wafer["metrology"].append({"timestamp":e.timestamp,**e.payload})
            if e.event_type==ManufacturingEventType.WAFER_SCRAP: wafer["scrapped"]=True
    return {"lots":{k:v for k,v in lots.items()},"lot_count":len(lots),
            "wafer_count":sum(len(v["wafers"]) for v in lots.values())}
