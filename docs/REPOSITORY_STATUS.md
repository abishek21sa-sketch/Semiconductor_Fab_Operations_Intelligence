# Repository Status — Flagship V7.2 Portfolio RC1

## Current release

- **Application version:** 7.2.0
- **Release:** `FLAGSHIP_V7_2`
- **Recovery stage:** `PORTFOLIO_RC1`
- **Primary local target:** Windows
- **Production/site validated:** No

## Implemented and locally validated

- re-entrant semiconductor lot routing and deterministic simulation;
- coupled fab twin with batching, reticles, PM, failures, queue-time damage, rework and scrap feedback;
- Factory Physics / bottleneck / Little's Law analytics;
- cycle-time, ETA and bottleneck predictive baselines;
- qualification-constrained assignment and release-control MILPs;
- integrated time-indexed scheduling;
- multi-operation precedence / queue-time / reticle / PM scheduling;
- RARE-FAB nominal + CVaR release optimization with slot-dependent scenario pressure;
- stochastic and closed-loop recovery policies;
- canonical manufacturing event fabric and deterministic state replay;
- wafer genealogy and equipment digital threads;
- SPC, EWMA, CUSUM and Shewhart process-health analytics;
- lot passport / risk-driver evidence / human-gated decision synthesis;
- FastAPI service and multi-workspace operator workstation;
- common-random-number research validation with hypothesis test, ablation and sensitivity;
- source-only reproducible release packaging.

## Recovery validation

The source regression suite contains **89 tests** and passed in two deterministic groups in the recovery build environment. The slower V6 scaling contract was included.

The deterministic functional contract also passed after recovery:

- coupled twin completed lots and emitted state events;
- multi-operation schedule had zero precedence, queue-time, reticle and PM conflicts;
- PHOTO_OUTAGE recovery changed future-state metrics while remaining supervisor-gated;
- V7 manufacturing data fabric validated and replayed correctly;
- V7.2 lot passport / decision synthesis remained human-gated.

The updated Windows release script must be run from a clean extraction before this RC is promoted to final.

## Current evidence boundary

All quantitative evidence supplied with the repository is synthetic/reference manufacturing evidence. It is suitable for demonstrating engineering structure, reproducibility, mathematical behavior and software execution, but it is not evidence of:

- live MES/EAP/SECS-GEM connectivity;
- site-calibrated model accuracy;
- production deployment;
- operator acceptance;
- realized fab throughput, cycle-time, yield or cost impact.

## Historical milestones

Historical root manifests and release metadata from V2/V3/V6/V7.1 are preserved under `docs/history/` to avoid confusing them with the current release.
