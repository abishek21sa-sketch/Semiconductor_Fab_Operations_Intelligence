# Flagship V3 Product Layer

## What V3 changes

V3 changes the project from a single control-room demonstration into a multi-workspace semiconductor operations workstation. The backend remains the source of truth. The browser calls live local API services for mission state, lot state, tool/PM state, fab topology, scheduling, AMHS, stress missions, decision packets, RARE-FAB research evidence, and Factory Physics.

## Operator workspaces

1. **Mission Control** — WIP, throughput, cycle-time tails, OTD, bay pressure, constraint migration and material alerts.
2. **Fab Map** — eight process bays, 19 reference tool assets, re-entrant links, qualification-aware reticle inventory.
3. **Lot Control** — lot route position, recipe, queue age, slack, predicted finish, hold/hot state and tardiness risk.
4. **Tool & PM Control** — utilization, availability, PM urgency, setup family, qualified recipes and queue exposure.
5. **RARE-FAB Lab** — paired risk-aware release benchmark with mean and CVaR evidence.
6. **Scheduling** — bounded rolling-horizon qualification-constrained tool assignment and recovered Gantt sequence.
7. **AMHS Network** — transfer-time tail, fleet utilization and congestion diagnostics.
8. **Digital Twin / Stress Lab** — PHOTO outage, demand surge, AMHS degradation, yield excursion and hot-lot surge missions.
9. **Decision Center** — stress evidence to ranked actions with expected recovery, confidence, evidence provenance and supervisor gate.
10. **Research & Evidence** — RARE-FAB benchmark, Factory Physics curve and explicit validation/claim boundaries.

## Semiconductor master-data expansion

The reference virtual fab now includes PHOTO, ETCH, DIFF, CLEAN, CMP, MET, IMPLANT and INSPECT bays; scanner/track/plasma/furnace/wet/polisher/PVD/implanter/metrology tool families; batch-capacity metadata; recipe qualification; reticle-to-scanner qualification; setup family; PM urgency and availability state.

This is still a **reference virtual fab**, not a claim that these assets represent any named commercial fab.

## Mathematical additions

V3 adds a bounded rolling-horizon MILP assignment layer. Binary job/tool decisions enforce process-bay and recipe qualification, one-tool-per-job assignment and per-tool horizon capacity. The objective penalizes processing, setup-family mismatch and due-date exposure. A deterministic EDD/priority list-recovery stage converts the assignment into a non-overlapping operator-readable sequence.

RARE-FAB remains the risk-aware release master using MIP + scenario CVaR. The Stress Lab supplies a separate digital-twin disturbance layer so the decision center can reason over system consequences rather than static KPI thresholds.

## Evidence state

**Implemented and locally testable:** all ten workspaces and their supporting APIs/services.

**Reference validated:** deterministic synthetic operating states, optimization feasibility, stress-mission deltas, decision provenance and paired RARE-FAB benchmark mechanics.

**Still external:** live MES/SECS-GEM feeds, proprietary route/recipe/qualification data, production IAM, real operator shadow validation, site-calibrated equipment failure/yield models, and realized production impact.
