# Entity Lifecycle PROC- Template

Use this template for PROC- artifacts that document a core domain entity — its definition, relationships, and lifecycle (if stateful).

**Naming convention:** `proc-{service}-{entity}-lifecycle` (e.g., `proc-cdm-case-lifecycle`, `proc-ctl-job-lifecycle`)

**When to use:** For every core entity identified in the scuba manifest. Core = 3+ non-FK fields, or API resource, or FK target for 2+ other entities.

---

```yaml
---
id: "PROC-{SERVICE}-{ENTITY}-LIFECYCLE"
type: "process"
title: "{Entity} Entity Definition and Lifecycle"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "scuba-depth entity definition + lifecycle from code scan"
freshness_triggers:
  - "{path/to/model/file}"
known_unknowns:
  - "Business rules governing state transitions need user confirmation"
  - "Side effects on transition not fully documented"
tags: ["entity-lifecycle"]
aliases: []
relates_to:
  - { type: "parent", target: "[[SYS-{SERVICE}]]" }
  - { type: "depends_on", target: "[[SCH-{SERVICE}-{SUB}]]" }
sources:
  - { ref: "{path/to/model/file}", type: "code" }
notes: ""
---
```

## Purpose

{What this entity represents in the domain. Why it exists. What role it plays in the system. 2-3 sentences.}

## Key Facts

- {Entity} is stored in {table/collection name} in {database} → `{model file path}`
- {Key business rule or constraint} → `{source}`
- {Relationship to other entities} → `{source}`

## Definition

### Fields

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| {field} | {type} | {yes/no} | {business meaning, not just technical type} |

Focus on fields that carry business meaning. Skip auto-generated fields (id, created_at, updated_at) unless they have special semantics.

### Relationships

- **Parent:** {entity} belongs to {parent entity} via `{fk_field}` → [[PROC-{SERVICE}-{PARENT}-LIFECYCLE]]
- **Children:** {child entities} reference this entity → [[PROC-{SERVICE}-{CHILD}-LIFECYCLE]]
- **Associations:** {many-to-many or cross-service relationships}

For junction tables that connect this entity to others, document them here (not as separate PROC- artifacts).

### Creation

How instances are created: API endpoint, background job, migration, external sync, etc. Cite the code path.

## States

{Only include this section if the entity has a status/state field. Otherwise, delete it.}

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> {InitialState}
    {InitialState} --> {NextState}: {trigger}
    {NextState} --> {FinalState}: {trigger}
    {FinalState} --> [*]
```

### {State Name}

- **Entry conditions:** {what causes transition into this state}
- **Exit conditions:** {what causes transition out}
- **Side effects:** {events published, downstream updates, notifications}
- **Irreversible?** {yes/no}

{Repeat for each state.}

## Related

- [[SYS-{SERVICE}]] -- parent system
- [[SCH-{SERVICE}-{SUB}]] -- schema definition
- [[PROC-{SERVICE}-{RELATED-ENTITY}-LIFECYCLE]] -- {relationship}
