# Flagship V2 — Semiconductor Autonomous Operations Lab

This release promotes the repository from an end-to-end demo platform to a semiconductor-native operations laboratory. It preserves the constitution's event/state/simulation/AI/optimization architecture and adds a distinct control hierarchy.

## Control hierarchy
1. **Evidence boundary** — FILE/REPLAY/API events remain distinct from synthetic benchmark evidence.
2. **State reconstruction** — wafer/tool state is reconstructed before decisions.
3. **Bay intelligence** — `FAB_BAY_RISK_HEATMAP` combines WIP, utilization, queue age, AMHS delay, energy and maintenance risk.
4. **RARE-FAB 2.0 master** — assigns candidate lot releases over a rolling horizon with workload/WIP feasibility and CVaR scenario risk.
5. **Dispatch/execution layer** — existing dispatch and assignment engines execute only approved near-term actions.
6. **Digital-twin challenge** — Monte Carlo/scenario replay challenges the proposed policy.
7. **Human disposition** — fab shift supervisor approval remains mandatory for operational action.

## Semiconductor-specific additions
- Re-entrant workload capacities by bay/tool group.
- Explicit AMHS contention proxy.
- Equipment availability, PM urgency, setup pressure and qualification coverage.
- Yield excursion/rework feedback.
- Factory Physics queue approximation and operating curves.
- Tail-risk scenario terms for queue, AMHS, energy, maintenance and qualification.

## Research discipline
RARE-FAB is an original project-specific engineering synthesis, not claimed as a new theorem. The benchmark harness reports common-random-number synthetic evidence, dominance, mean/tail loss and runtime. External/site validation remains a hard boundary.
