from __future__ import annotations
from fabops.domain.models import Lot

def _remaining_work(lot: Lot, route) -> float:
    return sum(op.process_time for op in route.operations[lot.step_index:])

def select_lot(candidates: list[Lot], now: float, route_lookup, rule: str = "FIFO") -> Lot:
    if not candidates:
        raise ValueError("candidates must not be empty")
    rule = rule.upper()
    if rule == "FIFO":
        key=lambda l:(l.queue_enter_time,l.release_time,l.lot_id)
    elif rule == "EDD":
        key=lambda l:(l.due_time,-l.priority,l.queue_enter_time)
    elif rule == "SPT":
        key=lambda l:(route_lookup(l.product).operations[l.step_index].process_time,l.due_time)
    elif rule == "CR":
        def key(l):
            rem=max(_remaining_work(l,route_lookup(l.product)),1e-9)
            return ((l.due_time-now)/rem,-l.priority,l.queue_enter_time)
    elif rule == "PRIORITY":
        key=lambda l:(-l.priority,l.due_time,l.queue_enter_time)
    else:
        raise ValueError(f"unknown dispatch rule: {rule}")
    return min(candidates,key=key)
