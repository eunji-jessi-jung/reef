---
id: "{ID}"
type: "pattern"
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

{What recurring design problem does this pattern address? Where does it appear — which services, which layers? One paragraph on the problem, one on the solution approach.}

## Key Facts

- {Verifiable claim about this pattern's implementation or usage} → `{source_ref}`

## Where It Appears

{Concrete instances of this pattern in the codebase. Show how the same approach manifests across different services or entities. If this is a cross-system comparison (same concept, different implementations), show the divergence side by side.}

## Design Intent

{Why this approach was chosen. What alternatives were considered or rejected. What constraint or business rule makes this the right choice. This section often requires human input — if the intent isn't clear from code alone, say so in known_unknowns.}

## Trade-offs

{What you gain and what you give up. Be specific: performance, complexity, coupling, flexibility, maintenance burden. Include edge cases where the pattern breaks down or requires workarounds.}

## Agent Guidance

{How should a code agent reason about this pattern when encountering it? What mistakes would an agent make without this context? Include negative rules ("never assume X means Y") where disambiguation matters.}

## Related

- [[{ARTIFACT_ID}]] -- {relationship description}
