import json
from fabops.governance import append_entry, verify_ledger


def test_hash_chain_detects_post_hoc_tampering(tmp_path):
    p = tmp_path / "ledger.jsonl"
    a = append_entry(p, event_type="LOT_DECISION_CERTIFIED", payload={"lot_id": "L1", "state": "REVIEW_REQUIRED"})
    b = append_entry(p, event_type="SUPERVISOR_REVIEW_REQUESTED", payload={"lot_id": "L1"})
    ok = verify_ledger(p)
    assert ok["valid"] is True and ok["entries"] == 2 and ok["head_sha256"] == b["entry_sha256"]
    rows = p.read_text().splitlines()
    first = json.loads(rows[0]); first["payload"]["state"] = "AUTO_RELEASE"
    rows[0] = json.dumps(first)
    p.write_text("\n".join(rows) + "\n")
    bad = verify_ledger(p)
    assert bad["valid"] is False and bad["first_invalid_sequence"] == 1


def test_same_payload_gets_unique_ledger_entry_but_certificate_can_remain_deterministic(tmp_path):
    p = tmp_path / "ledger.jsonl"
    a = append_entry(p, event_type="EVIDENCE_CAPTURED", payload={"x": 1})
    b = append_entry(p, event_type="EVIDENCE_CAPTURED", payload={"x": 1})
    assert a["entry_sha256"] != b["entry_sha256"]
    assert b["previous_sha256"] == a["entry_sha256"]
