# Semiconductor Fab Operations Intelligence — Airlines-1.5× Depth Candidate

Release: `SEMICONDUCTOR_FAB_FORTUNE50_AIRLINES15X_RC5`

## What changed

This release adds a provenance-aware empirical backbone, a live empirical API, project-native historical/entity diagnostics, a named empirical case study, external-source refresh/promotion workflow, live empirical charts, and a 26+ workspace contract in which each workspace has a distinct method/evidence/action definition.

## Current evidence mode

- Source: **SECOM**
- Source URL: https://archive.ics.uci.edu/dataset/179/secom
- Mode: **offline_reference**
- Promotion state: **REFERENCE_ONLY**
- Local analyzable evidence: **92 rows / 3 fields**
- Workspaces: **28**

## Domain diagnostic

**fab tail-risk and risk-aversion sensitivity**

Reference metrics:
```json
{
  "rare_vs_fifo_mean_loss_improvement": 72.3229,
  "rare_vs_fifo_cvar90_reduction": 81.8924,
  "tail_gain_vs_risk_neutral": 10.3076,
  "paired_dominance_rate": 1.0
}
```

Decision signal: Use risk-aware release control when tail-risk gain is material; retain FIFO as a transparent baseline.

## Analytical chain

source provenance → schema/data-quality checks → entity/factor drilldown → cohort/history comparison → diagnostic ranking → predictive model → original algorithm → OR/simulation escalation → counterfactual challenge → human decision

## Windows gates

Core/offline acceptance:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\windows_airlines15x_acceptance.ps1
```

External-data promotion (internet required):
```powershell
.\scripts\windows_external_data_promotion.ps1
```

## Claim boundary

External-source results are claimed only when data_mode is refreshed_external or published_external_snapshot; offline_reference remains reference evidence.

The label “Airlines-1.5×” is an internal portfolio-depth target relative to the latest observable Airlines evidence, not an external company certification and not a claim that reference/synthetic data is real production evidence.
