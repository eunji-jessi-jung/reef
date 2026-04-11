---
description: "Deepen knowledge through automated analysis and Socratic questioning"
---

# /reef:scuba

Two-phase knowledge deepening. Phase 1 runs automatically — generates advanced artifacts from what snorkel+source already produced. Phase 2 is interactive — surfaces what code cannot answer and guides the user through Socratic exploration.

Core principle: "AI found the answers. I asked the questions."

## MANDATORY — Completion checklist

You MUST complete these phases IN ORDER. Do NOT skip any. Do NOT jump ahead.

1. **Locate the reef** (Step 1)
2. **Load context** (Step 2)
3. **Build the artifact generation manifest** (Step 2.5) — explicit list of every artifact to produce
4. **Phase 1: Automated Deepening** (Step 3) — work through the manifest, NO user input needed
5. **Phase 1 Briefing** (Step 4) — present manifest completion status, ask user where to start Phase 2
6. **Phase 2: Interactive Q&A** (Step 5) — Socratic exploration, one question at a time
7. **Session management** (Step 6) — track progress, summarize at pauses

**CRITICAL: Phase 1 ALWAYS runs first.** Even if the user says "let's answer the questions" or "go through all of them" or similar — this means: run Phase 1 to auto-answer what code can reveal, THEN present findings in the briefing, THEN start Phase 2 for what code alone could not answer. The user's first interaction point is the Phase 1 briefing (Step 4), not before. Do NOT ask the user questions until Phase 1 is complete.

---

## Setup

Read these references before doing anything else:

- `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/understanding-template.md` — focus on Scuba (C1-C10) questions

## Voice

Curious Researcher at scuba depth. Conversational, Socratic — asking good questions, not interrogating. Present-participle narration for progress. Genuine curiosity about the domain. No emojis. No exclamation marks.

Honest about limits: "I can see the code does X, but I can not tell from the code alone why this design was chosen. Do you know the history?"

The user is the domain expert. Claude reads code; the user knows context.

---

## Step 1 — Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

---

## Step 2 — Load context

- Read `.reef/project.json` to understand scope, source roots, and service groupings.
- Read `.reef/questions.json` to see the question bank and what has been answered.
- Scan `artifacts/` for existing artifacts — read their frontmatter to understand current coverage.
- Read `sources/apis/` and `sources/schemas/` for extracted API specs and ERDs. These contain the complete endpoint maps and data models. If these directories are empty, note this and warn that Phase 1 will produce thinner results — suggest running `/reef:source` first.
- Read all GLOSSARY- artifacts — these are needed for entity comparison and glossary cross-checking.
- **Mine snorkel artifacts for deepening signals.** Read the full body (not just frontmatter) of every existing artifact — especially Key Facts, Core Concepts, and known_unknowns sections. Extract patterns, domain-specific mechanisms, and architectural findings that deserve deeper investigation. Examples of signals:
  - A named pattern (e.g., "outbox pattern", "saga orchestration", "event sourcing") → candidate for a PROC- artifact documenting the pattern
  - A domain-specific mechanism (e.g., "hash-based deduplication", "materialized views", "optimistic locking with version counters") → candidate for a PROC- or DEC- artifact
  - A cross-service coupling signal (e.g., "shared API client must be passed to service initializers") → candidate for deeper CON- artifact
  - A gap or uncertainty in known_unknowns that code reading could partially resolve

  **Categorize each signal as scuba-level or deep-level:**
  - **Scuba**: understand the pattern conceptually — what it is, which entities/services use it, why it exists, what it enables, how it differs from the standard approach. Produces PROC-, DEC-, or CON- artifacts.
  - **Deep**: trace the implementation exhaustively — field-by-field lineage, exact code paths, every edge case. Produces dense, line-cited artifacts. Flag these for `/reef:deep` rather than investigating in scuba.

  Collect scuba-level signals into a list for Phase 1 sub-step 3.9. Collect deep-level signals into a separate list for the Phase 1 briefing.

