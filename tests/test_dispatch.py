import pytest
from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.dispatch import select_lot

def test_dispatch_rules_return_candidate():
    cfg=build_minifab_config(); lots=generate_lots(4,seed=3)
    for l in lots: l.queue_enter_time=l.release_time
    for rule in ["FIFO","EDD","SPT","CR","PRIORITY"]:
        assert select_lot(lots,10,lambda p:cfg.routes[p],rule) in lots

def test_invalid_rule():
    cfg=build_minifab_config(); lots=generate_lots(2)
    with pytest.raises(ValueError): select_lot(lots,0,lambda p:cfg.routes[p],"BAD")
