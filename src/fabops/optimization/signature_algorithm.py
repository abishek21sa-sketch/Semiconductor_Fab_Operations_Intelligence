"""RARE-FAB CVaR release reference contract."""

from math import ceil


def _cvar(losses, alpha):
    ordered = sorted(float(x) for x in losses)
    tail_start = min(len(ordered) - 1, max(0, ceil(alpha * len(ordered)) - 1))
    tail = ordered[tail_start:]
    return sum(tail) / len(tail)


def select_release_slot(lot, slots, scenarios, *, alpha=0.90, risk_aversion=0.35):
    if not slots or not scenarios or not (0 < alpha < 1):
        raise ValueError("slots, scenarios and alpha are required")
    rows = []
    for slot in slots:
        losses = []
        for scenario in scenarios:
            due = float(lot.get("due_slot", 0))
            queue = float(lot.get("queue_risk", 0)) * float(scenario.get("queue", 1))
            losses.append(max(0.0, float(slot) - due) + queue)
        nominal = sum(losses) / len(losses)
        rows.append({"slot": slot, "nominal_loss": nominal, "cvar": _cvar(losses, alpha), "score": nominal + risk_aversion * _cvar(losses, alpha)})
    return min(rows, key=lambda x: (x["score"], x["slot"]))


def ablation(lot, slots, scenarios, **kwargs):
    kwargs["risk_aversion"] = 0.0
    return select_release_slot(lot, slots, scenarios, **kwargs)


def sensitivity(lot, slots, scenarios, alpha, **kwargs):
    kwargs["alpha"] = alpha
    return select_release_slot(lot, slots, scenarios, **kwargs)
