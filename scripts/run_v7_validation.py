
from __future__ import annotations
import json
from fabops.api.app import APP_VERSION
from fabops.data_fabric.mes_simulator import generate_mes_stream
from fabops.data_fabric.validators import validate_events
from fabops.data_fabric.replay import replay_manufacturing_state
from fabops.genealogy.wafer_tree import build_wafer_genealogy
from fabops.equipment.digital_thread import build_equipment_threads
from fabops.process_control.spc import analyze_metrology

def main():
    events=generate_mes_stream(50,6,71)
    validation=validate_events(events)
    state=replay_manufacturing_state(events)
    genealogy=build_wafer_genealogy(events)
    equipment=build_equipment_threads(events)
    vals=[float(e.payload["value"]) for e in events if e.event_type.value=="metrology_result" and e.payload.get("metric")=="cd_nm"]
    spc=analyze_metrology(vals or [100,100.1,99.9,100.2,100.0],100.0)
    out={
      "release":"FLAGSHIP_V7_1","version":APP_VERSION,
      "data_fabric":{"events":len(events),"valid":validation["valid"],"duplicates":len(validation["duplicates"]),
                     "anomalies":len(validation["anomalies"])},
      "state_replay":state["counts"],
      "wafer_genealogy":{"lots":genealogy["lot_count"],"wafers":genealogy["wafer_count"]},
      "equipment_thread":{"tools":equipment["count"],
                          "min_health":round(min((x["health_score"] for x in equipment["tools"].values()),default=1),3)},
      "process_control":{"observations":len(vals),"state":spc["overall_state"],
                         "ewma_state":spc["ewma"]["state"],"cusum_state":spc["cusum"]["state"]},
      "evidence_boundary":"Reference synthetic MES/data-fabric validation only; no live fab telemetry claim."
    }
    if not validation["valid"]: raise RuntimeError("V7 event validation failed")
    if state["counts"]["lots"]!=50: raise RuntimeError("V7 state replay lot count mismatch")
    if genealogy["wafer_count"]<=0: raise RuntimeError("V7 wafer genealogy produced no wafers")
    if equipment["count"]<=0: raise RuntimeError("V7 equipment thread empty")
    print(json.dumps(out,indent=2))
    print("V7_DATA_FABRIC_VALIDATION=PASS")
    return out

if __name__=="__main__":
    main()
