---
id: "{ID}"
type: "process"
title: "{TITLE}"
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

## Purpose

{One to two paragraphs explaining what this process accomplishes, when it runs, and why it exists.}

## Key Facts

- {Verifiable claim about this process} → `{source_ref}`

<!-- The body section below adapts to the process archetype.
     Use exactly one of the following based on the nature of the process:

     LIFECYCLE archetype — for entities that move through states:
       ## States
       ### {State Name}
       - **Entry conditions:** {what causes transition into this state}
       - **Exit conditions:** {what causes transition out}
       - **Invariants:** {what must be true while in this state}

     WORKFLOW archetype — for step-by-step procedures:
       ## Steps
       1. **{Step Name}** — {what happens and who/what does it}
       2. **{Step Name}** — {what happens and who/what does it}

     PIPELINE archetype — for data transformation chains:
       ## Phases
       ### {Phase Name}
       - **Input:** {what enters this phase}
       - **Transform:** {what happens to it}
       - **Output:** {what leaves this phase}

     EVENT-DRIVEN archetype — for reactive/event-based processes:
       ## Triggers
       ### {Event Name}
       - **Source:** {where this event originates}
       - **Handler:** {what processes it}
       - **Side effects:** {what changes as a result}
-->

{ARCHETYPE-DEPENDENT BODY SECTION}

## Related

- [[{ARTIFACT_ID}]] -- {relationship description}
