# Flagship V7.1 — Manufacturing Data Fabric

V7.1 adds the first manufacturing data and traceability backbone above the validated V6 virtual-fab engine.

## Canonical event contract
A strict Pydantic event schema represents lot release, moves, processing, metrology, alarms, PM, tool state, scrap and rework. Events carry lot, wafer, tool, chamber, recipe, operation and payload context.

## Synthetic MES replay
The included MES simulator produces timestamped reference manufacturing events. The replay engine reconstructs lot, tool and wafer state deterministically from the append-only event stream.

## Wafer traceability
Wafer genealogy links wafer metrology observations to lot process history, operation sequence, tool, chamber and recipe.

## Equipment digital thread
Tool histories accumulate process counts, recipes, chambers, down events, PM events, alarms, health score and reference failure probability.

## Process control
The V7 process-health service implements:
- Shewhart 3-sigma monitoring,
- EWMA drift detection,
- CUSUM shift detection.

## Operator workspaces
V7 adds:
- Manufacturing Data Fabric,
- Wafer Traceability,
- Process Health / SPC.

## Evidence boundary
All included streams are synthetic/reference manufacturing events. V7.1 does not claim a live MES, SECS/GEM equipment connection, site-calibrated SPC limits, or production deployment.
