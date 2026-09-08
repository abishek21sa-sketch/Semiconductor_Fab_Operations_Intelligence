from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.decision.engine import recommend_dispatch_rule

def test_recommendation_has_evidence():
    r=recommend_dispatch_rule(FabSimulator(build_minifab_config(),seed=8),generate_lots(30,seed=8))
    assert r.recommended_rule in r.evidence
    assert r.confidence=="simulation-backed"
