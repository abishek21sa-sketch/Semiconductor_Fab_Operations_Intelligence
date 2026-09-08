from __future__ import annotations

import json
from pathlib import Path

from fabops import __release__, __version__
from fabops.intelligence.lot_passport import build_lot_passport
from fabops.agents.decision_synthesizer import synthesize


def main():
    passport = build_lot_passport("V72-LOT-001")
    decision = synthesize(passport)
    assert passport["risk"]["level"] in ["LOW", "MEDIUM", "HIGH"]
    assert decision["human_gate"] is True
    out = {"release": __release__, "version": __version__, "status": "PASS", "lot": passport, "decision": decision}
    target = Path(__file__).resolve().parents[1] / "docs" / "validation" / "v72_validation_results.json"
    target.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("V72_DECISION_CENTER=PASS")


if __name__ == "__main__":
    main()
