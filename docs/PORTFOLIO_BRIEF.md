# Portfolio Brief

Built an end-to-end **Semiconductor Fab Operations Intelligence Platform** around a reproducible re-entrant wafer-fab benchmark. The platform ingests MES-like events, reconstructs lot/tool state through deterministic event replay, persists operational evidence, simulates re-entrant production under stochastic disruptions, evaluates dispatch policies, optimizes qualified tool assignments and WIP release with MILP, estimates cycle time/ETA/bottleneck risk, and converts simulation/optimization evidence into explainable operational recommendations through FastAPI and an operator UI.

The repository demonstrates Industrial Engineering through Factory Physics, Little's Law, WIP control and bottleneck management; semiconductor manufacturing through wafer lots, re-entrant routes, recipes, qualification and setup behavior; Operations Research through dispatching and bounded MILP decision services; AI through three validated synthetic predictive baselines; simulation through a reproducible digital twin and Monte Carlo scenarios; and enterprise software engineering through contracts, persistence, modular APIs, tests, CI, containerization, runbooks and explicit evidence boundaries.

## Defensible interview statement

"I built a portfolio-scale semiconductor fab decision-intelligence platform that integrates event-sourced wafer state, a re-entrant discrete-event digital twin, dispatching, MILP release/assignment decisions, predictive models and simulation-backed recommendations. I validated the software and quantitative behavior on a synthetic MiniFab-inspired benchmark; I do not claim commercial-fab production validation."