---

## Step 2.5 — Build the artifact generation manifest

**This is the most important step.** Before executing Phase 1, build an explicit, complete list of every artifact that Phase 1 must produce. Without this manifest, artifacts will be missed — Claude will generate "some" and move on.

### Resume detection

First, check if `.reef/scuba-manifest.json` already exists from a previous run:

- If it exists and has `completed` entries: report what was already done.

  ```
  Found existing scuba manifest:
    Completed: N artifacts
    Remaining: M artifacts
    Skipped:   K artifacts

  Options:
    1. Continue — pick up where you left off (generate remaining M artifacts)
    2. Start fresh — rebuild manifest and regenerate all artifacts
  ```

- If the user chooses "continue": load the existing manifest, skip completed items, and proceed to Phase 1 with only the remaining planned artifacts.
- If the user chooses "start fresh" or no manifest exists: build from scratch below.

### Building the manifest

Scan all sources and existing artifacts systematically:

### API- artifacts (from extracted specs)

List every `sources/apis/{service}/{sub}/openapi.json` file. Each one → one API- artifact.

```
Planned API- artifacts:
- API-{SERVICE}-{SUB} ← sources/apis/{service}/{sub}/openapi.json
  [exists: yes/no] [current artifact: {id} or none]
```

### SCH- artifacts (from extracted schemas)

List every `sources/schemas/{service}/{sub}/schema.md` file. Each one → one SCH- artifact.

```
Planned SCH- artifacts:
- SCH-{SERVICE}-{SUB} ← sources/schemas/{service}/{sub}/schema.md
  [exists: yes/no] [current artifact: {id} or none]
```

### PROC- entity artifacts (from schema entities)

For each SCH- artifact (existing or planned), read the schema and extract every entity (table or collection). Each **core entity** gets its own PROC- artifact covering definition, relationships, and lifecycle (if status fields exist).

**Core entity filter:** An entity is "core" if it has 3+ non-FK fields, OR appears as an API resource in any endpoint, OR is referenced as a FK target by 2+ other entities. Junction tables (2 FK columns only), audit log tables, and pure config tables are documented inside their parent entity's PROC- instead.

```
Planned PROC- entity artifacts:
- PROC-{SERVICE}-{ENTITY}-LIFECYCLE ← entity {Entity} from SCH-{SERVICE}-{SUB}
  [has status field: yes/no] [API resource: yes/no]
```

### CON- contract artifacts (from service pairs)

Compute all service pairs combinatorially. For N services, there are N×(N-1)/2 pairs. Each pair → one CON- artifact (or update to existing).

```
Planned CON- artifacts:
- CON-{SERVICE-A}-{SERVICE-B} [exists: yes/no]
```

### PROC- auth artifacts (from auth patterns)

One per service where auth patterns exist (detected during Step 2 context loading or from SYS- artifacts mentioning auth).

### PROC-/DEC- pattern artifacts (from snorkel signal mining)

One per scuba-level signal identified in Step 2.

### Summary

Print the full manifest with counts:

```
Artifact generation manifest:
  API-  artifacts: N planned (M new, K updates)
  SCH-  artifacts: N planned (M new, K updates)
  PROC- entities:  N planned (from X core entities across Y schemas)
  CON-  contracts: N planned (M new, K updates)
  PROC- auth:      N planned
  PROC-/DEC-:      N planned (from pattern signals)
  ──────────────
  Total:           N artifacts
```

Save the manifest to `.reef/scuba-manifest.json` with this structure:

```json
{
  "generated_at": "ISO timestamp",
  "planned": [
    { "id": "API-PAYMENTS-GATEWAY", "type": "api", "source": "sources/apis/payments/gateway/openapi.json", "status": "new" },
    { "id": "PROC-PAYMENTS-ORDER-LIFECYCLE", "type": "process", "source": "sources/schemas/payments/gateway/schema.md", "entity": "Order", "status": "new" }
  ],
  "completed": [],
  "skipped": []
}
```

