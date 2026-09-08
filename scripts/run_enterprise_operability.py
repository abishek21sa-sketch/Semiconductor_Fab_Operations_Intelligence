from __future__ import annotations
import json, tempfile, time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT/'src'):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
from fabops.governance import certify_lot_decision, append_entry, verify_ledger
from fabops.research.benchmark import rare_fab_benchmark

start=time.perf_counter()
with tempfile.TemporaryDirectory() as td:
    ledger=Path(td)/'audit.jsonl'
    cert=certify_lot_decision('OPS-CERT-001',queue=88,yield_risk=82,equipment=77,delivery=75)
    for i in range(25):
        append_entry(ledger,event_type='LOT_DECISION_CERTIFIED',payload={'sequence_case':i,'certificate_sha256':cert['certificate_sha256'],'decision_state':cert['decision_state']})
    chain=verify_ledger(ledger)
    lines=ledger.read_text().splitlines(); tampered=json.loads(lines[5]); tampered['payload']['decision_state']='AUTO_RELEASE'; lines[5]=json.dumps(tampered); ledger.write_text('\n'.join(lines)+'\n')
    tamper=verify_ledger(ledger)
bench=rare_fab_benchmark(seed=117,replications=4,lot_count=8)
elapsed=time.perf_counter()-start
checks={
    'certificate_human_gated':cert['human_gate'] is True and cert['autonomous_execution_allowed'] is False,
    'ledger_chain_valid_before_tamper':chain['valid'] is True and chain['entries']==25,
    'ledger_detects_tampering':tamper['valid'] is False,
    'rare_fab_benchmark_executes':bool(bench),
    'reference_runtime_under_30s':elapsed < 30,
}
payload={'phase':'ENTERPRISE_OPERABILITY_V1','status':'PASS' if all(checks.values()) else 'HOLD','checks':checks,'runtime_seconds':elapsed,'audit_chain_head':chain.get('head_sha256'),'certificate_sha256':cert['certificate_sha256'],'benchmark':bench,'claim_boundary':'Local reference-operability evidence; not live-fab cybersecurity, MES validation, or production authorization.'}
(ROOT/'artifacts'/'enterprise_operability.json').write_text(json.dumps(payload,indent=2,sort_keys=True,default=str))
print(json.dumps({'status':payload['status'],'checks':checks,'runtime_seconds':round(elapsed,3)},indent=2))
if payload['status']!='PASS': raise SystemExit('FABOPS_ENTERPRISE_OPERABILITY=HOLD')
print('FABOPS_ENTERPRISE_OPERABILITY=PASS')
