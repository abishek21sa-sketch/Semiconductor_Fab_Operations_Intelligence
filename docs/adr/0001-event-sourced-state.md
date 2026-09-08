# ADR-0001 — Event-sourced wafer state

**Decision:** reconstruct operational lot/tool state from ordered canonical events rather than maintaining an opaque mutable singleton.

**Why:** deterministic replay, point-in-time inspection, auditability and easier integration with future MES streams outweigh the small local complexity cost.

**Consequence:** source adapters must produce stable event identifiers and timestamps. Duplicate handling is explicit.
