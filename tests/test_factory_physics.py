from fabops.analytics.factory_physics import bottleneck_report, little_law_check

def test_bottleneck_report_ranks_utilization():
    r=bottleneck_report({"utilization":{"A-1":.4,"B-1":.9,"B-2":.7}})
    assert r["primary_bottleneck"]=="B-1"
    assert r["group_utilization"]["B"]==.8

def test_little_law_check_fields():
    r=little_law_check({"makespan":100,"throughput":10,"avg_cycle_time":20,"avg_wip":2})
    assert r["little_law_implied_wip"]==2.0
    assert r["absolute_gap"]==0.0
