# Validation Protocol

Validation is reproducible and explicitly scoped to the included synthetic benchmark.

## Software validation

`python -m pytest` verifies domain behavior, deterministic simulation, dispatch selection, optimization constraints, ingestion, state replay, persistence, predictive services, Factory Physics analytics and API contracts.

`python -m compileall -q src scripts` provides an additional syntax/importability gate.

## Quantitative validation

`python scripts/run_validation.py` regenerates `docs/validation/validation_results.json` using fixed reference seeds plus a 12-replication Monte Carlo disruption experiment.

Operational evidence includes throughput, makespan, average/P95 cycle time, tardiness, on-time rate, WIP, utilization, bottleneck ranking, Little's Law diagnostics, operational risk and dispatch-policy comparisons.

Predictive evidence includes cycle-time MAE/R², ETA grouped-holdout MAE versus a naive baseline, and bottleneck classification accuracy/macro-F1 on generated scenario records.

Optimization evidence includes qualification-constrained parallel-tool assignment and capacity-constrained lot-release plans.

State evidence includes canonical event count, reconstructed lots/tools, WIP and replay anomalies.

## Evidence boundary

No benchmark result is generalized to a real semiconductor fab. Real MES data, operator acceptance, shadow-mode validation and production deployment remain external-dependency work.