**Phase 1 executes against this manifest.** After each artifact is written, move it from `planned` to `completed`. If a planned artifact turns out to be unnecessary (empty schema, no meaningful content), move it to `skipped` with a reason.

### Confirm before executing

After presenting the manifest summary, show an estimated cost and ask for confirmation:

```
Estimated Phase 1 cost:
  ~3-5 artifacts/min with parallelism
  {N} artifacts → ~{N/4} to {N/3} min, ~{N * 5}k-{N * 8}k tokens

Proceed with Phase 1? (yes / skip to Phase 2 / adjust scope)
```

If the user wants to adjust scope, let them remove categories from the manifest (e.g., "skip entity PROC- artifacts for now, just do API and SCH"). Update the manifest accordingly.

**Do NOT start Phase 1 without user confirmation.**

---

## Step 3 — Phase 1: Automated Deepening

No user input after confirmation. Work through the manifest systematically — every planned artifact must be addressed (completed or explicitly skipped with reason). Report progress as you go: "Writing API-PAYMENTS-GATEWAY (1/9 API artifacts)...", "Writing PROC-PAYMENTS-ORDER-LIFECYCLE (3/24 entity artifacts)...".

All Phase 1 artifacts are `status: "draft"`. Phase 2 can promote to `"active"` with user confirmation.

**Parallelism:** Where possible, use the Agent tool to process multiple independent artifacts concurrently. For example, launch one agent per API- artifact or one agent per service's entity batch.

### 3.1 — API pattern analysis

For each service with an extracted OpenAPI spec in `sources/apis/{service}/{sub}/openapi.json`:

1. Read the full spec.
2. Analyze and document:
   - **Surface profile**: path count, operation count, method split (GET/POST/PUT/PATCH/DELETE)
   - **Auth posture**: count operations with vs without security requirements. "All N operations auth-gated" or "M of N operations have no auth requirement"
   - **Non-CRUD action patterns**: scan for `:verb` suffix on path segments (e.g., `:finalize`, `:assign`, `:clone`). List them. Note: "these are workflow transitions, not plain resource mutations"
   - **Batch operations**: scan for `batch` or `Batch` in paths or operationIds
   - **Pagination convention**: scan for `page`/`page_size`/`limit`/`offset`/`cursor` on GET list endpoints
   - **Error code patterns**: scan response schemas for common error codes. Note which are most prevalent
   - **Contract limits**: what OpenAPI does NOT encode — business invariants, side effects, cross-entity invariants, idempotency semantics
3. **Output:** Write an API- artifact per service/sub as a "delta layer on top of OpenAPI" — not a duplication of endpoint tables, but agent-relevant interpretation. Include a "How Agents Should Use This" section. Set `freshness_note: "scuba-depth API pattern analysis"`.

### 3.2 — Comprehensive schema documentation

For each service with an extracted ERD in `sources/schemas/{service}/{sub}/schema.md`:

1. Read the full schema.
2. Document:
   - **Tech stack**: explicitly state the database (PostgreSQL, MongoDB, Redis) and ORM/ODM (SQLAlchemy, Beanie, GORM, Prisma)
   - **For RDB schemas**: full field tables with columns for Field, Type, Nullable, PK/FK, Index, Notes. Mermaid ERD diagram showing tables and FK relationships.
   - **For document stores (MongoDB)**: document nesting structure, embedded vs referenced fields, index strategies. Mermaid diagram showing document relationships.
   - **Entity descriptions**: what each table/collection represents, not just its fields
   - **Relationship cardinalities**: one-to-one, one-to-many, many-to-many with join table names
3. **Output:** Write or update SCH- artifacts per service/sub. Set `freshness_note: "scuba-depth schema documentation"`.

### 3.3 — Entity definition and lifecycle artifacts

