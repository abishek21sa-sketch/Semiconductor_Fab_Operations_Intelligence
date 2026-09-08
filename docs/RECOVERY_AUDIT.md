# Semiconductor Fab Operations Intelligence — Recovery Audit

## Baseline recovered

The recovered repository was package version **7.2.0** and contained the full V0.9 → V7 engineering history, including re-entrant simulation, RARE-FAB, integrated and multi-operation MILPs, closed-loop recovery, manufacturing data fabric, process control, a multi-workspace frontend, Windows scripts and extensive tests.

The previous Windows evidence showed the 7.2.0 source executing deterministic functional contracts successfully, including the coupled twin, multi-operation schedule, closed-loop PHOTO outage recovery and V7 data-fabric reconstruction. That evidence remains historical input to the recovery, not proof that the newly patched RC has already passed on Windows.

## Release blockers found

### 1. Version-contract drift — FIXED

The repository simultaneously reported 3.0.0, 7.1.0 and 7.2.0 across package metadata, tests, frontend, API release labels, README and acceptance output.

Recovery action:

- `fabops.__version__ = 7.2.0`
- `fabops.__release__ = FLAGSHIP_V7_2`
- API imports the package version/release instead of redefining a second source of truth
- stale 7.1 test expectations removed
- frontend labels updated
- Windows acceptance final marker updated
- V7.2 release metadata added

### 2. Release archive contamination — FIXED IN RELEASE BUILDER

The recovered 119 MB ZIP included a complete `.venv`, pytest cache, bytecode and generated egg metadata. These are not appropriate for GitHub or a recruiter-facing release.

Recovery action:

- release builder now produces a source-only archive;
- `.venv`, caches, bytecode, local databases, egg metadata and `dist` are excluded;
- a SHA-256 file manifest is generated;
- the final ZIP receives a separate SHA-256 digest.

### 3. V7.2 capability not included in the full acceptance chain — FIXED

The repository contained `run_v72_validation.py`, lot passports and decision synthesis, but the Windows acceptance script stopped at V7 data-fabric validation.

Recovery action:

- full pytest added to the acceptance chain;
- V7.2 decision-center validation added;
- portfolio research validation added.

### 4. CVaR risk term was weakly decision-coupled — FIXED

The previous scenario loss mostly multiplied lot attributes by scenario scalars that were independent of release slot. That meant the CVaR term could be mathematically present while producing the same release plan as a risk-neutral optimizer.

Recovery action:

- scenario `slot_pressure` introduced as a scalar/list/mapping contract;
- queue, AMHS, energy, maintenance and qualification exposure now vary with the chosen release window;
- the existing MILP/CVaR structure is preserved;
- risk-aware versus risk-neutral behavior is now measured explicitly.

### 5. Research evidence was incomplete relative to governance — FIXED FOR RC

The governance standard requires baselines, null hypotheses, ablations, sensitivity and computational evidence.

Recovery action:

- capacity-feasible FIFO comparison under common random numbers;
- one-sided paired hypothesis test;
- exact paired sign test;
- risk-neutral optimization ablation;
- alpha / risk-aversion sensitivity grid;
- machine-readable evidence boundary.

## Regression status

The source suite contains **89 tests**. During recovery it was executed in two groups to avoid a single long CI-style timeout:

- all tests except the V6 group: PASS;
- V6 API + coupled/scaling tests: PASS.

`python -m compileall -q src scripts` is also part of the release gate.

## Remaining gate before final promotion

The RC must be extracted into a clean Windows folder and run through:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\acceptance_windows.ps1
```

Only after the updated source emits `FLAGSHIP_V7_2_ACCEPTANCE=PASS` should this RC be labeled final portfolio release.
