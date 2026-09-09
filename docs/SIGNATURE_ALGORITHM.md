# RARE-FAB — Signature Algorithm Contract

This document is the project-native mathematical center required by the portfolio governance pack. The implementation alias is **QSHIFT triage plus risk-aware release scheduling**.

## Operational decision

The module makes one operational decision: **select a release slot for a lot under due-date, queue-risk, and tail-loss uncertainty**.

## Mathematical center

- **Decision variables:** discrete release-slot choice; scenario losses and queue-risk terms.
- **Objective:** minimize nominal lateness plus risk_aversion * CVaR_alpha of scenario loss.
- **Constraints and release gates:** slot must be one of the declared release slots; CVaR uses eta/excess tail logic over the scenario losses.
- **Determinism:** the reference contract is deterministic for a fixed candidate set, scenario, and seed.
- **Solver status:** the current reference is an executable enumerative/closed-form contract; production solver integration remains downstream of this gate.

## Baseline and counterfactual

The named baseline is **capacity-feasible FIFO or earliest-due-date release**. The counterfactual is evaluated on the same inputs and scenario so that a claimed improvement cannot be caused by a changed data slice.

## Ablation

The declared ablation is to **set risk_aversion to zero so only nominal lateness remains**. It is executable through the module's `ablation(...)` function and is covered by the signature tests.

## Sensitivity

The sensitivity sweep is: **vary alpha and risk aversion; report slot, tail loss, and feasibility response**. Sensitivity output is evidence about robustness, not a claim of causal production impact.

## Evidence classes and authority

Evidence is kept separate as observed, simulated, optimized, shadow-mode, and realized. **observed SECOM/fab public data for predictive context; simulated release scenarios; realized fab intervention outcomes are not claimed** A human authority remains required before any operational action; autonomous execution is disabled.

## Implementation and acceptance

- Implementation: `src/fabops/optimization/signature_algorithm.py`
- Windows acceptance test: `tests/test_signature_algorithm.py`
- Required acceptance result: `4 tests, OK`, with invalid inputs and no-feasible cases controlled explicitly.

## Release boundary

This signature is release-ready only when this contract, the research-validation protocol, the machine-readable governance artifact, the existing production-ready gates, and the final integrity/hash checks all pass together.