Generate a PROC- artifact for every core entity listed in the manifest. Work through the manifest's PROC- entity list systematically. **Do not skip entities.**

**Naming:** `PROC-{SERVICE}-{ENTITY}-LIFECYCLE` (e.g., `PROC-CDM-CASE-LIFECYCLE`, `PROC-CTL-JOB-LIFECYCLE`). The `-LIFECYCLE` suffix distinguishes entity artifacts from workflow or pattern PROC- artifacts.

**Template:** Follow `/Users/jessi/Projects/seaof-ai/reef/references/templates/process-entity-lifecycle.md` exactly. It defines the full structure: Purpose, Key Facts, Definition (Fields table, Relationships, Creation), States (with Mermaid state diagram), and Related.

For each core entity:

1. **Read the source code** — find the model/schema definition file in the source repo. Read it to understand fields, relationships, validators, and business logic.
2. **Write the PROC- artifact** following the template. Key requirements:
   - **Fields table**: focus on business-meaningful fields, not a raw dump
   - **Relationships**: reference other PROC-{SERVICE}-{ENTITY}-LIFECYCLE artifacts
   - **States section with Mermaid `stateDiagram-v2`**: only if the entity has status/state fields. Search source code for where status is set/updated to map transitions.
   - **Known unknowns**: generously flag gaps
3. **Output:** Set `freshness_note: "scuba-depth entity definition + lifecycle from code scan"`.

**Entity completeness check:** After generating all entity PROC- artifacts for a service, compare the list against the schema's entity list. If any core entity was skipped, go back and generate it. Common misses: entities in non-primary sub-apps, entities only referenced via FK but not directly queried, entities with short model files.

