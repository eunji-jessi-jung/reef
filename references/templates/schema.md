---
id: "{ID}"
type: "schema"
title: "{Title in Title Case}"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "{FRESHNESS_NOTE}"
freshness_triggers: []
known_unknowns: []
tags: []
aliases: []
relates_to: []
sources: []
notes: ""
---

## Overview

{One to two paragraphs interpreting this data model: what it represents, why it is structured this way, and what assumptions it encodes. Do not restate the raw schema -- explain what it means.}

## Key Facts

- {Verifiable claim about the schema} → `{source_ref}`

## Entities

### {EntityName}

{What this entity represents in the domain and why it exists.}

**Key fields:**

| Field | Type | Significance |
|-------|------|-------------|
| {field_name} | {type} | {Why this field matters, not just what it stores} |

### {EntityName}

{Repeat for each significant entity.}

## Worked Examples

### Common Queries

{One or two representative join queries or access patterns showing how to use this schema. Use the actual table/collection names and field names from the schema above. Format as SQL, ORM pseudocode, or API call — whichever matches the tech stack.}

### Enum Values

{For every status, type, or category field in this schema, list all valid values with a one-line description of each. If exact values are unknown, add to known_unknowns instead of guessing.}

| Field | Value | Meaning |
|-------|-------|---------|
| {field_name} | {value} | {what it means in the domain} |

## Related

- [[{ARTIFACT_ID}]] -- {relationship description}
