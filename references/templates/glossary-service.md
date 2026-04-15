# Per-Service GLOSSARY- Template

Use this template for GLOSSARY- artifacts that document domain terms specific to a single service.

**Naming convention:** `glossary-{service}` (e.g., `glossary-payments`, `glossary-fulfillment`)

**When to use:** One per service when the service has 5+ unique domain terms. Per-service glossaries are authoritative within their scope; the unified glossary aggregates and disambiguates across services.

---

```yaml
---
id: "GLOSSARY-{SERVICE}"
type: "glossary"
title: "{Service} Domain Glossary"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "scuba-depth glossary from artifact and code scan"
freshness_triggers:
  - "{path/to/source/root}"
known_unknowns:
  - "Some terms may have business meanings not captured in code"
tags: ["glossary"]
aliases: []
relates_to:
  - { type: "parent", target: "[[SYS-{SERVICE}]]" }
  - { type: "refines", target: "[[GLOSSARY-{UNIFIED}]]" }
sources:
  - { ref: "{path/to/source/root}", type: "code" }
notes: ""
---
```

## Terms

| Term | Definition | Code Location | See Also |
|------|-----------|---------------|----------|
| {term} | {what it means in this service's context} | `{file:class/function}` | [[PROC-{SERVICE}-{ENTITY}-LIFECYCLE]] |

Focus on terms that carry domain meaning — not generic programming terms. Include:
- Entity names and what they represent
- Status/state values and their business meaning
- Acronyms used in this service's code
- Domain-specific field names (e.g., "order_hash", "item_type")

## Disambiguation

{Only include this section if terms in this service overlap with terms in other services.}

| Term | This Service Means | Other Service Means | Risk |
|------|-------------------|-------------------|------|
| {term} | {definition here} | {definition in other service} ([[GLOSSARY-{OTHER}]]) | {what goes wrong if confused} |

## Naming Conventions

- {Convention 1: e.g., "All entity IDs use UUID v4 except Account which uses hash-based IDs"}
- {Convention 2: e.g., "Endpoints use :verb suffix for non-CRUD actions (e.g., :finalize, :assign)"}
- {Convention 3: e.g., "MongoDB collections are singular (project, job), not plural"}

## Related

- [[SYS-{SERVICE}]] -- parent system
- [[GLOSSARY-{UNIFIED}]] -- unified cross-service glossary
