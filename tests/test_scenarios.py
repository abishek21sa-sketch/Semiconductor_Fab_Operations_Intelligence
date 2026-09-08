from fabops.simulation.scenarios import Scenario, run_scenario, monte_carlo

def test_scenario_is_reproducible():
    s=Scenario("x",lots=20,seed=8)
    a=run_scenario(s); b=run_scenario(s)
    assert a["run_id"]==b["run_id"]
    assert a["avg_cycle_time"]==b["avg_cycle_time"]

def test_monte_carlo_produces_uncertainty_bounds():
    out=monte_carlo(Scenario("x",lots=15,seed=3,failure_rate=.02),replications=4)
    assert out["replications"]==4
    assert out["metrics"]["avg_cycle_time"]["p95"] >= out["metrics"]["avg_cycle_time"]["p05"]
