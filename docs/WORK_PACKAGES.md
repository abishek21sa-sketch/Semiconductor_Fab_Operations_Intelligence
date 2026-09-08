# Work Package Register — v0.9.0

| WP | Scope | State | Primary evidence |
|---|---|---|---|
| WP01 | Repository foundation | Validated | package, Makefile, CI, Docker, tests |
| WP02 | Semiconductor domain model | Validated | routes, lots, recipes, tool qualifications |
| WP03 | Fab event ingestion | Validated | canonical Pydantic contract, CSV/JSONL loaders |
| WP04 | Wafer/tool state engine | Validated | deterministic replay, snapshots, anomalies |
| WP05 | Persistence/audit | Validated | SQLite idempotent event store + decision history |
| WP06 | Digital twin | Validated benchmark | re-entrant DES + disruptions + event log |
| WP07 | Dispatching | Validated benchmark | FIFO/EDD/SPT/CR/priority comparison |
| WP08 | Factory Physics | Validated benchmark | utilization, WIP, Little's Law, bottleneck report |
| WP09 | Scenario/Monte Carlo | Validated benchmark | distributional scenario evidence |
| WP10 | Scheduling/assignment | Validated bounded MILP | qualification-constrained assignment |
| WP11 | WIP/release optimization | Validated bounded MILP | capacity-constrained release control |
| WP12 | Cycle-time AI | Validated synthetic baseline | holdout metrics in validation artifact |
| WP13 | ETA AI | Validated synthetic baseline | grouped-holdout metrics |
| WP14 | Bottleneck AI | Validated synthetic baseline | scenario holdout metrics, bounded evidence |
| WP15 | Decision intelligence | Validated benchmark | simulation-backed recommendation + risk score |
| WP16 | REST API | Validated | automated endpoint tests |
| WP17 | Frontend | Implemented | responsive operational UI |
| WP18 | Deployment/CI | Implemented | Docker, Compose, GitHub Actions |
| WP19 | Documentation/reproducibility | Validated | status, architecture, runbooks, generated evidence |
| WP20 | Real-fab integration | External dependency | requires MES/equipment/data/IAM environment |
