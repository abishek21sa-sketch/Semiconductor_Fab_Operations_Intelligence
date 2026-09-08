# Architecture

## Decision flow

`MES-like events -> canonical contract -> event store -> wafer/tool state -> analytics + digital twin -> prediction + optimization -> decision engine -> API -> operator UI`

The platform is intentionally decision-centric. Prediction is never the terminal product; model outputs and simulation evidence are downstream inputs to dispatch, release, scheduling and risk decisions.

## Bounded contexts

- **Domain**: lots, routes, operations, recipes, tools, qualification and state.
- **Ingestion**: strict canonical event contract and file adapters.
- **Persistence**: append/idempotent event storage plus scenario/decision audit records.
- **State**: point-in-time deterministic replay for lot/tool operational state.
- **Simulation**: re-entrant discrete-event twin and stochastic scenario engine.
- **Analytics**: Factory Physics, utilization and bottleneck diagnostics.
- **Optimization**: bounded rolling-horizon assignment and WIP-release decisions.
- **AI**: cycle-time regression, ETA prediction and bottleneck classification baselines.
- **Decision**: policy comparison, operational risk and evidence-backed recommendation.
- **API/UI**: application boundary for operators and external integrations.

## Production extension points

The canonical event contract is the anti-corruption boundary for future MES/equipment adapters. SQLite is a local reproducibility implementation; a production deployment can replace it behind the repository interface without changing upstream domain semantics. Predictive models are deliberately isolated so a model registry/serving layer can replace in-process objects later.

## Non-goals of this benchmark release

The repository does not emulate proprietary semiconductor data, claim SECS/GEM connectivity, or represent synthetic model performance as commercial-fab validation.
