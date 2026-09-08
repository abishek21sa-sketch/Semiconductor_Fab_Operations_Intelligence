from fabops.governance import certify_lot_decision

def test_high_risk_certificate_is_human_gated_and_tamper_evident():
    a=certify_lot_decision('CERT-001',queue=88,yield_risk=82,equipment=77,delivery=75)
    b=certify_lot_decision('CERT-001',queue=88,yield_risk=82,equipment=77,delivery=75)
    assert a['decision_state']=='REVIEW_REQUIRED'
    assert a['human_gate'] is True
    assert a['autonomous_execution_allowed'] is False
    assert a['certificate_sha256']==b['certificate_sha256']
    assert len(a['certificate_sha256'])==64
