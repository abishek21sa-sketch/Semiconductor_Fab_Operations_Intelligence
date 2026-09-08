from fabops.optimization.release_control import optimize_release

def test_release_respects_capacity():
    lots=[
      {"lot_id":"A","weight":10,"workload":{"LITHO":6,"ETCH":2}},
      {"lot_id":"B","weight":8,"workload":{"LITHO":5,"ETCH":3}},
      {"lot_id":"C","weight":3,"workload":{"LITHO":2,"ETCH":1}},
    ]
    r=optimize_release(lots,{"LITHO":8,"ETCH":5})
    assert r.success
    assert r.total_load["LITHO"] <= 8+1e-9
    assert "A" in r.selected_lots
