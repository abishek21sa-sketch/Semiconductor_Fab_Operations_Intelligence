from fabops.ingestion.events import FabEvent, FabEventType
from fabops.state.engine import WaferStateEngine

def test_state_reconstruction_and_completion():
    ev=[
      FabEvent(event_id="e-001",event_type="lot_released",timestamp=1,lot_id="L1",product="P1"),
      FabEvent(event_id="e-002",event_type="process_started",timestamp=2,lot_id="L1",tool_id="T1",step=1,recipe="R1"),
      FabEvent(event_id="e-003",event_type="process_completed",timestamp=5,lot_id="L1",tool_id="T1",step=1,payload={"route_complete":True}),
    ]
    s=WaferStateEngine().reconstruct(ev)
    assert s.lots["L1"].status=="completed"
    assert s.tools["T1"].status=="idle"
    assert s.to_dict()["wip"]==0

def test_duplicate_event_is_anomaly_not_double_apply():
    e=FabEvent(event_id="e-100",event_type=FabEventType.LOT_RELEASED,timestamp=1,lot_id="L1")
    s=WaferStateEngine().reconstruct([e,e])
    assert s.anomalies==["duplicate_event:e-100"]

def test_tool_double_booking_detected():
    ev=[
      FabEvent(event_id="a01",event_type="process_started",timestamp=1,lot_id="L1",tool_id="T1",step=1),
      FabEvent(event_id="a02",event_type="process_started",timestamp=2,lot_id="L2",tool_id="T1",step=1),
    ]
    s=WaferStateEngine().reconstruct(ev)
    assert any(x.startswith("tool_double_booked") for x in s.anomalies)
