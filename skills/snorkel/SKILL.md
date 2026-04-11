---
description: "Auto-discover 5-10 draft artifacts per source from code"
---

# reef:snorkel

Question-guided auto-discovery. Reads source code, uses the discovery question bank for direction, and produces 5-10 draft artifacts per source. No user input needed.

The key difference from a blind scan: snorkel reads the question bank and uses it to decide what to look at, what to document, and what to flag as unknown. Questions are the steering mechanism.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for project name, source paths, and service groupings. If no sources: "No sources configured. Run `/reef:init` to add source paths."
3. **Read `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`** — voice and personality.
4. **Read `.reef/questions.json`** — the discovery questions. These steer what you investigate and document.
5. **Read existing artifacts** in `artifacts/` to avoid duplicates.

### Resume detection

After loading context, check if snorkel has already partially run by comparing existing artifacts against what `project.json` services would produce:

- Count existing SYS-, SCH-, API-, CON-, GLOSSARY-, PROC-, RISK-, DEC- artifacts
- Compare against the number of services and source repos configured

If artifacts already exist:

```
Found existing snorkel artifacts:
  SYS-: N (expected: M based on services)
  SCH-: N (expected: M based on schemas)
  CON-: N (expected: M based on service pairs)
  PROC-: N (auth + runtime)
  RISK-: N
  DEC-: N
  GLOSSARY-: N

Options:
  1. Continue — skip services that already have artifacts, generate the rest
  2. Start fresh — regenerate all artifacts from scratch
  3. Exit — reef looks complete, suggest /reef:scuba instead
```

If all expected artifacts exist, suggest `/reef:scuba` and exit unless the user insists.

Note: The artifact contract and templates are embedded inline in Step 5 below. You do not need to read them separately.

---

## Step 1 — Refresh the source index

Report: "Refreshing the source index..."

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index --reef <reef-root>
```

Report results in natural language.

---

## Step 2 — Generate discovery questions

Read `${CLAUDE_PLUGIN_ROOT}/references/understanding-template.md`. For snorkel, focus on the **Snorkel (S1-S8)** questions.

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

## Step 3 — Question-guided structural scan

For each source in project.json:

1. Read the 2-level directory tree.
2. Read README.md if present.
3. Identify entry points, routers/handlers, models/schemas, config, tests, API definitions.
4. Note the tech stack.
5. Flag cross-system boundaries (imports, HTTP clients, shared schemas).

**Check for multiple applications within a single source.** Some repos are internal monorepos — one git repo containing multiple independent applications with their own entry points, models, databases, or API surfaces. Common signals:
- Multiple `main.py` / `app.py` entry points in separate directories
- Multiple FastAPI/Flask/Express apps under an `applications/`, `services/`, or `apps/` directory
- Separate database configurations or ORM model sets per sub-directory
- A workspace orchestrator (Nx, Turborepo, Cargo workspace) managing multiple packages

When you find this: treat each sub-application as a **distinct sub-domain**. Generate separate SCH- and API- artifacts for each (e.g., `SCH-PAYMENTS-GATEWAY`, `SCH-PAYMENTS-LEDGER`, `API-PAYMENTS-GATEWAY`, `API-PAYMENTS-LEDGER`), not one combined artifact for the whole repo. The SYS- artifact stays as one per service — it describes the overall system and references the per-app schema/API artifacts.

The "3-6 artifacts per source" target scales up for multi-app sources. A repo with 4 independent apps may warrant 8-12 artifacts.

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

## Step 4 — Generate artifacts

Generate artifacts guided by what you learned. Every service has a **mandatory minimum set** — do not move to the next service until these are written.

### Mandatory per-service artifacts (generate ALL of these)

1. **SYS-** — one per service, always. The entry point artifact. Use orientation question findings.
2. **SCH-** — one per distinct data model. If the source has multiple independent apps with separate data models, generate one SCH- per app (e.g., SCH-PAYMENTS-GATEWAY, SCH-PAYMENTS-LEDGER). Even a thin draft with entity names and relationships is better than nothing — scuba will upgrade it from extracted ERDs.
3. **API-** — one per distinct API surface. Same multi-app rule as SCH-. Even a thin draft listing router files and endpoint groups is better than nothing — scuba will upgrade it from extracted OpenAPI specs.
4. **PROC- auth** — one per service. Every service has auth. Document the mechanism (JWT, API key, OAuth, session), enforcement point (middleware, decorator, gateway), and identity provider. 3-5 Key Facts.
5. **GLOSSARY-{SERVICE}** — one per service. Extract domain terms found during Step 3 scan. Template: `${CLAUDE_PLUGIN_ROOT}/references/templates/glossary-service.md`.
6. **RISK-** — one per service. Scan for TODO/FIXME/HACK/XXX, bare exceptions, hardcoded URLs/credentials, disabled tests. Group by theme. Severity always "medium" at snorkel depth. Template: `${CLAUDE_PLUGIN_ROOT}/references/templates/risk-service.md`. If genuinely no signals found (rare), skip with a note.

### Cross-service artifacts (generate ALL of these)

7. **CON-** — one per service pair. For N services, generate exactly N×(N-1)/2 contracts. Name both parties, describe what flows between them (or note "no detected integration"). This is a completeness requirement — do not generate "some" and move on.
8. **GLOSSARY-** unified — one for the whole reef. Cross-service disambiguation. If you already have per-service glossaries, the unified glossary resolves conflicts and notes where the same term means different things.

### Conditional artifacts (generate when signal is present)

9. **PROC- runtime architecture** — generate when docker-compose, Helm, multiple entry points, or background workers are detected. 3-5 Key Facts on runtime topology.
10. **DEC-** for observable decisions — generate when the scan reveals a non-obvious technology or architecture choice (dual databases, custom auth, specific queue, sync-over-async). Stub with Context, Decision, and `known_unknowns: ["Rationale not available from code alone"]`.

### Minimum count validation

Before finishing a service, count its artifacts against this checklist:

```
Service {name} artifact count:
  SYS-:      {N} (minimum: 1)
  SCH-:      {N} (minimum: 1 per data model)
  API-:      {N} (minimum: 1 per API surface)
  PROC-auth: {N} (minimum: 1)
  GLOSSARY-: {N} (minimum: 1)
  RISK-:     {N} (minimum: 1)
  Total:     {N} (minimum: 6 per single-app service)
