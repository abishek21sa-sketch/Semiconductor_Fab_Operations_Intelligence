from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator

def test_all_lots_complete():
    lots=generate_lots(25,seed=1)
    result=FabSimulator(build_minifab_config(),seed=1).run(lots,"FIFO")
    assert result.throughput==25
    assert result.avg_cycle_time>0
    assert 0<=result.on_time_rate<=1

def test_reproducible():
    lots=generate_lots(20,seed=4)
    a=FabSimulator(build_minifab_config(),seed=9,failure_rate=.05).run(lots,"EDD")
    b=FabSimulator(build_minifab_config(),seed=9,failure_rate=.05).run(lots,"EDD")
    assert a.avg_cycle_time==b.avg_cycle_time
    assert a.avg_tardiness==b.avg_tardiness

def test_reentrant_litho_occurs_twice():
    result=FabSimulator(build_minifab_config()).run(generate_lots(3,seed=2),"FIFO")
    starts=[e for e in result.event_log if e["event"]=="start" and e["lot_id"]=="LOT-0001" and e["tool_id"].startswith("LITHO")]
    assert len(starts)==2
