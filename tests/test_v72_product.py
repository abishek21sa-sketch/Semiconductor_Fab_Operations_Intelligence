from fabops import __release__, __version__
from fabops.agents.decision_synthesizer import synthesize
from fabops.intelligence.lot_passport import build_lot_passport
from fabops.api.app import APP_RELEASE, APP_VERSION


def test_release_contract_is_coherent():
    assert APP_VERSION == __version__ == "7.2.0"
    assert APP_RELEASE == __release__ == "FLAGSHIP_V7_2"


def test_lot_passport_and_decision_are_human_gated():
    passport = build_lot_passport("V72-LOT-001", queue=84, yield_risk=82, equipment=76, delivery=74)
    decision = synthesize(passport)
    assert passport["risk"]["level"] == "HIGH"
    assert passport["recommendation"] == "ENGINEERING_REVIEW"
    assert decision["human_gate"] is True
    assert decision["recommendation"] == "MOVE_LOT_AND_REVIEW_TOOL"
    assert decision["evidence"]