```

If any mandatory type shows 0, go back and generate it before proceeding. A thin draft is always better than a missing artifact — scuba needs the skeleton to build on.

**Target: 6-10 artifacts per source.** For a 4-source reef, that means 24-40 service artifacts + N×(N-1)/2 contracts + 1 unified glossary. Multi-app sources (monorepos with 3+ sub-apps) should generate 8-12 artifacts.

**Parallelism:** Artifact generation is independent per service. Use the Agent tool to generate all artifacts for multiple services concurrently — launch one agent per service, each responsible for that service's full artifact batch (SYS-, SCH-, API-, PROC-, RISK-, etc.). All agents in a single message.

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
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id-lowercase> --reef <reef-root>
```

**e. Present to the user.** Show each artifact one at a time as it's written.

---

## Step 5 — Spec-driven artifact upgrade

If `/reef:source` ran in parallel with snorkel, extracted API specs and ERDs are now available in `sources/apis/` and `sources/schemas/`. Use them to upgrade draft artifacts from surface-level summaries to spec-accurate documentation.

**When to run:** Only if `sources/apis/` or `sources/schemas/` contain extracted specs. If both directories are empty, skip to Step 6 — source extraction may not have been configured or may still be running.

**For each API- artifact with `freshness_note` containing "snorkel":**

1. Find the matching spec: `sources/apis/{service}/{sub}/openapi.json`.
2. Read the full OpenAPI spec — extract all endpoints, methods, request/response schemas, auth requirements, tags.
3. Rewrite the artifact body with complete endpoint documentation:
   - Group endpoints by tag/resource
   - Include request parameters and response schemas
   - Note auth requirements per endpoint
   - List error codes where specified
4. Update frontmatter:
   - `freshness_note: "upgraded from extracted OpenAPI spec"`
   - `known_unknowns`: remove items answered by the spec, keep others
   - Add `openapi.json` to `sources` list
5. Follow the full artifact contract (field order, validation, determinism rules).
6. Run snapshot after writing.

**For each SCH- artifact with `freshness_note` containing "snorkel":**

1. Find the matching schema: `sources/schemas/{service}/{sub}/schema.md`.
2. Read the full ERD — extract all tables/collections, fields, types, relationships.
3. Rewrite the artifact body with complete data model documentation:
   - All tables with full field lists (types, nullability, PK/FK, indexes)
   - Relationship cardinalities
   - **Mermaid `erDiagram` block (REQUIRED)** — this is a hard requirement, not optional. Every SCH- upgraded from an ERD must include a Mermaid ER diagram. Keep diagrams concise: max 15 entities per diagram, split into multiple diagrams if larger.
4. Update frontmatter same as API artifacts.
5. Run snapshot after writing.

**Quality mandates for spec-driven upgrades:**

- Every SCH- upgraded from an ERD **must** include a Mermaid `erDiagram` block. No exceptions.
- Every API- upgraded from OpenAPI **must** include one worked JSON request/response example for the most representative endpoint. Place it in a `### Worked Example` subsection after the endpoint tables.

**Parallelism:** Each artifact upgrade is independent. Use the Agent tool to upgrade all eligible SCH- and API- artifacts concurrently — launch one agent per artifact, all in a single message.

**After all upgrades:** Report what was upgraded:

```
Upgraded N artifacts from extracted specs:
- api-{service}: {N} endpoints (was {M} in draft)
- sch-{service}: {N} tables (was {M} in draft)
```

---

## Step 6 — Glossary cross-check

After all artifacts are written (including the GLOSSARY- artifact), do a glossary validation pass:

