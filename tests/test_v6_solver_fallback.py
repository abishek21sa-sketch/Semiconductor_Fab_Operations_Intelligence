from types import SimpleNamespace

import fabops.optimization.multi_operation as multi_operation
from fabops.optimization.multi_operation import build_lot_operations, optimize_multi_operation


def test_multi_operation_returns_checked_fallback_when_solver_times_out(monkeypatch):
    """A solver time budget must not turn a feasible control plan into an outage."""
    monkeypatch.setattr(
        multi_operation,
        "milp",
        lambda *args, **kwargs: SimpleNamespace(
            success=False,
            status=1,
            x=None,
            message="Time limit reached",
        ),
    )

    schedule = optimize_multi_operation(build_lot_operations(3, 17), 96, 17)

    assert schedule.success is True
    assert schedule.message.startswith("FALLBACK_FEASIBLE_AFTER_SOLVER_STATUS")
    assert schedule.operations == 24
    assert schedule.precedence_violations == 0
    assert schedule.queue_breaches == 0
    assert schedule.reticle_conflicts == 0
    assert schedule.pm_conflicts == 0
