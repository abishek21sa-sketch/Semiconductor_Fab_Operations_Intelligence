# Validation Runbook

`python -m pytest` validates behavioral contracts. `python scripts/run_validation.py` regenerates `docs/validation/validation_results.json` from fixed seeds plus Monte Carlo replications.

A release is not portfolio-ready if either command fails. Quantitative statements must be copied from the generated artifact and described as synthetic benchmark results.