1. Read the GLOSSARY- artifact(s).
2. For each non-glossary artifact, scan Key Facts, Overview, and Core Concepts for domain terms defined in the glossary.
3. If any term is used with a meaning that contradicts the glossary definition, fix the artifact to align — or update the glossary if the artifact's usage is more accurate.
4. If any glossary-defined term is used ambiguously (e.g., "Case" without specifying which service when the glossary flags it as a disambiguation), add the qualifier.

This prevents drift between artifacts and the glossary from the very first generation. It is fast — just a string-matching pass over terms, not a deep re-read.

---

## Step 7 — Bidirectional linking pass

After all artifacts are written, do a linking pass to ensure the Obsidian graph is fully connected:

1. Read the frontmatter of every artifact just generated.
2. For each `relates_to` entry, check whether the target artifact links back. For example, if `SCH-ORDERS-CORE` has `relates_to: [{type: "parent", target: "[[SYS-ORDERS]]"}]`, then `SYS-ORDERS` must have a corresponding entry pointing to `SCH-ORDERS-CORE` (e.g., `{type: "refines", target: "[[SCH-ORDERS-CORE]]"}`).
3. If the reverse link is missing, add it. Use the appropriate inverse relationship:
   - `parent` ↔ `refines` (child→parent / parent→child)
   - `depends_on` ↔ `feeds` (consumer→producer / producer→consumer)
   - `constrains` — add reverse `constrains` on the target
   - `integrates_with` — always bidirectional, add if missing
4. Also ensure the `## Related` section's wikilinks match the updated `relates_to` frontmatter.
5. Re-snapshot any artifact that was modified.

This pass is critical for Obsidian graph view — unlinked nodes appear as disconnected islands.

---

## Step 8 — Update question bank

After generating artifacts, update `.reef/questions.json`:

- Mark questions as `"answered"` if the artifacts fully address them
- Mark as `"partial"` if artifacts touch on it but gaps remain
- Leave as `"unanswered"` if the snorkel pass couldn't address them

This gives `/reef:test` and `/reef:scuba` a clear picture of what's covered and what needs deeper work.

---

## Step 9 — Wrap up

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Snorkel pass: generated N artifacts, answered M/T questions" --reef <reef-root>
```

**Run the audit** to verify mandatory minimums are met:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py audit --reef <reef-root>
```

If the audit reports missing artifacts, generate them now before proceeding. Each missing artifact is independent — launch one agent per gap. A thin draft is always better than a missing artifact.

Then run the health report:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff --reef <reef-root>
```

Render a compact health summary using this exact format (copy the Unicode box-drawing characters directly):

```
Reef Health — {project name}                         {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources          Files    Seen   Deep   Freshness
────────────────────────────────────────────────
{source}         {N}      {N}    {N}    {bar} {status}

Artifacts        Total    Fresh  Aging  Stale  Errors
────────────────────────────────────────────────
{TYPE-}          {N}      {N}    {N}    {N}    {N}

Issues: {N} errors · {N} warnings · {N} info
```

**Freshness bar:** 8 characters wide using `█` (filled) and `░` (empty), proportional to coverage. Example: `████████░░` = fresh, `██░░░░░░░░` = stale.
**Freshness status:** `fresh` (no source changes), `aging` (some changes), `stale` (many changes or old `last_verified`).

Populate from lint and diff output. Show every source and artifact type, even if counts are zero. This table must render completely — do not skip or truncate it.

Summarize:
- Artifacts created (list IDs and one-line descriptions)
- Questions answered vs remaining
- Key gaps discovered (the most important known_unknowns across artifacts)

Then suggest next steps:

"The snorkel pass answered M of T discovery questions. Draft artifacts are in place with honest gaps.

Next steps:
- `/reef:scuba` — automated deepening + Socratic exploration. Generates advanced artifacts (lifecycles, auth boundaries, dependency maps) then works through unanswered questions with you.
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

- **Follow the frontmatter schema and body sections in Step 4 exactly.**
- **Questions steer discovery.** Don't just scan blindly — use the question bank to decide what to investigate.
- **Artifact IDs**: uppercase prefix + uppercase domain/name, hyphen-separated.
- **Filenames**: lowercase ID + `.md`.
- **Source refs always relative** to source root.
- **Stop when diminishing returns.** If a source is simple, 2-3 artifacts is fine. Don't pad.
- **Cross-system contracts always-on.** When code calls another system, flag it.
- **No user input.** Snorkel is fully automated. All interactive steps (service grouping, extract confirmation) happen in init before snorkel is triggered. Read, generate, report.

---

## If Called Without Init

If `.reef/questions.json` is empty or missing, Step 2 (Generate discovery questions) will create it. If `.reef/project.json` has no service groupings, snorkel will proceed without them — questions will be per-repo rather than per-service. Suggest the user run `/reef:init` for a better experience. Snorkel is self-sufficient — it can run standalone on any reef that has been scaffolded and indexed.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No sources**: "No sources configured. Run `/reef:init` to add source paths."
- **Source path missing**: warn, skip, continue with others.
- **reef.py fails**: report the error. Do not silently swallow.
- **No structures found in a source**: still generate a SYS- artifact with generous known_unknowns.
