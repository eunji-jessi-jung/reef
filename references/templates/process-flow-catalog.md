# Flow Catalog PROC- Template

Use this template for PROC- artifacts that enumerate all flows/pipelines/jobs within a service or subsystem.

**Naming convention:** `proc-{service}-flow-catalog` or `proc-{service}-{subsystem}-flow-catalog` (e.g., `proc-pipeline-flow-catalog`, `proc-pipeline-ingestion-flow-catalog`)

**When to use:** For services with pipeline orchestration (Prefect, Celery, Airflow), background job systems, or multi-step workflow processing. One per service or subsystem that has distinct flow sets.

---

```yaml
---
id: "PROC-{SERVICE}-FLOW-CATALOG"
type: "process"
title: "{Service} Flow Catalog"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "scuba-depth flow enumeration from code scan"
freshness_triggers:
  - "{path/to/flow/definitions}"
known_unknowns:
  - "Flow dependencies and ordering constraints not fully traced"
  - "Error recovery behavior not confirmed for all flows"
tags: ["flow-catalog"]
aliases: []
relates_to:
  - { type: "parent", target: "[[SYS-{SERVICE}]]" }
sources:
  - { ref: "{path/to/flow/definitions}", type: "code" }
notes: ""
---
```

## Purpose

{What this catalog covers. What orchestration framework is used. How many flows exist and what they collectively accomplish.}

## Key Facts

- {N} flows enumerated across {M} files → `{flow definition root}`
- Orchestration: {Prefect/Celery/Airflow/custom} → `{config path}`
- {Notable pattern: e.g., "all flows share a common retry decorator"} → `{source}`

## Flow Summary

| Flow | Trigger | Steps | Terminal States | Error Handling |
|------|---------|-------|----------------|----------------|
| {flow-name} | {manual/scheduled/event/upstream} | {N} | {success, failure, skipped} | {retry N times / fail-fast / dead-letter} |

## Flow Details

### {Flow Name}

**Trigger:** {What starts this flow — schedule, API call, upstream flow completion, event}
**Code:** `{path/to/flow/definition}`

**Phases:**

```mermaid
graph LR
    A[{Phase 1}] --> B[{Phase 2}]
    B --> C[{Phase 3}]
    C --> D[{Terminal}]
```

1. **{Phase 1 name}** — {what it does, key inputs}
2. **{Phase 2 name}** — {what it does, transforms applied}
3. **{Phase 3 name}** — {what it does, where output goes}

**Input:** {What data/parameters the flow requires}
**Output:** {What the flow produces — data written, APIs called, events emitted}

**Failure behavior:**
- {What happens on failure at each phase}
- {Retry semantics}
- {Alerting/notification}

**Dependencies:** {Other flows or services this flow depends on}

{Repeat for each flow.}

## Flow Dependencies

```mermaid
graph TD
    {flow-a} --> {flow-b}
    {flow-b} --> {flow-c}
    {flow-a} --> {flow-d}
```

{If flows have ordering dependencies, show the DAG. If flows are independent, state "All flows are independently triggerable."}

## Related

- [[SYS-{SERVICE}]] -- parent system
- [[PROC-{SERVICE}-{ENTITY}-LIFECYCLE]] -- {entity processed by flows}
