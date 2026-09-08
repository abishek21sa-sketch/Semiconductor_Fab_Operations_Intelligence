# Frontend Demo Flow — Semiconductor Fab Operations Intelligence

This product keeps its own visual language: **fab command center / tool-lot topology**. The shared contract is behavioral evidence, not a shared layout or theme.

## Native entrypoint

`frontend/index.html`

## Project-specific demo sequence

1. inspect lot and tool state
2. simulate queue and hazard risk
3. run CVaR release schedule
4. stress the fab scenario
5. shift supervisor approves release

## Evidence requirements

The screen must show the project-native inputs, objective, constraints, baseline/counterfactual, evidence class, signature decision, and human approval/hold state. The product must not imply autonomous actuation.

## API evidence surface

The read-only signature evidence endpoint is `/governance/signature`. Its response is linked to `artifacts/fortune50_capability_benchmark.json` and exposes the current decision, baseline, sensitivity/counterfactual evidence, and human-gated status.
