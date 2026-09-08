from fabops import __version__
def test_v2_health(client):
    assert client.get('/health').json()['version'] == __version__


def test_bay_risk_api(client):
    assert client.post('/control/bay-risk', json=[{"bay": "PHOTO", "wip": 5, "wip_limit": 10}]).status_code == 200


def test_rare_api(client):
    lots = [{"lot_id": "L1", "workload": {"PHOTO": 1}}, {"lot_id": "L2", "workload": {"PHOTO": 1}}]
    slots = [{"slot": 0, "wip_limit": 1, "capacity": {"PHOTO": 1}}, {"slot": 1, "wip_limit": 1, "capacity": {"PHOTO": 1}}]
    r = client.post('/optimize/rare-fab', json={"lots": lots, "slots": slots, "scenarios": [{"queue": 1.2}]})
    assert r.status_code == 200 and len(r.json()['assignments']) == 2
