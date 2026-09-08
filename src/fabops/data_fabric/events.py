
from __future__ import annotations
from enum import Enum
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class ManufacturingEventType(str, Enum):
    LOT_RELEASE="lot_release"
    MOVE_START="move_start"
    MOVE_COMPLETE="move_complete"
    PROCESS_START="process_start"
    PROCESS_COMPLETE="process_complete"
    METROLOGY_RESULT="metrology_result"
    ALARM_TRIGGER="alarm_trigger"
    PM_START="pm_start"
    PM_COMPLETE="pm_complete"
    TOOL_DOWN="tool_down"
    TOOL_UP="tool_up"
    WAFER_SCRAP="wafer_scrap"
    REWORK_ROUTE="rework_route"

class ManufacturingEvent(BaseModel):
    model_config=ConfigDict(extra="forbid")
    event_id:str=Field(min_length=4)
    timestamp:float=Field(ge=0)
    source:str="mes_simulator"
    event_type:ManufacturingEventType
    lot_id:str|None=None
    wafer_id:str|None=None
    tool_id:str|None=None
    chamber_id:str|None=None
    recipe_id:str|None=None
    operation_seq:int|None=Field(default=None, ge=1)
    payload:dict[str,Any]=Field(default_factory=dict)
    ingested_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
