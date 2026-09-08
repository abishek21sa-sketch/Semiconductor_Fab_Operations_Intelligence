def test_config_exposes_routes(client):
    r = client.get('/fab/config')
    assert r.status_code == 200
    assert 'routes' in r.json()


def test_simulation_has_risk_and_factory_physics(client):
    r = client.post('/simulate', json={"lots": 15, "rule": "CR", "seed": 2})
    assert r.status_code == 200
    j = r.json()
    assert 'risk' in j and 'little_law' in j and 'bottleneck' in j


def test_release_endpoint(client):
    body = {"lots": [{"lot_id": "A", "weight": 2, "workload": {"LITHO": 2}}], "capacity": {"LITHO": 3}}
    r = client.post('/optimize/release', json=body)
    assert r.status_code == 200 and r.json()['success']
