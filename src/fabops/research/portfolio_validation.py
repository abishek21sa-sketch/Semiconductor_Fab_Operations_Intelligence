from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass

from scipy.stats import binomtest, ttest_rel

from fabops.optimization.rare_fab import _cost, optimize_rare_fab


@dataclass(frozen=True)
class _Challenge:
    lots: list[dict]
    slots: list[dict]
    scenarios: list[dict]


def _challenge(seed: int, lot_count: int) -> _Challenge:
    rng = random.Random(seed)
    lots = []
    for i in range(lot_count):
        lots.append(
            {
                "lot_id": f"L{i:03d}",
                "priority": 1 + (i % 3),
                "due_slot": i % 4,
                "queue_risk": rng.uniform(0.15, 1.30),
                "amhs_moves": 1 + (i % 4),
                "energy_kwh": rng.uniform(1.0, 4.5),
                "maintenance_interaction": rng.random(),
                "qualification_risk": rng.random() * 0.65,
                "wip_units": 1.0,
                "workload": {
                    "PHOTO": 0.75 + (i % 2) * 0.50,
                    "ETCH": 0.50 + (i % 3) * 0.20,
                },
            }
        )
    slot_count = max(4, math.ceil(lot_count / 4))
    slots = [
        {
            "slot": t,
            "wip_limit": 4,
            "capacity": {"PHOTO": 5.0, "ETCH": 4.4},
            "base_penalty": t * 0.12,
        }
        for t in range(slot_count)
    ]
    scenarios = []
    for k in range(20):
        hot = rng.randrange(slot_count)
        pressure = [rng.uniform(0.75, 1.25) for _ in range(slot_count)]
        pressure[hot] *= rng.uniform(1.8, 3.0)
        # Secondary congestion window produces nontrivial trade-offs instead of one
        # universally safe slot.
        pressure[(hot + 1 + (k % max(1, slot_count - 1))) % slot_count] *= rng.uniform(1.2, 1.8)
        scenarios.append(
            {
                "queue": rng.uniform(0.75, 2.0),
                "amhs": rng.uniform(0.75, 2.1),
                "energy": rng.uniform(0.75, 1.8),
                "maintenance": rng.uniform(0.7, 2.0),
                "qualification": rng.uniform(0.75, 1.8),
                "capacity": rng.uniform(0.9, 1.25),
                "slot_pressure": pressure,
            }
        )
    return _Challenge(lots, slots, scenarios)


def _feasible_fifo_assignment(ch: _Challenge) -> list[int]:
    """Greedy FIFO baseline honoring the same WIP/resource capacities as RARE-FAB."""
    resources = sorted({r for s in ch.slots for r in s.get("capacity", {})})
    used_wip = [0.0 for _ in ch.slots]
    used = [{r: 0.0 for r in resources} for _ in ch.slots]
    assignment: list[int] = []
    for lot in ch.lots:
        chosen = None
        for t, slot in enumerate(ch.slots):
            if used_wip[t] + float(lot.get("wip_units", 1.0)) > float(slot.get("wip_limit", len(ch.lots))) + 1e-9:
                continue
            feasible = True
            for r in resources:
                cap = float(slot.get("capacity", {}).get(r, math.inf))
                load = float(lot.get("workload", {}).get(r, 0.0))
                if used[t][r] + load > cap + 1e-9:
                    feasible = False
                    break
            if feasible:
                chosen = t
                break
        if chosen is None:
            raise RuntimeError("FIFO baseline could not construct a capacity-feasible release plan")
        assignment.append(chosen)
        used_wip[chosen] += float(lot.get("wip_units", 1.0))
        for r in resources:
            used[chosen][r] += float(lot.get("workload", {}).get(r, 0.0))
    return assignment


def _losses_for_assignment(ch: _Challenge, assignment: list[int]) -> list[float]:
    return [
        sum(
            _cost(lot, assignment[i], scenario)
            + float(ch.slots[assignment[i]].get("base_penalty", 0.0)) * float(scenario.get("capacity", 1.0))
            for i, lot in enumerate(ch.lots)
        )
        for scenario in ch.scenarios
    ]


def _cvar(xs: list[float], alpha: float = 0.90) -> float:
    ordered = sorted(float(x) for x in xs)
    if not ordered:
        return 0.0
    q = ordered[min(len(ordered) - 1, math.ceil(alpha * len(ordered)) - 1)]
    tail = [x for x in ordered if x >= q]
    return statistics.mean(tail)


def _safe_ttest_less(a: list[float], b: list[float]) -> tuple[float, float]:
    result = ttest_rel(a, b, alternative="less")
    stat, p = float(result.statistic), float(result.pvalue)
    if math.isnan(stat):
        stat = 0.0
    if math.isnan(p):
        p = 1.0
    return stat, p


