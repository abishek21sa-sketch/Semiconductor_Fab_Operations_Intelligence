# ADR-0002 — Bounded rolling-horizon optimization

**Decision:** use small, auditable MILP services for ready-operation assignment and lot release rather than claiming a monolithic full-fab global schedule.

**Why:** semiconductor fabs are stochastic and re-entrant. Short-horizon decisions can be re-solved frequently and compared against the digital twin; this is more defensible for the included benchmark and keeps solver requirements open-source.
