## AIRLINES-1.5× DEPTH CANDIDATE

Current release `SEMICONDUCTOR_FAB_FORTUNE50_AIRLINES15X_RC5` adds a live empirical/historical analysis layer, 26+ substantive workspaces, project-native domain diagnostics, external-source refresh/provenance, and AI decisions grounded in explicit evidence mode. See `docs/AIRLINES_15X_RELEASE.md`.

# Fortune-50 TENX analytical release

**Internal portfolio target:** Math 10/10 · UI 10/10 · AI 10/10, subject to the evidence boundaries below.

- Repository-authored algorithm: **QSHIFT-v1**
- Unique predictive-learning family: **Cox proportional-hazards survival learning**
- Analytical AI role: **AI Shift Engineer**
- TENX workspaces: **22**
- Operational authority: **human-gated; autonomous execution blocked**

### Test the TENX layer on Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\windows_tenx_acceptance.ps1
.\scripts\start_tenx_workstation.ps1
```

The first command validates prediction → decision → counterfactual → OR escalation → user-aid behavior and a five-seed originality stress suite. The second opens the dedicated analytical workstation.

> **Evidence boundary:** TENX bundled metrics are synthetic/reference validation, not field deployment validation. Existing native Windows, Julia/Go/Rust/frontend, external-data, clinical, or production gates remain applicable where documented.

---


## Portfolio RC2 — governed decision certificates

The V7.2 decision center now emits tamper-evident SHA-256 decision certificates with explicit risk evidence, supervisor authority, human-gate state, and an autonomous-execution hard block. This adds release-level traceability without changing the underlying RARE-FAB optimization claims or evidence boundary.

# Semiconductor Fab Operations Intelligence — Flagship V7.2

**Version 7.2.0 · Windows-first semiconductor manufacturing decision-intelligence platform**

Semiconductor Fab Operations Intelligence is a portfolio-grade research/engineering workstation for **wafer-lot release, dispatch, re-entrant scheduling, queue-time control, tool/reticle constraints, preventive-maintenance interactions, disruption recovery, process-health monitoring, and cycle-time risk**. It is not a generic dashboard: the operator console is backed by a discrete-event fab twin, mixed-integer optimization, CVaR tail-risk logic, manufacturing-state reconstruction, predictive analytics, and human-gated decision synthesis.

> **Evidence boundary.** All included numerical results use synthetic/reference MiniFab-inspired manufacturing data unless a source is explicitly identified otherwise. The repository does **not** claim live MES/SECS-GEM connectivity, site-calibrated performance, production deployment, or realized fab impact.

## Why this project exists

A semiconductor fab is a re-entrant, highly coupled production system. Release decisions change downstream WIP; queue-time violations can damage yield; reticles and qualified chambers constrain lithography; PM and stochastic failures change available capacity; and local dispatch choices can create global cycle-time risk. This repository models those interactions as a decision system rather than presenting isolated KPIs.

## Decision stack

1. **Manufacturing data fabric** — canonical MES-like events, validation, deterministic replay, lot/wafer/tool state reconstruction.
2. **Factory digital twin** — re-entrant discrete-event simulation with batching, reticles, PM, stochastic tool failures, queue-time damage, rework and scrap feedback.
3. **Prediction / risk** — cycle-time, ETA, bottleneck, equipment, yield, queue and process-health analytics.
4. **Operations Research** — qualified-tool assignment, CONWIP-style release control, time-indexed integrated scheduling, multi-operation precedence scheduling and RARE-FAB CVaR release optimization.
5. **Decision intelligence** — closed-loop recovery, ranked evidence packets, lot passports, risk-driver attribution and mandatory supervisor approval.
6. **Research evidence** — common-random-number benchmarks, null-hypothesis testing, risk-neutral ablation, sensitivity analysis and explicit claim boundaries.

## Signature mathematical core — RARE-FAB

For candidate lot `i` and release slot `t`, binary variable `x[i,t]` selects exactly one release slot. The optimizer enforces slot WIP and tool-group workload capacities and minimizes a nominal operating cost plus CVaR tail exposure:

```text
min  nominal_cost(x) + λ * CVaRα(Ls(x))

subject to
  Σt x[i,t] = 1                                 for every lot i
  Σi workload[i,r] x[i,t] ≤ capacity[t,r]      for every slot t, resource r
  Σi wip[i] x[i,t] ≤ WIP_limit[t]              for every slot t
  us ≥ Ls(x) - η                               for every scenario s
  us ≥ 0
  x[i,t] ∈ {0,1}