def portfolio_validation(seed: int = 117, replications: int = 10, lot_count: int = 12) -> dict:
    """Portfolio release evidence for RARE-FAB under common random numbers.

    This is deliberately a synthetic/reference experiment. It tests whether the risk-aware
    release policy improves paired scenario loss versus a capacity-feasible FIFO baseline,
    includes a risk-neutral ablation, and records alpha/lambda sensitivity on one fixed challenge.
    """
    if replications < 3:
        raise ValueError("replications must be >= 3")
    if lot_count < 6:
        raise ValueError("lot_count must be >= 6")

    started = time.perf_counter()
    fifo_mean: list[float] = []
    rare_mean: list[float] = []
    neutral_mean: list[float] = []
    fifo_tail: list[float] = []
    rare_tail: list[float] = []
    neutral_tail: list[float] = []
    rare_runtime: list[float] = []

    for r in range(replications):
        ch = _challenge(seed + r * 101, lot_count)
        fifo_assign = _feasible_fifo_assignment(ch)
        fifo_losses = _losses_for_assignment(ch, fifo_assign)

        rare = optimize_rare_fab(ch.lots, ch.slots, ch.scenarios, alpha=0.90, risk_aversion=0.35)
        neutral = optimize_rare_fab(ch.lots, ch.slots, ch.scenarios, alpha=0.90, risk_aversion=0.0)
        if not rare.success or not neutral.success:
            raise RuntimeError("RARE-FAB validation solve failed")

        fifo_mean.append(statistics.mean(fifo_losses))
        rare_mean.append(statistics.mean(rare.scenario_losses))
        neutral_mean.append(statistics.mean(neutral.scenario_losses))
        fifo_tail.append(_cvar(fifo_losses, 0.90))
        rare_tail.append(_cvar(rare.scenario_losses, 0.90))
        neutral_tail.append(_cvar(neutral.scenario_losses, 0.90))
        rare_runtime.append(rare.runtime_s)

    stat, p_value = _safe_ttest_less(rare_mean, fifo_mean)
    paired_improvement = [b - a for a, b in zip(rare_mean, fifo_mean)]
    wins = sum(x > 0 for x in paired_improvement)
    sign_p = float(binomtest(wins, replications, 0.5, alternative="greater").pvalue)

    # Fixed-challenge sensitivity: same lots/scenarios across all alpha/lambda settings.
    fixed = _challenge(seed + 99991, lot_count)
    sensitivity = []
    for alpha in (0.80, 0.90, 0.95):
        for lam in (0.0, 0.20, 0.35, 0.60):
            plan = optimize_rare_fab(fixed.lots, fixed.slots, fixed.scenarios, alpha=alpha, risk_aversion=lam)
            if not plan.success:
                raise RuntimeError(f"sensitivity solve failed for alpha={alpha}, lambda={lam}")
            sensitivity.append(
                {
                    "alpha": alpha,
                    "risk_aversion": lam,
                    "mean_loss": round(statistics.mean(plan.scenario_losses), 4),
                    "cvar_loss": round(_cvar(plan.scenario_losses, alpha), 4),
                    "objective": plan.objective,
                    "runtime_s": plan.runtime_s,
                }
            )

    return {
        "evidence_class": "REFERENCE_SYNTHETIC_BENCHMARK",
        "seed": seed,
        "replications": replications,
        "lot_count": lot_count,
        "hypothesis": {
            "null": "RARE-FAB paired mean scenario loss is not lower than capacity-feasible FIFO.",
            "alternative": "RARE-FAB paired mean scenario loss is lower than capacity-feasible FIFO.",
            "test": "one-sided paired t-test with common random numbers",
            "statistic": round(stat, 6),
            "p_value": round(p_value, 8),
            "reject_at_0_05": p_value < 0.05,
            "paired_sign_test_p_value": round(sign_p, 8),
        },
        "paired_comparison": {
            "rare_mean_loss": round(statistics.mean(rare_mean), 4),
            "fifo_mean_loss": round(statistics.mean(fifo_mean), 4),
            "mean_improvement": round(statistics.mean(paired_improvement), 4),
            "median_improvement": round(statistics.median(paired_improvement), 4),
            "dominance_rate": round(wins / replications, 4),
            "rare_cvar90": round(statistics.mean(rare_tail), 4),
            "fifo_cvar90": round(statistics.mean(fifo_tail), 4),
        },
        "risk_neutral_ablation": {
            "neutral_mean_loss": round(statistics.mean(neutral_mean), 4),
            "risk_aware_mean_loss": round(statistics.mean(rare_mean), 4),
            "neutral_cvar90": round(statistics.mean(neutral_tail), 4),
            "risk_aware_cvar90": round(statistics.mean(rare_tail), 4),
            "tail_delta_neutral_minus_risk_aware": round(statistics.mean(neutral_tail) - statistics.mean(rare_tail), 4),
        },
        "sensitivity": sensitivity,
        "mean_solver_runtime_s": round(statistics.mean(rare_runtime), 6),
        "wall_runtime_s": round(time.perf_counter() - started, 4),
        "claim_boundary": (
            "Synthetic MiniFab-inspired decision benchmark only. This evidence does not establish real-fab "
            "performance, causal production improvement, site calibration, or methodological novelty."
        ),
    }
