# V3 Mathematical Architecture

The V3 platform separates the fab decision stack into five layers:

**State layer:** event-sourced operational state and reference master data.

**Prediction/risk layer:** cycle-time/ETA/bottleneck models plus tool, yield, AMHS and bay-risk signals.

**Simulation layer:** re-entrant DES, Monte Carlo scenarios and named stress missions.

**Optimization layer:** dispatch comparisons, parallel-tool assignment, CONWIP release control, rolling-horizon qualified-tool scheduling and RARE-FAB CVaR release optimization.

**Decision layer:** evidence aggregation, ranked action alternatives, confidence/evidence class and mandatory supervisor disposition.

The architecture intentionally avoids using an LLM as the numerical decision engine. Mathematical and simulation outputs are computed first; any future language layer may explain those outputs but may not replace them.
