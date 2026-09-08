from fabops.ai.eta import ETAModel
from fabops.ai.bottleneck import BottleneckModel

def test_eta_model_beats_naive_on_structured_fixture():
    records=[]
    for i in range(40):
        release=float(i*4); queue=float((i%5)*2); p='P2' if i%2 else 'P1'
        records.append({'lot_id':f'LOT-{i:04d}','priority':1+i%3,'release_time':release,'queue_time':queue,
                        'product':p,'completion_time':release+50+queue+(8 if p=='P2' else 0)})
    m=ETAModel(); metrics=m.fit(records,seed=1)
    assert metrics['mae'] < metrics['naive_mae']

def test_bottleneck_model_predicts_known_synthetic_pattern():
    rows=[]
    for i in range(40):
        f=.08 if i%2 else 0.0
        rows.append({'lots':50+i%3,'interarrival':5.0,'failure_rate':f,'repair_time':10.0,
                     'bottleneck':'LITHO-01' if f==0 else 'ETCH-01'})
    m=BottleneckModel(); metrics=m.fit(rows,seed=2)
    assert metrics['accuracy'] >= .8
    assert m.predict(52,5.0,.08,10.0)['predicted_bottleneck'] in {'LITHO-01','ETCH-01'}
