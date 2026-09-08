# Canonical Fab Event Contract

Every operational event contains `event_id`, `event_type`, non-negative `timestamp`, optional `lot_id`/`tool_id`, product/step/recipe fields where applicable, quantity, payload, source and ingestion timestamp.

Supported event types are lot release, queue, process start/completion, tool down/up, hold start/release and scrap. Pydantic forbids undeclared top-level fields. Lot events require a lot identifier. Duplicate `event_id` values are idempotent in persistence and flagged during raw state replay.

The contract is deliberately MES-neutral. Production adapters should map source-specific events into this contract rather than leaking source schemas into simulation, optimization or AI layers.
