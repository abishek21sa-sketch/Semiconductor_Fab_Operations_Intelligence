from fabops.optimization import multi_operation


def test_solver_exception_uses_constraint_checked_fallback(monkeypatch):
    def fail_before_result(*args, **kwargs):
        raise MemoryError("simulated HiGHS allocation failure")

    monkeypatch.setattr(multi_operation, "milp", fail_before_result)
    jobs = multi_operation.build_lot_operations(2, 17)
    result = multi_operation.optimize_multi_operation(jobs, 96, 17)
    assert result.success is True
    assert "FALLBACK_FEASIBLE_AFTER_SOLVER_STATUS" in result.message
    assert result.precedence_violations == 0
    assert result.queue_breaches == 0
