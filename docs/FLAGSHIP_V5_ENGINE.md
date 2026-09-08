# FLAGSHIP V5 — Integrated Fab Engine

V5 moves the project from tool-level operational views toward semiconductor execution mechanics.

## Windows hardening
The predictive services no longer use scikit-learn at runtime. Cycle-time and ETA models use standardized NumPy OLS, and bottleneck prediction uses a NumPy nearest-centroid classifier. The official Windows acceptance disables pytest's faulthandler/color wrappers while preserving strict non-zero exit-code failure behavior and constrains numerical thread counts.

## Semiconductor engine additions
- 27 chamber-level states derived from the 19-tool virtual fab.
- Furnace/wet-bench batch formation with batch capacity and maximum waiting policy.
- Reticle-contention serialization for lithography requests.
- Qualification matrix exposing tool recipes, chamber count, and batch capacity.
- Time-indexed MILP scheduling with:
  - qualified tool assignment,
  - hard queue-time latest-start constraints,
  - tool non-overlap,
  - preventive-maintenance blocking windows,
  - shared-reticle capacity,
  - due-date and priority costs.
- Finite-scenario mean + CVaR recovery optimization across outage, demand, AMHS, yield, and reticle-risk dimensions.

## Product workspaces
V5 adds Chambers & Batching and Stochastic Recovery to the V4 workstation, and upgrades Scheduling to the integrated queue/PM/reticle-aware solve.

## Evidence boundary
All V5 quantitative outputs are reference virtual-fab evidence. They are not production-site telemetry, site-calibrated model accuracy, realized savings, or autonomous equipment-control claims.
