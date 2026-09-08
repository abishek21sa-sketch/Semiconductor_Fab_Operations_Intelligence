# Flagship V6 Integration Architecture

## Why V6 exists

Earlier releases implemented many semiconductor-operating capabilities but several were evaluated as separate services. V6 couples the most important physical and decision mechanisms into the same reference trajectory.

## Coupled digital twin

A lot moves through a re-entrant semiconductor route. Its operation start time can be delayed by:

1. qualified-tool availability,
2. setup family,
3. preventive-maintenance blackout,
4. shared reticle availability,
5. batch formation for batch-capable processes,
6. stochastic tool failure and repair.

The queue-time clock runs until the actual start, not merely until dispatch is attempted.

If the realized queue-time exposure is excessive, the reference yield mechanism can trigger rework or scrap. Rework changes the lot's route index and returns the lot upstream, so WIP, batching, cycle time, reticle pressure and future queues all change.

## Multi-operation rolling-horizon MILP

The V6 scheduler assigns operation/start/tool variables over a bounded horizon.

Hard constraints include:

- one assignment per operation;
- tool qualification;
- tool-time non-overlap;
- reticle-time non-overlap;
- PM blackout exclusion;
- within-lot technological precedence;
- queue-time upper bound between consecutive operations.

The reference scaling experiment is intentionally bounded. A two-lot / 16-operation instance solves reliably under the short scaling budget. A three-lot / 24-operation instance solves under a larger bounded budget. The four-lot / 32-operation probe can hit the configured time limit, which is reported rather than hidden.

## Closed-loop recovery

A disruption first changes the coupled twin. A generic mean/CVaR policy model provides a prior action. V6 then executes every candidate recovery policy against the same virtual-fab disruption and compares the resulting future state. The selected recommendation is therefore simulation-challenged before entering the supervisor review gate.

## Windows acceptance

The official Windows evidence stream does not use pytest because the user's Microsoft Store Python 3.13 runtime produced non-fatal access-violation diagnostics inside the pytest/native diagnostic path despite zero exit status. V6 therefore separates:

- **development gate:** 78 portable pytest tests;
- **official Windows functional gate:** direct module contracts + persistence + quantitative validations + real Uvicorn HTTP smoke.

This is not a suppression of functional failures. Every official acceptance subprocess has its exit code checked explicitly.

## Evidence boundary

All results remain reference/synthetic virtual-fab evidence. V6 does not claim calibration to a specific semiconductor site or autonomous production execution.