**For junction/config tables** (entities that didn't pass the core entity filter): document them in the `## Relationships` section of their parent entity's PROC- artifact. Don't generate a separate artifact.

**Parallelism:** Entity artifacts within the same service can share context (same schema, same source repo). Group by service and launch one agent per service batch.

### 3.4 — Auth boundary artifacts

For each service, scan for authentication and authorization patterns:

1. Search the source code for:
   - JWT validation middleware or decorators
   - Keycloak/Auth0/OAuth2 client configuration
   - RBAC decorators, permission checks, policy engines
   - Service account configuration (client credentials)
   - API key validation
   - Multiple auth paths coexisting (legacy vs new)
2. For each service where auth patterns are found, document:
   - **AuthN mechanism**: what it is and where in code (JWT, Keycloak, service accounts)
   - **AuthZ enforcement**: how it works (RBAC middleware, decorators, policy engine)
   - **Token flow**: how tokens move between frontend and backend (if detectable)
   - **Service-to-service auth**: how backend services authenticate to each other
   - If multiple auth paths coexist, document both with path selection logic
3. **Output:** PROC- artifact per service for auth boundaries. Set `freshness_note: "scuba-depth auth boundary scan"`.

If no auth patterns are found in a service, skip and note in the briefing.

### 3.5 — FE/BE contract identification

Scan frontend source repos (if present in project.json sources):

1. Look for:
   - Generated API clients: `openapi-generator`, `swagger-codegen`, `orval`, `openapi-typescript` in dependency files or generated file headers
   - Shared type definitions: TypeScript interfaces/types that mirror backend schemas
   - Auth flow code: silent SSO setup, token refresh logic, auth interceptors in HTTP clients
   - API base URL configuration: environment variables pointing to backend services
2. **Output:** CON- artifact documenting the FE/BE contract per service pair where both frontend and backend repos exist. If no frontend repos exist in the reef, skip entirely and note in the briefing.

### 3.6 — Error handling patterns per service

For each service's source code:

1. Search for:
   - Global exception handlers or error middleware
   - Retry decorators/wrappers (retry logic, exponential backoff)
   - Timeout configurations (HTTP client timeouts, database connection timeouts, query timeouts)
   - Circuit breaker patterns or libraries
   - Dead letter queues or error queues
2. **Output:** If meaningful patterns are found, write a PROC- or RISK- artifact per service documenting the error handling approach. If patterns are absent (no retry, no circuit breaker, no timeout configuration), that itself is a finding — note as a RISK- artifact or add to an existing service's `known_unknowns`.

### 3.7 — Service contracts (all pairs)

Generate or update a CON- artifact for **every service pair** in the manifest. For N services, there are N×(N-1)/2 pairs — all must be covered. **Do not skip pairs.**

**Naming:** `CON-{SERVICE-A}-{SERVICE-B}` (alphabetical order, e.g., `CON-CDM-CTL`, `CON-CDM-DAIP`).

**Template:** Follow `/Users/jessi/Projects/seaof-ai/reef/references/templates/contract-service-pair.md` exactly. It defines the full structure: Parties, Key Facts, Integration Map (endpoint table per direction), Data Flow, Coupling Assessment table, Failure Behavior, and a "No Integration Detected" fallback section.

For each service pair:

1. Search both services' source code for evidence of interaction (HTTP clients, generated API clients, shared schemas, events, shared DB access).
2. If interaction found: fill the Integration Map, Data Flow, Coupling Assessment, and Failure Behavior sections per the template.
3. If NO interaction found: use the "No Integration Detected" section from the template. This confirms architectural separation.
4. **Output:** CON- artifact per pair. Update existing ones if they exist from snorkel.

**Completeness check:** After all contracts are written, count them. For N services, you must have exactly N×(N-1)/2 CON- artifacts. If any are missing, go back and generate them.

After all pairs, add a summary heat map table to the briefing:

```markdown
| Source | Target | Call Sites | Shared Schemas | Generated Clients | Coupling |
|--------|--------|------------|----------------|-------------------|----------|
```

For single-service reefs, skip this step.

### 3.8 — Cross-service entity comparison

Check GLOSSARY- artifacts for terms flagged as ambiguous or used in multiple services:

1. For each term that appears in SCH- artifacts from different services (e.g., "Order" in Payments and Fulfillment, "Product" in Catalog and Inventory, "User" in Auth and Billing):
   - Pull the field lists from both SCH- artifacts
   - Generate a side-by-side comparison table
   - Flag semantic mismatches: same-name fields with different types, different storage (RDB vs document store), different lifecycle semantics
2. **Output:** CON- artifact per entity comparison documenting:
   - What the term means in each service
   - Field-level comparison table
   - High-risk ambiguities (where conflation could cause bugs or misunderstanding)
   - Canonical writing rules: "Always prefix with service name when referring to {entity}"

For single-service reefs, skip this step.

### 3.9 — Pattern and mechanism deepening

Using the scuba-level signals collected during Step 2 (mining snorkel artifacts), investigate each one:

1. For each named pattern or domain-specific mechanism found in snorkel artifacts' Key Facts or Core Concepts:
   - Read the source code referenced by the artifact to understand the pattern at a conceptual level
   - Document: what the pattern is, which entities/services use it, why it exists, what it enables, how it differs from the standard approach
   - Example: if snorkel found "Soft-delete pattern: entities use is_deleted flag instead of hard delete" — read the model files to understand which entities use it, whether cascading deletes are handled, and why soft-delete was chosen over hard delete
   - Example: if snorkel found "Hash-based deduplication using content_hash and source_hash" — document what's hashed, why multi-level hashing exists, what happens on collision, and how it relates to data integrity
   - Example: if snorkel found "OrderSummaryMV is a materialized view" — document why it exists (read-heavy list endpoints), how it differs from a regular view (pre-computed, needs refresh), and what the staleness implications are

2. **Output:** PROC- or DEC- artifact per pattern/mechanism. Set `freshness_note: "scuba-depth pattern analysis"`. Focus on the "what and why" — leave "trace every line" for `/reef:deep`.

3. **Do not go deep.** If investigating a signal requires tracing more than 2-3 source files to understand, stop and flag it as a deep-level item. Add it to the deep-level signals list for the briefing. The heuristic:
   - Scuba: "What is this pattern and why does it exist?" (conceptual, 1-3 files)
   - Deep: "Show me every line of the implementation." (exhaustive, 5+ files, field-by-field)

---

## Step 4 — Phase 1 Briefing

After all sub-steps, read `.reef/scuba-manifest.json` and present a manifest-based summary:

```
Phase 1 complete.

Manifest: N/M planned artifacts completed, K skipped.

  API-  artifacts:  N/M completed
  SCH-  artifacts:  N/M completed
  PROC- entities:   N/M completed
  CON-  contracts:  N/M completed
  PROC- auth:       N/M completed
  PROC-/DEC-:       N/M completed

Skipped (with reasons):
- {ID}: {reason}

Key findings:
- {Service} has N action-style endpoints (workflow transitions, not plain CRUD)
- {Entity} has a status field with M states but only K transitions traceable in code
- {Service-A} → {Service-B} has the heaviest coupling (N call sites)
- ...

Could not resolve from code alone (Phase 2 candidates):
- What triggers the {state} → {state} transition for {entity}?
- Is the naming overlap between {service-A}.{entity} and {service-B}.{entity} intentional?
- What is the production behavior for {timeout/retry} pattern?
- ...

Flagged for /reef:deep (too detailed for scuba):
- Field-by-field lineage of {entity} (hash computation, transformation chain)
- Exact refresh logic for {materialized view}
- Line-by-line execution path for {critical flow}
- ...
```

Then:

1. **Glossary cross-check** all new artifacts against GLOSSARY- artifacts (same procedure as snorkel Step 6).
2. **Bidirectional linking pass** to ensure all new artifacts are connected in the graph (same procedure as snorkel Step 7).
3. **Add unresolved items** to `.reef/questions.json` with `"phase": "scuba"` and `"status": "unanswered"`.
4. **Run post-write commands** for all artifacts created:
   ```bash
   python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
   python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
   python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Scuba Phase 1: generated N artifacts" --reef <reef-root>
   ```

Then ask:

> "Ready for Phase 2? Here are the exploration-worthy patterns I found. Where would you like to start — or would you rather explore something else?"

Present the unresolved items as a prioritized list. The heaviest dependencies, the most ambiguous entities, and the most incomplete lifecycles should rank highest.

---

## Step 5 — Phase 2: Interactive Q&A

The Socratic half. The user directs where to go. One question at a time.

### 5.1 — Entry point determination

One of four modes based on what the user says:

**a. Phase 1 follow-up** (default) — the user picks from the unresolved questions list:

1. Take the selected question.
2. Read relevant source code to prepare context.
3. Begin the question-by-question flow.

**b. User names a topic** — e.g., "Let's explore the order processing lifecycle":

1. Read relevant source code for that topic.
2. Generate targeted questions that code reading alone cannot answer.
3. Begin the question-by-question flow.

**c. Deepen a draft** — e.g., "Deepen SYS-INGEST":

1. Read the existing artifact file.
2. Review its `known_unknowns` for gaps.
3. Generate questions specifically to fill those gaps.
4. Begin the question-by-question flow.

**d. Generate from template** — user has no specific direction:

1. Adapt the C1-C10 questions from `understanding-template.md` to what the structural scan and Phase 1 reveal about this codebase.
2. Skip questions already answered by existing artifacts.
3. Present the adapted question list and let the user choose where to start.

### 5.2 — Question patterns

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

### 5.3 — Question-by-question flow

For each question or topic:

1. **Present the question.** One at a time. Do not dump a list.
2. **Listen to the user's answer.** Let them talk. Ask follow-ups if something is unclear.
3. **Synthesize what was learned:**
   - Fact — what was established
   - Why it matters — how it connects to the system understanding
   - Source — user statement, code reference, or both
   - Confidence — high/medium/low
   - Open question — anything the answer raised but did not resolve
4. **When enough material accumulates for an artifact,** propose creating or updating one. Explain what artifact type, what ID, and what it would cover.
5. **After each artifact is written,** always ask: "What did I get wrong? What am I missing?"

Proactively suggest questions that code cannot answer:

- Team ownership and responsibility boundaries
- Decision rationale and historical context
- Operational reality vs design intent
- Cross-system boundaries and integration pain points
- When uncertain about code interpretation, suggest documentation sources the user might have

Prioritize unanswered questions from `.reef/questions.json`.

### 5.4 — Artifact creation

When creating or updating an artifact, follow the full artifact contract.

**Frontmatter field order** (all fields required, in this order):

```yaml
id:
type:
title:
domain:
status:
last_verified:
freshness_note:
freshness_triggers:
known_unknowns:
tags:
aliases:
relates_to:
sources:
notes:
```

**Body requirements:**

- Include all required body sections for the artifact type (per the contract).
- Key Facts section with source citations using `→` syntax.
- `## Related` section with wikilinks that match `relates_to` in frontmatter.

**Determinism rules** (for reproducible diffs):

- `relates_to` sorted alphabetically by target.
- `sources` sorted alphabetically by ref.
- `freshness_triggers` sorted alphabetically.

**Validation** — same blocking and warning checks as `/reef:artifact`:

- Blocking: YAML parseable, all required fields present, `id` matches filename, valid enums, non-empty `freshness_note`, Key Facts present (except Glossary).
- Warning: `relates_to` targets resolve, `sources` resolve, required body sections present, wikilinks match frontmatter.

**Glossary cross-check:** Before writing, compare domain terms against GLOSSARY- artifacts. Fix drift or ambiguity.

Status can be "draft" (Phase 1 or uncertain) or "active" (user-confirmed in Phase 2).

### 5.5 — Post-write commands

Run these in order after each artifact file is written and accepted:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in the log message when updating an existing artifact.

---

## Step 6 — Session management

- Track which questions have been covered in this session.
- At natural pauses, summarize progress: artifacts created or updated, questions answered, remaining gaps.
- The user can end the session at any time. Do not push to continue.
- When the user ends the session, update `.reef/questions.json` to reflect what was answered.

---

## Key Rules

- Never invent facts. If uncertain, add to `known_unknowns`.
- Honest gaps beat confident lies.
- The user is the domain expert. Claude reads code; the user knows context.
- **Phase 1 must complete fully before asking the user any questions.**
- **Phase 1 artifacts are all `status: draft`** unless analysis is highly confident.
- **Phase 2 can promote artifacts to `status: active`** based on user confirmation.
- Do not ask all questions at once — work through them one at a time.
- Prioritize unanswered questions from the question bank.
- After every artifact written in Phase 2, ask what was gotten wrong and what is missing.
- Each answered Phase 2 question can produce PROC-, DEC-, RISK-, CON-, or GLOSSARY- artifacts.

---

## If Called Without Snorkel

If no snorkel artifacts exist (empty `artifacts/` directory), Phase 1 will have very little to work with. Warn the user and suggest running `/reef:snorkel` first. Scuba builds on snorkel's foundation — it deepens, not creates from scratch.

If snorkel artifacts exist but `sources/apis/` and `sources/schemas/` are empty, Phase 1 sub-steps 3.1 and 3.2 will produce thin results. Suggest running `/reef:source` for better output. Other sub-steps (lifecycle, auth, error handling, dependencies) can still run from source code directly.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No sources**: "No sources configured. Run `/reef:init` to add source paths."
- **Source path missing**: warn, skip, continue with others.
- **reef.py fails**: report the error. Do not silently swallow.
- **Phase 1 sub-step fails**: report the error, continue with remaining sub-steps. Include the failure in the briefing.
