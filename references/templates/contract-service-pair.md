# Service Pair CON- Template

Use this template for CON- artifacts that document the integration contract between two services.

**Naming convention:** `con-{service-a}-{service-b}` (alphabetical order, e.g., `con-auth-payments`, `con-payments-fulfillment`)

**When to use:** For every service pair in the reef, combinatorially. N services = N*(N-1)/2 contracts. All pairs must be covered — including pairs with no detected integration (documenting absence is valuable).

---

```yaml
---
id: "CON-{SERVICE-A}-{SERVICE-B}"
type: "contract"
title: "{Service A} ↔ {Service B} Integration Contract"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "scuba-depth service contract from code scan"
freshness_triggers:
  - "{path/to/client/code}"
  - "{path/to/api/endpoint}"
known_unknowns:
  - "Production failure behavior not confirmed"
  - "Retry/timeout semantics not fully traced"
tags: ["service-contract"]
aliases: []
relates_to:
  - { type: "parent", target: "[[SYS-{SERVICE-A}]]" }
  - { type: "refines", target: "[[SYS-{SERVICE-B}]]" }
sources:
  - { ref: "{path/to/client/code}", type: "code" }
  - { ref: "{path/to/api/spec}", type: "spec" }
notes: ""
---
```

## Parties

- **{Service A}**: {role — caller/provider/subscriber/publisher}
- **{Service B}**: {role — caller/provider/subscriber/publisher}

## Key Facts

- {Service A} calls {N} endpoints on {Service B} → `{client code path}`
- Auth: {how A authenticates to B} → `{source}`
- Transport: {REST/gRPC/events/shared DB/file drops} → `{source}`

## Integration Map

### {Direction: A → B}

| Endpoint/Topic | Method | Purpose | Auth | Used In |
|---------------|--------|---------|------|---------|
| {/api/v1/resource} | {GET/POST} | {what this call does} | {JWT/API key/service account} | {which flow uses this} |

### {Direction: B → A}

{Same table, or "No calls detected in this direction."}

## Data Flow

What data crosses the boundary? In what format?

- **Request payloads:** {key fields sent}
- **Response payloads:** {key fields returned}
- **Shared entities:** {entities that exist in both services — link to entity comparison CON- if applicable}

## Coupling Assessment

| Metric | Value |
|--------|-------|
| Call sites (A→B) | {N} |
| Call sites (B→A) | {N} |
| Shared schemas | {yes/no — list if yes} |
| Generated clients | {yes/no} |
| Coupling rating | {heavy / moderate / light / none} |

## Failure Behavior

- **What happens when {Service B} is down?** {timeout, retry, circuit breaker, fail-open, fail-closed, or unknown}
- **Retry logic:** {exponential backoff, fixed interval, none detected}
- **Timeout:** {configured value or "not configured"}

## No Integration Detected

{Use this section INSTEAD of the above if no integration evidence was found. Delete the Integration Map, Data Flow, Coupling Assessment, and Failure Behavior sections.}

These services appear to operate independently. No HTTP calls, shared schemas, event passing, or database sharing detected between them.

This confirms architectural separation — these services do not directly depend on each other.

## Related

- [[SYS-{SERVICE-A}]] -- party
- [[SYS-{SERVICE-B}]] -- party
