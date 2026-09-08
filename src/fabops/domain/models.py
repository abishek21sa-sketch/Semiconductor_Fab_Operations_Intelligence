from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

class ToolStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DOWN = "down"

@dataclass(frozen=True)
class Operation:
    step: int
    tool_group: str
    process_time: float
    recipe: str

@dataclass(frozen=True)
class ProductRoute:
    product: str
    operations: tuple[Operation, ...]

@dataclass
class Lot:
    lot_id: str
    product: str
    release_time: float
    due_time: float
    priority: int = 1
    step_index: int = 0
    queue_enter_time: float = 0.0
    start_time: float | None = None
    completion_time: float | None = None
    total_queue_time: float = 0.0
    history: list[dict] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.completion_time is not None

@dataclass
class Tool:
    tool_id: str
    tool_group: str
    qualified_recipes: frozenset[str]
    status: ToolStatus = ToolStatus.IDLE
    available_at: float = 0.0
    current_recipe: str | None = None
    busy_time: float = 0.0
    setup_time: float = 0.0

@dataclass(frozen=True)
class FabConfig:
    routes: dict[str, ProductRoute]
    tools: tuple[Tool, ...]
    setup_time: float = 2.0

    def route(self, product: str) -> ProductRoute:
        return self.routes[product]

    def tools_for(self, group: str, recipe: str) -> Iterable[Tool]:
        return (t for t in self.tools if t.tool_group == group and recipe in t.qualified_recipes)
