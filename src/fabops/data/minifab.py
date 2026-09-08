from __future__ import annotations
import random
from fabops.domain.models import FabConfig, Lot, Operation, ProductRoute, Tool

# A compact re-entrant benchmark inspired by the Intel/ASU MiniFab structure.
# It is not represented as proprietary fab data.
def build_minifab_config() -> FabConfig:
    routes = {
        "P1": ProductRoute("P1", (
            Operation(1,"LITHO",10,"L1"), Operation(2,"ETCH",8,"E1"),
            Operation(3,"DIFF",12,"D1"), Operation(4,"LITHO",9,"L2"),
            Operation(5,"ETCH",7,"E2"), Operation(6,"METROLOGY",4,"M1"),
        )),
        "P2": ProductRoute("P2", (
            Operation(1,"LITHO",11,"L1"), Operation(2,"DIFF",13,"D2"),
            Operation(3,"ETCH",9,"E1"), Operation(4,"LITHO",10,"L2"),
            Operation(5,"DIFF",11,"D1"), Operation(6,"METROLOGY",5,"M1"),
        )),
    }
    tools = (
        Tool("LITHO-01","LITHO",frozenset({"L1","L2"})),
        Tool("LITHO-02","LITHO",frozenset({"L1","L2"})),
        Tool("ETCH-01","ETCH",frozenset({"E1","E2"})),
        Tool("DIFF-01","DIFF",frozenset({"D1","D2"})),
        Tool("DIFF-02","DIFF",frozenset({"D1","D2"})),
        Tool("MET-01","METROLOGY",frozenset({"M1"})),
    )
    return FabConfig(routes=routes, tools=tools, setup_time=2.0)

def generate_lots(n: int = 40, seed: int = 7, interarrival: float = 6.0) -> list[Lot]:
    rng = random.Random(seed)
    lots=[]
    t=0.0
    for i in range(n):
        t += rng.expovariate(1.0/interarrival)
        product = "P1" if rng.random() < 0.55 else "P2"
        nominal = 50.0 if product == "P1" else 59.0
        due = t + nominal * rng.uniform(2.1, 3.2)
        priority = 3 if rng.random() < 0.12 else (2 if rng.random() < 0.25 else 1)
        lots.append(Lot(f"LOT-{i+1:04d}", product, round(t,3), round(due,3), priority=priority))
    return lots
