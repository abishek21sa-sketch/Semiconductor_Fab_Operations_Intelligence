from __future__ import annotations
import json
from fabops.api.app import APP_VERSION
from fabops.semiconductor.chambers import chamber_state, form_batches, reticle_contention
from fabops.optimization.integrated_fab import optimize_integrated_schedule, demo_integrated_jobs
from fabops.optimization.stochastic_recovery import optimize_recovery
from fabops.services.training import train_predictive_suite

def main():
    ch=chamber_state(17)
    lots=[{"lot_id":f"B{i:02d}","bay":"DIFF","recipe":"D1","ready_time":float(i%5)} for i in range(12)]
    batches=form_batches(lots,max_wait=5)
    ret=reticle_contention([
      {"lot_id":"R1","reticle":"R-P1-L1","ready_time":0,"duration":3},
      {"lot_id":"R2","reticle":"R-P1-L1","ready_time":1,"duration":3},
      {"lot_id":"R3","reticle":"R-P1-L2","ready_time":0,"duration":2},
    ],24)
    sched=optimize_integrated_schedule(demo_integrated_jobs(17,12),48,17).to_dict()
    recovery=optimize_recovery().to_dict()
    suite=train_predictive_suite()
    predictive={k:v["metrics"] for k,v in suite.items()}
    out={"release":"FLAGSHIP_V5","version":APP_VERSION,
         "windows_hardening":{"predictive_estimators":[predictive[k].get("estimator") for k in predictive],
                              "sklearn_runtime_dependency":False},
         "chamber_engine":{"chambers":len(ch),"down":sum(x["status"]=="DOWN" for x in ch),"busy":sum(x["status"]=="BUSY" for x in ch)},
         "batching":{"batches":len(batches["batches"]),"mean_fill_rate":batches["mean_fill_rate"],
                     "max_batch_size":max((b["size"] for b in batches["batches"]),default=0)},
         "reticle_contention":{"requests":len(ret["assignments"]),"conflicts_detected":ret["conflicts"],"max_wait":ret["max_wait"]},
         "integrated_schedule":{"success":sched["success"],"jobs":len(sched["assignments"]),"queue_breaches":sched["queue_breaches"],
                                "reticle_conflicts":sched["reticle_conflicts"],"objective":sched["objective"]},
         "stochastic_recovery":{"action":recovery["action"],"expected_loss":recovery["expected_loss"],"cvar":recovery["cvar"],
                                "risk_aversion":recovery["risk_aversion"]},
         "predictive_models":predictive,
         "claim_boundary":"Reference virtual-fab validation; no site-calibrated performance, production execution, or realized-impact claim."}
    print(json.dumps(out,indent=2))
    return out
if __name__=="__main__": main()
