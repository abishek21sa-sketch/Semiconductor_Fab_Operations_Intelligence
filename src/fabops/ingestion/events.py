from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class FabEventType(str, Enum):
    LOT_RELEASED = "lot_released"
    QUEUED = "queued"
    PROCESS_STARTED = "process_started"
    PROCESS_COMPLETED = "process_completed"
    TOOL_DOWN = "tool_down"
    TOOL_UP = "tool_up"
    HOLD_STARTED = "hold_started"
    HOLD_RELEASED = "hold_released"
    SCRAPPED = "scrapped"

class FabEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=3)
    event_type: FabEventType
    timestamp: float = Field(ge=0)
    lot_id: str | None = None
    tool_id: str | None = None
    product: str | None = None
    step: int | None = Field(default=None, ge=1)
    recipe: str | None = None
    quantity: int = Field(default=25, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "synthetic_mes"
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("lot_id")
    @classmethod
    def validate_lot_for_lot_events(cls, v: str | None, info):
        et = info.data.get("event_type")
        if et in {
            FabEventType.LOT_RELEASED, FabEventType.QUEUED, FabEventType.PROCESS_STARTED,
            FabEventType.PROCESS_COMPLETED, FabEventType.HOLD_STARTED,
            FabEventType.HOLD_RELEASED, FabEventType.SCRAPPED,
        } and not v:
            raise ValueError("lot_id is required for lot events")
        return v


def normalize_simulation_log(event_log: list[dict]) -> list[FabEvent]:
    """Convert simulator events into a strict MES-like canonical contract."""
    out: list[FabEvent] = []
    seq = 0
    mapping = {
        "release": FabEventType.LOT_RELEASED,
        "start": FabEventType.PROCESS_STARTED,
        "finish": FabEventType.PROCESS_COMPLETED,
    }
    for raw in event_log:
        kind = raw.get("event")
        if kind not in mapping:
            continue
        seq += 1
        out.append(FabEvent(
            event_id=f"SIM-{seq:08d}",
            event_type=mapping[kind],
            timestamp=float(raw["time"]),
            lot_id=raw.get("lot_id"),
            tool_id=raw.get("tool_id"),
            product=raw.get("product"),
            step=raw.get("step"),
            payload={k: v for k, v in raw.items() if k not in {"time","event","lot_id","tool_id","product","step"}},
        ))
    return out
