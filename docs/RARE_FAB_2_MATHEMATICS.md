# RARE-FAB 2.0 Mathematical Defense

## Decision

Choose the release slot for each candidate wafer lot under re-entrant workload capacity and uncertain fab conditions.

Let `x[i,t]` be binary and equal to one when lot `i` is released in slot `t`. Every lot is assigned exactly once. Each slot has WIP and tool-group workload capacities.

## Objective

For scenario `s`, release-plan loss `L_s(x)` contains service/tardiness, queue-time, AMHS, energy, maintenance-opportunity and qualification exposure. V7.2 introduces **release-window pressure** so scenario exposure changes with the selected slot instead of acting only as a lot-level constant.

The master problem is:

```text
min nominal_cost(x) + lambda * CVaR_alpha(L_s(x))
```

with the standard CVaR epigraph:

```text
CVaR_alpha = eta + 1 / ((1-alpha) |S|) * sum_s u_s
u_s >= L_s(x) - eta
u_s >= 0
```

## Core constraints

```text
sum_t x[i,t] = 1
```

for every candidate lot `i`.

For tool-group/resource `r` in release slot `t`:

```text
sum_i workload[i,r] * x[i,t] <= capacity[t,r]
```

For released WIP:

```text
sum_i wip_units[i] * x[i,t] <= WIP_limit[t]
```

`x[i,t]` is binary. `eta` is continuous and `u_s >= 0`.

## Scenario / decision coupling

A scenario may specify `slot_pressure[t]`. Queue, AMHS, energy, maintenance and qualification exposure are scaled by that pressure for the selected release slot. Examples include a lithography congestion window, reticle contention, AMHS surge or maintenance-sensitive capacity window.

This coupling is important: a high-risk lot can be moved away from a vulnerable release window, allowing risk aversion `lambda` and tail level `alpha` to change the optimized plan.

## Rolling-horizon interpretation

The model plans multiple slots, but only the first receding-horizon action is execution-eligible. The optimization is rebuilt when new fab state is available.

## Falsification protocol

RARE-FAB is not promoted because one objective improves. Validation must include:

- capacity-feasible FIFO baseline;
- common random numbers;
- risk-neutral optimization ablation (`lambda = 0`);
- paired hypothesis testing;
- CVaR comparison;
- alpha/lambda sensitivity;
- runtime evidence.

The claim is downgraded if paired improvement disappears, tail risk worsens materially, the risk-aware plan is indistinguishable from the risk-neutral plan across meaningful stress cases, or runtime becomes operationally unsuitable.

## Evidence boundary

The included benchmark is `REFERENCE_SYNTHETIC_BENCHMARK`. It does not establish real-fab performance, realized savings, causal production improvement, site calibration or methodological novelty.
