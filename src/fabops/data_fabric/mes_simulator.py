
from __future__ import annotations
import random
from fabops.data_fabric.events import ManufacturingEvent, ManufacturingEventType
from fabops.operations.genealogy import route_catalog

def generate_mes_stream(lots:int=50,wafers_per_lot:int=6,seed:int=71)->list[ManufacturingEvent]:
    rng=random.Random(seed); routes=route_catalog(); out=[]; seq=0; clock=0.0
    def emit(t,kind,**kwargs):
        nonlocal seq
        seq+=1
        out.append(ManufacturingEvent(event_id=f"MES7-{seq:08d}",timestamp=round(t,3),event_type=kind,**kwargs))
    for i in range(lots):
        lid=f"MESLOT-{i+1:04d}"; product="P1" if i%2==0 else "P2"; clock += rng.uniform(.8,2.2)
        emit(clock,ManufacturingEventType.LOT_RELEASE,lot_id=lid,payload={"product":product,"quantity":wafers_per_lot})
        for op in routes[product][:6]:
            tool=f"{op['bay']}-01"; chamber=f"{tool}-CH1"; move=rng.uniform(.2,.8)
            emit(clock+.1,ManufacturingEventType.MOVE_START,lot_id=lid,operation_seq=op["sequence"],payload={"to_bay":op["bay"]})
            clock+=move
            emit(clock,ManufacturingEventType.MOVE_COMPLETE,lot_id=lid,operation_seq=op["sequence"],payload={"bay":op["bay"]})
            if rng.random()<.025:
                emit(clock+.01,ManufacturingEventType.TOOL_DOWN,tool_id=tool,payload={"reason":"reference_fault"})
                clock+=rng.uniform(1.0,3.0)
                emit(clock,ManufacturingEventType.TOOL_UP,tool_id=tool)
            emit(clock+.05,ManufacturingEventType.PROCESS_START,lot_id=lid,tool_id=tool,chamber_id=chamber,
                 recipe_id=op["recipe"],operation_seq=op["sequence"])
            clock+=float(op["process_time"])*.18
            emit(clock,ManufacturingEventType.PROCESS_COMPLETE,lot_id=lid,tool_id=tool,chamber_id=chamber,
                 recipe_id=op["recipe"],operation_seq=op["sequence"])
            if op["bay"]=="INSPECT":
                for w in range(wafers_per_lot):
                    wid=f"{lid}-W{w+1:02d}"; val=100+rng.gauss(0,1.1)+(1.8 if i%17==0 else 0)
                    emit(clock+.01+w*.001,ManufacturingEventType.METROLOGY_RESULT,lot_id=lid,wafer_id=wid,tool_id=tool,
                         operation_seq=op["sequence"],payload={"metric":"cd_nm","value":round(val,4),"target":100.0})
    return sorted(out,key=lambda e:(e.timestamp,e.event_id))
