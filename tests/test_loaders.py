import json
from fabops.ingestion.loaders import load_jsonl, load_csv

def test_jsonl_loader(tmp_path):
    p=tmp_path/'e.jsonl'; p.write_text(json.dumps({'event_id':'abc','event_type':'lot_released','timestamp':1,'lot_id':'L1'})+'\n')
    assert load_jsonl(p)[0].lot_id=='L1'

def test_csv_loader(tmp_path):
    p=tmp_path/'e.csv'; p.write_text('event_id,event_type,timestamp,lot_id,step\nabc,queued,2.5,L1,2\n')
    e=load_csv(p)[0]; assert e.timestamp==2.5 and e.step==2
