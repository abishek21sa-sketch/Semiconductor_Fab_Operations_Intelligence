"""Tamper-evident, human-gated decision certificates for portfolio release evidence."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from fabops import __release__, __version__
from fabops.agents.decision_synthesizer import synthesize
from fabops.intelligence.lot_passport import build_lot_passport


def certify_lot_decision(lot_id: str, **risk_inputs) -> dict:
    passport = build_lot_passport(lot_id, **risk_inputs)
    decision = synthesize(passport)
    state = "REVIEW_REQUIRED" if passport["risk"]["level"] == "HIGH" else "MONITOR"
    core = {
        "release": __release__,
        "version": __version__,
        "lot_id": lot_id,
        "decision_state": state,
        "recommendation": decision["recommendation"],
        "risk": passport["risk"],
        "evidence": decision["evidence"],
        "human_gate": True,
        "approval_authority": "FAB_SHIFT_SUPERVISOR",
        "autonomous_execution_allowed": False,
        "claim_boundary": "Reference/synthetic decision support only; no autonomous fab control or real-fab performance claim.",
    }
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        **core,
        "certificate_sha256": digest,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
