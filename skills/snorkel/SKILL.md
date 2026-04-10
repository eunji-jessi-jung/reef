---
description: "Auto-discover 3-6 draft artifacts from source code"
---

# reef:snorkel

Question-guided auto-discovery. Reads source code, uses the discovery question bank for direction, and produces 3-6 draft artifacts per source. No user input needed.

The key difference from a blind scan: snorkel reads the question bank and uses it to decide what to look at, what to document, and what to flag as unknown. Questions are the steering mechanism.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for project name, source paths, and service groupings. If no sources: "No sources configured. Run `/reef:init` to add source paths."
3. **Read `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`** — voice and personality.
4. **Read `.reef/questions.json`** — the discovery questions. These steer what you investigate and document.
5. **Read existing artifacts** in `artifacts/` to avoid duplicates.

Note: The artifact contract and templates are embedded inline in Step 5 below. You do not need to read them separately.

---

## Step 1 — Refresh the source index

Report: "Refreshing the source index..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

Report results in natural language.

---

## Step 2 — Extract API specs and ERDs

If API frameworks or ORMs are detected in any source, run extraction automatically. Read `/Users/jessi/Projects/seaof-ai/reef/skills/extract/SKILL.md` and follow its instructions using the "Called from init" integration mode (skip context loading and re-indexing). The extracted specs land in `sources/raw/`.

If no API frameworks or ORMs are detected, skip this step silently. Do not ask the user.

---

## Step 3 — Generate discovery questions

Read `/Users/jessi/Projects/seaof-ai/reef/references/understanding-template.md`. For snorkel, focus on the **Snorkel (S1-S8)** questions.

For each source, do a quick structural scan:
- Read the 2-level directory tree
- Identify entry points, routers, models, config, tests
- Note the tech stack

Adapt the template questions to what you found. For each source, generate 8-15 specific questions:
- **Concrete, not generic.** Instead of "What are the core entities?", write "What are the core entities in order-service and how do Order, LineItem, and Payment relate?" if you see those model names.
- **Answerable from code.** Every question should be something you can investigate by reading source files.
- **Ordered by discovery priority:** System boundaries first, then data model, then API surface, then cross-system.

For multi-source reefs, add cross-system questions using the service groupings:
- **Within a service**: "How do pay-gateway and pay-ledger divide responsibilities within Payments?"
- **Across services**: "What data flows from Orders to Fulfillment?" / "What contracts exist between Payments and Inventory?"

Write to `.reef/questions.json`:
```json
{
  "questions": [
    {
      "id": "Q-001",
      "text": "What are the system boundaries and external dependencies of order-service?",
      "source": "order-service",
      "phase": "snorkel",
      "added": "2026-04-10",
      "status": "unanswered"
    }
  ]
}
```

Report: "Generated N discovery questions across M sources."

Show the questions briefly — a numbered list, grouped by service. Do not ask for approval. Move on.

---

## Step 4 — Question-guided structural scan

For each source in project.json:

1. Read the 2-level directory tree.
2. Read README.md if present.
3. Identify entry points, routers/handlers, models/schemas, config, tests, API definitions.
4. Note the tech stack.
5. Flag cross-system boundaries (imports, HTTP clients, shared schemas).

**Now use the question bank to go deeper.** For each question tagged to this source (or untagged):

- **Orientation questions** (boundaries, dependencies): Read entry points, config, dependency files. Trace imports to external services. Identify databases, queues, auth providers.
- **Data questions** (entities, relationships, state machines): Read model files thoroughly. Map entity names, relationships, field types. Look for status/state fields that indicate lifecycles.
- **Behavior questions** (workflows, error handling): Read router/handler files. Trace the main request paths. Note middleware, decorators, and error handlers.
- **Cross-system questions**: Search for HTTP clients, message publishers/consumers, shared schema imports. Map which source calls which.

For each question you can answer from code, note:
- **Fact**: what you found
- **Source**: which files (relative paths)
- **Confidence**: high (directly visible in code) / medium (inferred from structure) / low (guessing)
- **Open questions**: what you cannot determine from a surface read

Report progress as you go: "Reading service-a's model layer — found 14 SQLAlchemy models across 6 files...", "Tracing the auth middleware — JWT validation with role-based access control...", "Found HTTP client for service-b in clients/service_b.py — flagging as cross-system boundary..."

---

## Step 5 — Generate artifacts

Generate artifacts guided by what you learned. For each source, produce:

1. **SYS-** first — always. This is the entry point artifact. Use orientation question findings to write a rich overview with real boundaries, dependencies, and tech stack details.
2. **SCH-** for major data models — use data question findings. Name actual entities, describe relationships, note lifecycle states.
3. **API-** for API surfaces — use behavior question findings. Group endpoints, note auth patterns, describe key request flows.
4. **GLOSSARY-** if domain terms emerged that need definition.
5. **CON-** for cross-system boundaries — use cross-system question findings. Name both parties, describe what flows between them, cite the client/server code.

**Target: 3-6 artifacts per source.** For a 4-source reef, that means 12-24 artifacts total. Adjust based on codebase complexity — a simple service might only warrant 2-3, a complex one might need 6.

### For each artifact

**a. Generate frontmatter** using this exact field order. Do NOT deviate:

