def test_v3_mission_api(client):
    r=client.get('/v3/mission-control?lots=40')
    assert r.status_code==200
    j=r.json(); assert len(j['bays'])==8 and j['kpis']['throughput']==40

def test_v3_map_and_lot_apis(client):
    m=client.get('/v3/fab-map').json(); l=client.get('/v3/lots?count=20').json()
    assert any(x.get('type')=='REENTRANT' for x in m['links'])
    assert len(l['lots'])==20

def test_v3_demo_schedule_api(client):
    r=client.get('/v3/demo-schedule')
    assert r.status_code==200 and r.json()['success'] is True

def test_v3_stress_and_decision_apis(client):
    payload={'scenario':'PHOTO_OUTAGE','magnitude':.35,'seed':31,'lots':40}
    s=client.post('/v3/stress',json=payload); d=client.post('/v3/decision',json=payload)
    assert s.status_code==200 and d.status_code==200
    assert d.json()['human_gate']=='FAB_SHIFT_SUPERVISOR'

def test_root_is_operator_workstation(client):
    r=client.get('/')
    assert r.status_code==200
    assert 'FABOPS V7' in r.text and 'Mission Control' in r.text and 'RARE-FAB Lab' in r.text
