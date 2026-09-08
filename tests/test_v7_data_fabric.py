
from fabops.data_fabric.mes_simulator import generate_mes_stream
from fabops.data_fabric.validators import validate_events
from fabops.data_fabric.replay import replay_manufacturing_state
from fabops.genealogy.wafer_tree import build_wafer_genealogy
from fabops.equipment.digital_thread import build_equipment_threads
from fabops.process_control.spc import shewhart, ewma, cusum, analyze_metrology

def test_mes_stream_and_validation():
    events=generate_mes_stream(12,6,71)
    assert len(events)>100
    v=validate_events(events)
    assert v["valid"] is True and not v["duplicates"]

def test_state_replay_reconstructs_lots_tools():
    events=generate_mes_stream(10,6,72)
    s=replay_manufacturing_state(events)
    assert s["counts"]["lots"]==10
    assert s["counts"]["tools"]>=4

def test_wafer_genealogy_has_traceable_wafers():
    events=generate_mes_stream(16,6,73)
    g=build_wafer_genealogy(events)
    assert g["lot_count"]==16
    assert g["wafer_count"]>0
    assert any(v["operations"] for v in g["lots"].values())

def test_equipment_digital_thread():
    events=generate_mes_stream(20,6,74)
    d=build_equipment_threads(events)
    assert d["count"]>=4
    assert all(0<=x["health_score"]<=1 for x in d["tools"].values())

def test_spc_algorithms():
    values=[100,100.1,99.9,100.2,100.0,100.1,100.2,101.2,101.6,102.0]
    assert "signals" in shewhart(values)
    assert ewma(values)["state"] in {"STABLE","DRIFT"}
    assert cusum(values,100)["state"] in {"STABLE","ALARM"}
    assert analyze_metrology(values)["overall_state"] in {"STABLE","ALARM"}
