# Enterprise Readiness — Semiconductor Fab Operations Intelligence

## Release status

**FLAGSHIP_V7_2_PORTFOLIO_RELEASE** is a portfolio release candidate, not a production deployment certification.

## Decision-system identity

Re-entrant fab control under queue-time, reticle, PM and disruption constraints with risk-aware lot release and human-gated execution.

**Signature core:** RARE-FAB stochastic release/recovery control + CVaR tail-risk reasoning + governed decision certificates

## Verified in this recovery build

- 90/90 Python regression tests verified
- Machine-readable validation evidence is included and hashed.
- Production writes/autonomous execution are blocked by release governance.
- Windows remains the primary local acceptance target.

## Evidence inventory

- `docs/validation/portfolio_release_validation.json` — SHA-256 `2d5e2299d6eaba3d6443c38a88078f4ef0cdae792d69554a846dbd4d452e04cb`
- `RELEASE_V7_2_VALIDATION.json` — SHA-256 `0c4cb59e4857477220b826e0ecd52fc6745113b5929e1f399a5b8960a418381f`

## Gates still required before any production claim

- Windows real-HTTP/PowerShell acceptance on target machine
- Real-fab/site calibration and external validation

## Claim boundary

This repository may be presented as a reproducible engineering/research decision system supported by its included model-based evidence. It must not be presented as real-world production improvement, certification, clinical effectiveness, vehicle certification, grid approval, or plant/fab performance unless that external validation is subsequently completed.
