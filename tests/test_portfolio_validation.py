from fabops.research.portfolio_validation import portfolio_validation


def test_portfolio_validation_contract():
    result = portfolio_validation(seed=31, replications=3, lot_count=8)
    assert result["evidence_class"] == "REFERENCE_SYNTHETIC_BENCHMARK"
    assert result["replications"] == 3
    assert 0 <= result["paired_comparison"]["dominance_rate"] <= 1
    assert len(result["sensitivity"]) == 12
    assert "p_value" in result["hypothesis"]
    assert "tail_delta_neutral_minus_risk_aware" in result["risk_neutral_ablation"]
    assert "real-fab" in result["claim_boundary"]
