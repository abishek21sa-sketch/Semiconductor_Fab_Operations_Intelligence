from fabops.operations.genealogy import route_catalog, lot_genealogy, queue_time_watch
from fabops.operations.maintenance import maintenance_calendar, setup_matrix
from fabops.operations.yield_genealogy import yield_genealogy
from fabops.operations.amhs_network import amhs_network
from fabops.experiments.experiment_manager import compare_stress_policies

def test_routes_are_reentrant_and_qualified():
    routes=route_catalog()
    assert set(routes)=={"P1","P2"}
    assert all(len(v)>=14 for v in routes.values())
    assert sum(x["bay"]=="PHOTO" for x in routes["P1"])>=3

def test_genealogy_has_queue_clocks_and_qualifications():
    g=lot_genealogy("LOT-017",17)
    assert g["route_length"]>=14
    assert any(x["reticle"] for x in g["operations"])
    assert all("queue_time_risk" in x for x in g["operations"])

def test_queue_time_watch_sorted():
    rows=queue_time_watch(17,20)
    assert rows[0]["fraction"]>=rows[-1]["fraction"]
    assert all(x["state"] in {"SAFE","AT_RISK","BREACH"} for x in rows)

def test_maintenance_calendar():
    x=maintenance_calendar(17,168)
    assert len(x["calendar"])==19
    assert x["due_24h"]>=0
    assert setup_matrix("PHOTO")["changeover_hours"][0][0]==0

def test_yield_genealogy_mass_balance():
    x=yield_genealogy(17,12)
    for lot in x["lots"]:
        assert abs(lot["expected_good_wafers"]+lot["rework_wafers"]+lot["scrap_wafers"]-25)<.2

def test_amhs_network_has_reentry():
    x=amhs_network(17)
    assert len(x["vehicles"])==8
    assert any(e["type"]=="REENTRANT" for e in x["edges"])

def test_experiment_manager():
    x=compare_stress_policies(31,40,.2)
    assert len(x["missions"])==5
    assert x["worst_case"] in {"PHOTO_OUTAGE","DEMAND_SURGE","AMHS_DEGRADATION","YIELD_EXCURSION","HOT_LOT_SURGE"}
