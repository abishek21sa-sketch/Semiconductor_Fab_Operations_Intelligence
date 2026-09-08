from fastapi.testclient import TestClient
import importlib

api = importlib.import_module('fabops.api.app')


def test_audited_certificate_is_recorded_and_verifiable(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "AUDIT_LEDGER_PATH", str(tmp_path / "audit.jsonl"))
    c = TestClient(api.app)
    r = c.post('/v72/decision-certificate/audited', json={
        'lot_id':'MESLOT-GOV-1','queue':88,'yield_risk':82,'equipment':77,'delivery':75
    })
    assert r.status_code == 200
    assert r.headers['X-Request-ID'].startswith('fab-')
    assert float(r.headers['X-Response-Time-Ms']) >= 0
    b = r.json()
    assert b['certificate']['human_gate'] is True
    assert b['certificate']['autonomous_execution_allowed'] is False
    assert b['audit_ledger_valid'] is True
    v = c.get('/governance/audit/verify').json()
    assert v['valid'] is True and v['entries'] == 1
