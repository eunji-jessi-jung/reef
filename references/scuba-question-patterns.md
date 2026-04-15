# Scuba Phase 2 — Question Patterns

Draw from these patterns, mapped to the understanding template C1-C10. Present one at a time, Socratic style — not as a dumped list.

**Entity lifecycle confirmation (C1):**
"I found {entity} has states {A, B, C} but I can only trace the A→B transition in code. What triggers B→C? Is it automatic, manual, or event-driven?"

**Critical workflow tracing (C2):**
"What are the most critical workflows in this service? I can trace the code path — you tell me what matters."

**Heavy dependency deep-dives (C3):**
"{Service-A} → {Service-B} has {N} endpoint calls across {M} flows. Want to trace the full integration contract — which flows call which endpoints, the auth model, the write-order semantics?"

**Operational reality (C4):**
"The code shows a {N}s timeout. Does that hold in production? What happens when {service} is slow or down?"

**Decisions and constraints (C5):**
"I see {pattern} in the code. Was this a deliberate architectural choice? What drove it?"

**Entity comparison confirmation (C6):**
"I found '{term}' means different things in {service-A} and {service-B}. Is this intentional? Do they ever need to align?"

**RBAC exploration (C7):**
"{Service} has {N} RBAC primitives. Want to document the full permission model — who can do what, where it's enforced, and what the edge cases are?"

**Concept taxonomy (C8):**
"{Service} uses '{concept}' {N} times across {M} directories. Is there a formal taxonomy? Want to document the different kinds?"

**Business logic surfacing (C9):**
"I found terms like '{term1}', '{term2}' that seem to carry business meaning beyond their technical implementation. Can you confirm what these mean to the business?"

**Version boundary exploration (C10):**
"{Service} has {versions} service layers. What's the migration story? Which versions are active, which are deprecated?"

**Data reconciliation (C4 extension):**
"If {service-A} uploads to {service-B} and it fails halfway, what happens? Is there reconciliation, retry, or manual intervention?"

**Tribal knowledge (open-ended):**
"What trips up every new engineer working in this area? What's the thing that isn't in the code?"