```yaml
---
id: "SYS-ORDERS"                        # uppercase prefix + uppercase slug
type: "system"                           # lowercase type matching prefix
title: "Order Management Service"        # human-readable
domain: "orders"                         # domain slug
status: "draft"                          # always "draft" for snorkel
last_verified: 2026-04-10               # unquoted ISO date, today
freshness_note: "snorkel-depth scan"     # never empty
freshness_triggers:                      # sorted alphabetically
  - "src/models/order.py"
  - "src/services/workflow.py"
known_unknowns:                          # generous — list what you could NOT answer
  - "Retry logic for failed payments unclear"
tags:
  - orders
  - fastapi
aliases:
  - "OMS"
relates_to:                              # sorted by target
  - type: "feeds"
    target: "[[SYS-FULFILLMENT]]"
sources:                                 # sorted by ref
  - category: "implementation"
    type: "github"
    ref: "src/main.py"
notes: ""
---
```

**b. Write body sections** based on artifact type:

| Type | Prefix | Required Sections |
|------|--------|-------------------|
| System | SYS- | Overview, Key Facts, Responsibilities, Core Concepts, Related |
| Schema | SCH- | Overview, Key Facts, Entities (with field tables), Related |
| API | API- | Overview, Key Facts, Source of Truth, Resource Map (endpoint tables), Related |
| Process | PROC- | Purpose, Key Facts, then ONE of: States (lifecycle), Steps (workflow), Phases (pipeline), Triggers (event-driven), Related |
| Decision | DEC- | Context, Decision, Key Facts, Rationale, Consequences (Positive/Negative/Neutral), Related |
| Glossary | GLOSSARY- | Overview, Terms (table: Term / Definition / See Also), Related |
| Contract | CON- | Parties, Key Facts, Agreement, Current State, Related |
| Risk | RISK- | Description, Key Facts, Impact, Severity+Resolution, Related |

**Key Facts format** (required for all types except Glossary):
```markdown
## Key Facts
- Order status transitions enforced at service layer → src/services/order.py
- Payment webhook triggers fulfillment flow → src/handlers/payment_webhook.py
- No retry mechanism for failed inventory checks → known gap
```

Each fact is an atomic, verifiable claim linked to its source with `→`.

**c. Write the file** to the correct subdirectory. Filename: lowercase ID + `.md` (e.g., `sys-orders.md`).

**d. Snapshot:**
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id-lowercase> --reef <reef-root>
```

**e. Present to the user.** Show each artifact one at a time as it's written.

---

## Step 6 — Update question bank

After generating artifacts, update `.reef/questions.json`:

- Mark questions as `"answered"` if the artifacts fully address them
- Mark as `"partial"` if artifacts touch on it but gaps remain
- Leave as `"unanswered"` if the snorkel pass couldn't address them

This gives `/reef:test` and `/reef:scuba` a clear picture of what's covered and what needs deeper work.

---

## Step 7 — Wrap up

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Snorkel pass: generated N artifacts, answered M/T questions" --reef <reef-root>
```

Then run the health report:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py lint --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py diff --reef <reef-root>
```

Render a compact health summary using the `/reef:health` report format (text table with Unicode box-drawing). This gives the user an immediate visual sense of coverage and freshness.

Summarize:
- Artifacts created (list IDs and one-line descriptions)
- Questions answered vs remaining
- Key gaps discovered (the most important known_unknowns across artifacts)

Then suggest next steps:

"The snorkel pass answered M of T discovery questions. The remaining gaps are areas where code alone is not enough — domain context, decision rationale, operational reality.

- `/reef:scuba` — work through the unanswered questions together. You bring the domain knowledge, I read the code.
- `/reef:deep` — exhaustive line-by-line tracing of a specific area.
- `/reef:test` — see how well the reef answers your questions right now."

If the key gaps include things that existing documents could answer (architecture decisions, deployment topology, authorization models, business rules), add:

"Some of these gaps might be answered by existing docs — PRDs, architecture specs, design docs, SRS. If you have any, `/reef:feed` can pull them in and the next pass will use them."

Only mention this if the gaps are genuinely the kind that docs would fill. Do not mention it if the gaps are code-level (e.g., "unclear error handling in module X").

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration.
- No emojis. No exclamation marks.
- Honest about uncertainty. Generous known_unknowns. When guessing, say so.
- Flag cross-system boundaries immediately when found.
- Do not narrate every file. Summarize at the source level, call out interesting findings.

---

## Key Rules

- **Follow the frontmatter schema and body sections in Step 5 exactly.**
- **Questions steer discovery.** Don't just scan blindly — use the question bank to decide what to investigate.
- **Artifact IDs**: uppercase prefix + uppercase domain/name, hyphen-separated.
- **Filenames**: lowercase ID + `.md`.
- **Source refs always relative** to source root.
- **Stop when diminishing returns.** If a source is simple, 2-3 artifacts is fine. Don't pad.
- **Cross-system contracts always-on.** When code calls another system, flag it.
- **No user input.** Snorkel is fully automated. All interactive steps (service grouping, extract confirmation) happen in init before snorkel is triggered. Read, generate, report.

---

## If Called Without Init

If `.reef/questions.json` is empty or missing, Step 3 (Generate discovery questions) will create it. If `.reef/project.json` has no service groupings, snorkel will proceed without them — questions will be per-repo rather than per-service. Suggest the user run `/reef:init` for a better experience. Snorkel is self-sufficient — it can run standalone on any reef that has been scaffolded and indexed.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No sources**: "No sources configured. Run `/reef:init` to add source paths."
- **Source path missing**: warn, skip, continue with others.
- **reef.py fails**: report the error. Do not silently swallow.
- **No structures found in a source**: still generate a SYS- artifact with generous known_unknowns.
