from fabops.data.minifab import build_minifab_config, generate_lots
from fabops.simulation.engine import FabSimulator
from fabops.ai.cycle_time import CycleTimeModel

def test_cycle_time_model_fit_predict():
    rec=FabSimulator(build_minifab_config(),seed=2).run(generate_lots(60,seed=2),"EDD").completed_lots
    m=CycleTimeModel(); metrics=m.fit(rec)
    assert metrics["train_n"]>0
    p=m.predict(rec[-1]); assert p>0
    assert abs(sum(m.feature_importance().values())-1)<.01
