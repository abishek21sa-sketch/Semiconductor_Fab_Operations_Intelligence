from __future__ import annotations
from dataclasses import dataclass, asdict, field
from fabops.ingestion.events import FabEvent, FabEventType

@dataclass
class LotState:
    lot_id: str
    product: str | None = None
    status: str = "unknown"
    current_step: int = 0
    current_tool: str | None = None
    quantity: int = 25
    released_at: float | None = None
    last_event_at: float = 0.0
    hold_reason: str | None = None
    completed_steps: int = 0
    history: list[str] = field(default_factory=list)

@dataclass
class ToolState:
    tool_id: str
    status: str = "idle"
    current_lot: str | None = None
    current_recipe: str | None = None
    last_event_at: float = 0.0

@dataclass
class FabSnapshot:
    as_of: float
    lots: dict[str, LotState]
    tools: dict[str, ToolState]
    anomalies: list[str]

    def to_dict(self) -> dict:
        return {
            "as_of": self.as_of,
            "lots": {k: asdict(v) for k,v in self.lots.items()},
            "tools": {k: asdict(v) for k,v in self.tools.items()},
            "anomalies": list(self.anomalies),
            "wip": sum(1 for l in self.lots.values() if l.status not in {"completed","scrapped"}),
        }

class WaferStateEngine:
    """Deterministically reconstruct lot/tool state from canonical events.

    The engine is intentionally event-sourced: a snapshot is derived from an ordered log,
    making state reconstruction auditable and replayable.
    """
    def reconstruct(self, events: list[FabEvent], as_of: float | None = None) -> FabSnapshot:
        lots: dict[str, LotState] = {}
        tools: dict[str, ToolState] = {}
        anomalies: list[str] = []
        ordered = sorted((e for e in events if as_of is None or e.timestamp <= as_of), key=lambda e:(e.timestamp,e.event_id))
        seen=set()
        for e in ordered:
            if e.event_id in seen:
                anomalies.append(f"duplicate_event:{e.event_id}")
                continue
            seen.add(e.event_id)
            if e.tool_id and e.tool_id not in tools:
                tools[e.tool_id]=ToolState(e.tool_id)
            if e.lot_id and e.lot_id not in lots:
                lots[e.lot_id]=LotState(e.lot_id, product=e.product, quantity=e.quantity)
            lot=lots.get(e.lot_id) if e.lot_id else None
            tool=tools.get(e.tool_id) if e.tool_id else None
            if lot and e.timestamp < lot.last_event_at:
                anomalies.append(f"out_of_order_lot_event:{e.event_id}")
            if e.event_type == FabEventType.LOT_RELEASED and lot:
                lot.product=e.product or lot.product; lot.status="released"; lot.released_at=e.timestamp
            elif e.event_type == FabEventType.QUEUED and lot:
                lot.status="queued"; lot.current_step=e.step or lot.current_step; lot.current_tool=None
            elif e.event_type == FabEventType.PROCESS_STARTED and lot:
                lot.status="processing"; lot.current_step=e.step or lot.current_step; lot.current_tool=e.tool_id
                if tool:
                    if tool.status == "busy" and tool.current_lot != lot.lot_id:
                        anomalies.append(f"tool_double_booked:{e.tool_id}:{e.event_id}")
                    tool.status="busy"; tool.current_lot=lot.lot_id; tool.current_recipe=e.recipe or tool.current_recipe
            elif e.event_type == FabEventType.PROCESS_COMPLETED and lot:
                lot.status="queued"; lot.current_step=e.step or lot.current_step; lot.completed_steps=max(lot.completed_steps, e.step or 0); lot.current_tool=None
                if e.payload.get("route_complete"):
                    lot.status="completed"
                if tool:
                    tool.status="idle"; tool.current_lot=None
            elif e.event_type == FabEventType.TOOL_DOWN and tool:
                tool.status="down"
            elif e.event_type == FabEventType.TOOL_UP and tool:
                tool.status="idle"; tool.current_lot=None
            elif e.event_type == FabEventType.HOLD_STARTED and lot:
                lot.status="hold"; lot.hold_reason=str(e.payload.get("reason","unspecified"))
            elif e.event_type == FabEventType.HOLD_RELEASED and lot:
                lot.status="queued"; lot.hold_reason=None
            elif e.event_type == FabEventType.SCRAPPED and lot:
                lot.status="scrapped"; lot.quantity=0; lot.current_tool=None
            if lot:
                lot.last_event_at=max(lot.last_event_at,e.timestamp); lot.history.append(e.event_id)
            if tool:
                tool.last_event_at=max(tool.last_event_at,e.timestamp)
        asof = as_of if as_of is not None else (ordered[-1].timestamp if ordered else 0.0)
        return FabSnapshot(asof,lots,tools,anomalies)