```

V7.2 makes scenario loss **decision-dependent by release window**: queue, AMHS, maintenance and qualification stress can vary by slot. This is important because it allows risk aversion to change the lot-to-slot plan rather than merely adding a constant risk term to every feasible solution.

See `docs/RARE_FAB_2_MATHEMATICS.md` and `docs/V3_MATHEMATICAL_ARCHITECTURE.md`.

## Portfolio validation added in V7.2

`scripts/run_portfolio_validation.py` evaluates RARE-FAB under common random numbers against a **capacity-feasible FIFO baseline** and a **risk-neutral optimization ablation**. It records:

- one-sided paired hypothesis test;
- paired dominance rate and mean/median improvement;
- mean loss and CVaR90 for RARE-FAB and FIFO;
- tail-risk difference between risk-aware and risk-neutral optimization;
- `(alpha, risk_aversion)` sensitivity grid;
- solver and wall-clock runtime;
- a machine-readable claim boundary.

The generated evidence is written to `docs/validation/portfolio_release_validation.json`.

## Product workspaces

The browser workstation includes:

- Mission Control
- Fab Topology
- Lot Control
- Lot Genealogy
- Queue-Time Control
- Tool & PM Control
- Yield & Rework
- RARE-FAB Lab
- Chambers & Batching
- Integrated Scheduling
- AMHS Network
- Coupled Digital Twin
- Closed-Loop Recovery
- Decision Center
- Experiment Manager
- Manufacturing Data Fabric
- Wafer Traceability
- Process Health / SPC
- Research & Evidence

## Windows quick start

From a clean extraction in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\start_windows.ps1
```

Open:

```text
http://127.0.0.1:9821/
```

API documentation:

```text
http://127.0.0.1:9821/docs
```

The startup script creates/reuses `.venv`, installs missing dependencies, and starts Uvicorn locally.

## Full Windows release gate

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\acceptance_windows.ps1
```

The current gate performs:

- editable installation;
- full pytest regression;
- deterministic functional acceptance;
- reference simulation / prediction / optimization validation;
- Flagship V2–V7 data-fabric validation;
- V7.2 decision-center validation;
- portfolio research validation;
- compileall;
- real local Uvicorn HTTP smoke test.

A successful updated run ends with:

```text
FLAGSHIP_V7_2_ACCEPTANCE=PASS
```

## Validation status

The recovery audit for this release found and corrected version-contract drift between `pyproject.toml`, the Python package, API responses, tests, frontend labels, Windows acceptance output and release metadata. The source regression suite contains **89 tests**. The current recovery build has passed the suite in the build container in two deterministic groups, including the V6 scaling contract. The updated Windows gate must still be executed on a clean Windows extraction before the RC is promoted to final portfolio release.

See `docs/RECOVERY_AUDIT.md` and `docs/PORTFOLIO_RELEASE.md`.

## Repository layout

```text
src/fabops/
  agents/             human-gated decision synthesis
  ai/                 cycle-time / ETA / bottleneck models
  analytics/          Factory Physics
  api/                FastAPI application
  control/            bay risk control
  data_fabric/        canonical MES-like events and replay
  decision/           risk, orchestration, closed-loop recovery
  equipment/          health, failure and digital-thread models
  experiments/        stress, comparison and scaling experiments
  genealogy/          wafer genealogy
  ingestion/          event contracts and loaders
  intelligence/       lot passports and risk evidence
  operations/         fab master data and operational views
  optimization/       MILP / CVaR / scheduling / release control
  process_control/    SPC, EWMA, CUSUM, Shewhart
  research/           reproducible benchmark harnesses
  semiconductor/      domain physics, AMHS, yield, chambers
  simulation/         DES and coupled fab twin
  state/              event-sourced state reconstruction
frontend/
  index.html           multi-workspace operator workstation
scripts/
  acceptance_windows.ps1
  start_windows.ps1
  run_*_validation.py
  build_release.py
tests/
docs/
```

## Engineering boundaries

Implemented and locally testable:

- deterministic synthetic manufacturing data generation;
- canonical event validation and replay;
- lot/wafer/tool genealogy;
- re-entrant discrete-event simulation;
- batching, reticle, PM and stochastic-failure interactions;
- queue-time damage / rework feedback;
- Factory Physics and bottleneck analysis;
- predictive baselines;
- MILP scheduling and release control;
- scenario-based CVaR optimization;
- closed-loop recovery simulation;
- human-gated decision packets;
- REST APIs, UI, tests and Windows scripts.

External dependencies intentionally not claimed:

- live factory MES/EAP/SECS-GEM integration;
- proprietary routes, recipes, qualifications and reticle inventories;
- real yield/metrology calibration;
- enterprise SSO/RBAC and production infrastructure;
- fab operator shadow-mode validation;
- causal production-impact validation.

## Release packaging

Build a sanitized source release:

```powershell
python .\scripts\build_release.py
```

The release builder excludes `.venv`, caches, bytecode, databases, generated package metadata and prior `dist` output, and writes a file-hash manifest plus SHA-256 digest beside the ZIP.

## Enterprise operability gate

This source release includes a governed decision-assurance layer, negative-path operability tests, hash-verifiable evidence, and a Windows enterprise acceptance gate. See `docs/ENTERPRISE_OPERABILITY.md`.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\\scripts\\acceptance_windows.ps1
```


## Public Data Backbone
This release contains a structured public-data layer under `data/raw`, `data/processed`, `data/contracts`, `data/dictionaries`, `data/provenance`, and `data/snapshots`. Run `scripts\fetch_public_data_windows.ps1` when the primary public dataset is not bundled, then run `scripts\windows_real_data_acceptance.ps1`. `artifacts/data_backbone_status.json` records source state, row/feature counts, missingness, SHA-256, validation status, case-study state, claim boundary, model version, and the human decision authority.

The public-data case is `SECOM Yield Excursion / Queue-Risk Investigation` and is wired into `QSHIFT-v1` review. Missing external raw data never silently falls back to a real-data claim; the dossier explicitly enters `REFERENCE_MODE_HOLD_FOR_REAL_DATA_CLAIM`.
