from __future__ import annotations
import json
from fabops.api.app import APP_VERSION
from fabops.operations.genealogy import route_catalog, queue_time_watch, lot_genealogy
from fabops.operations.maintenance import maintenance_calendar
from fabops.operations.yield_genealogy import yield_genealogy
from fabops.operations.amhs_network import amhs_network
from fabops.experiments.experiment_manager import compare_stress_policies

def main():
    routes=route_catalog(); q=queue_time_watch(17,36); pm=maintenance_calendar(17,168)
    y=yield_genealogy(17,28); net=amhs_network(17); exp=compare_stress_policies(31,70,.30)
    out={"release":"FLAGSHIP_V4","version":APP_VERSION,
         "fab_model":{"products":len(routes),"route_operations":{k:len(v) for k,v in routes.items()},
                      "photo_visits":{k:sum(x["bay"]=="PHOTO" for x in v) for k,v in routes.items()}},
         "queue_time":{"watched":len(q),"breach":sum(x["state"]=="BREACH" for x in q),"at_risk":sum(x["state"]=="AT_RISK" for x in q)},
         "maintenance":{"assets":len(pm["calendar"]),"due_24h":pm["due_24h"],"execute_windows":pm["execute_windows"]},
         "yield":{"mean_predicted_yield":y["mean_predicted_yield"],"rework_load_wafers":y["rework_load_wafers"],
                  "engineering_holds":y["engineering_holds"]},
         "amhs":{"vehicles":len(net["vehicles"]),"edges":len(net["edges"]),"congested_edges":net["congested_edges"],
                 "p95_transfer":net["network_p95_transfer"]},
         "experiment":{"id":exp["experiment_id"],"missions":len(exp["missions"]),"worst_case":exp["worst_case"]},
         "evidence_boundary":"Reference virtual-fab validation only; no production/site performance claim."}
    print(json.dumps(out,indent=2))
    return out
if __name__=="__main__": main()
