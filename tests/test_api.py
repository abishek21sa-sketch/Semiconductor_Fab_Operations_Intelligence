def test_root_operator_console(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'text/html' in r.headers.get('content-type', '')


def test_health(client):
    assert client.get('/health').json()['status'] == 'ok'


def test_simulate(client):
    r = client.post('/simulate', json={'lots': 10, 'rule': 'EDD', 'seed': 1})
    assert r.status_code == 200 and r.json()['throughput'] == 10


def test_recommend(client):
    r = client.post('/recommend/dispatch', json={'lots': 12, 'seed': 1})
    assert r.status_code == 200 and 'recommended_rule' in r.json()
