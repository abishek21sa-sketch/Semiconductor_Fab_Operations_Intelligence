from fabops.persistence.sqlite import FabRepository
from fabops.ingestion.events import FabEvent

def test_sqlite_event_idempotency(tmp_path):
    r=FabRepository(tmp_path/"fab.db")
    e=FabEvent(event_id="ev001",event_type="lot_released",timestamp=1,lot_id="L1")
    assert r.append_events([e])==1
    assert r.append_events([e])==0
    assert len(r.read_events())==1

def test_decision_audit_log(tmp_path):
    r=FabRepository(tmp_path/"fab.db")
    did=r.record_decision("dispatch",{"x":1},{"rule":"CR"})
    rows=r.list_decisions()
    assert rows[0]["decision_id"]==did
    assert rows[0]["response"]["rule"]=="CR"
