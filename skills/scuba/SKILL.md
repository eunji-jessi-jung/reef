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

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`
- `${CLAUDE_PLUGIN_ROOT}/references/understanding-template.md` — focus on Scuba (C1-C10) questions

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

### RISK- per service

One per service that does not already have a RISK- artifact with 5+ findings. Even if snorkel created a thin RISK-, scuba deepens it with broader code scanning.

### DEC- observable decisions

One per observable technology/architecture choice that lacks a DEC- artifact. Scan for: database choice rationale, auth provider selection, API framework choice, monorepo structure decisions, sync vs async patterns, soft vs hard delete, versioning strategy, dual-database architectures.

### GLOSSARY- per service

One per service that lacks a per-service GLOSSARY-{SERVICE} artifact. Per-service glossaries are authoritative within their scope and complement the unified glossary.

### PROC- flow catalogs

For services with pipeline/orchestration/job systems (detected by: Prefect flows, Celery tasks, Airflow DAGs, background job classes, sequential status progressions). One per service or subsystem with distinct flow sets.

### PROC- multi-app comparison pairs

For services where the same domain concept is implemented differently across sub-apps (e.g., parallel directory structures, similar-but-not-identical models, domain-branching logic). One per {concept} x {app-pair}.

### SCH- per-collection (document stores)

For MongoDB/document-store services with 3+ collections. One SCH- per collection, documenting fields, indexes, embedded vs referenced docs, and nesting structure. This complements the unified SCH- with per-collection depth.

### SCH- field lineage

For core entities with complex data origins (ingestion pipelines, ETL, computed fields). One per entity group, documenting where each non-trivial field comes from (API input, external system, computed, copied from another entity, system-generated).

### Summary

Print the full manifest with counts:

```
Artifact generation manifest:
  API-  artifacts:       N planned (M new, K updates)
  SCH-  artifacts:       N planned (M new, K updates)
  SCH-  per-collection:  N planned
  SCH-  field lineage:   N planned
  PROC- entities:        N planned (from X core entities across Y schemas)
  PROC- auth:            N planned
  PROC- flow catalogs:   N planned
  PROC- comparisons:     N planned
  PROC-/DEC- patterns:   N planned (from pattern signals)
  CON-  contracts:       N planned (M new, K updates)
  RISK- per service:     N planned
  DEC-  observable:      N planned
  GLOSSARY- per service: N planned
  ──────────────
  Total:                 N artifacts
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

No user input after confirmation. Work through the manifest systematically — every planned artifact must be addressed (completed or explicitly skipped with reason). Report progress as you go: "Writing API-PAYMENTS-GATEWAY (1/9 API artifacts)..."

All Phase 1 artifacts are `status: "draft"`. Phase 2 can promote to `"active"` with user confirmation.

**Parallelism — CRITICAL for time efficiency.** The 16 sub-steps are NOT all sequential. Execute in 5 parallel batches:

| Batch | Sub-steps | What | Parallelism |
|-------|-----------|------|-------------|
| 1. Spec Layer | 3.1, 3.2 | API patterns + Schema docs | One agent per service |
| 2. Entity Deep-Dive | 3.3, 3.15, 3.16 | Entity lifecycles + per-collection SCH- + field lineage | One agent per service |
| 3. Service Signals | 3.4, 3.6, 3.10, 3.13 | Auth + error handling + risks + flow catalogs | One agent per service |
| 4. Cross-Service | 3.5, 3.7, 3.8, 3.14 | FE/BE contracts + service pairs + entity comparisons + multi-app comparisons | One agent per pair |
| 5. Synthesis | 3.9, 3.11, 3.12 | Patterns + DEC- + GLOSSARY- per service | One agent per category |

Within each batch, launch one Agent per service (or per pair for Batch 4). Batches 1-3 can run concurrently since they read different aspects of the same code. Batch 4 depends on Batch 1-2 results (needs SCH- and GLOSSARY- artifacts). Batch 5 depends on all prior batches.

**Minimum execution:** 3 sequential rounds (Batches 1-3 together, then 4, then 5), each internally parallel.

**Read `references/scuba-phase1-substeps.md`** for full details on each sub-step. Summary of each:

### 3.1 — API pattern analysis
Analyze OpenAPI specs → write API- artifacts as "delta layer on top of OpenAPI" with surface profile, auth posture, non-CRUD actions, pagination, and contract limits. **Must include `### Worked Example`** with realistic JSON request/response.

### 3.2 — Comprehensive schema documentation
Read extracted ERDs → write SCH- artifacts with field tables, entity descriptions, relationships. **Must include Mermaid `erDiagram`** (RDB) or `classDiagram` (document store). Max 15 entities per diagram.

### 3.3 — Entity definition and lifecycle artifacts
PROC- artifact for every core entity in manifest. **Naming:** `PROC-{SERVICE}-{ENTITY}-LIFECYCLE`. Template: `references/templates/process-entity-lifecycle.md`. **Must include Mermaid `stateDiagram-v2`** if status field exists, plus `## Agent Guidance` section. **Completeness check** against schema entity list after each service.
   - **Relationships**: reference other PROC-{SERVICE}-{ENTITY}-LIFECYCLE artifacts
### 3.4 — Auth boundary artifacts
Scan for JWT, OAuth, RBAC, API keys, service accounts → write PROC- per service's auth pattern.

### 3.5 — FE/BE contract identification
Scan frontend repos for generated API clients, shared types, auth flow → write CON- per FE/BE pair. Skip if no frontend repos.

### 3.6 — Error handling patterns per service
Scan for exception handlers, retry logic, timeouts, circuit breakers, dead-letter queues → write PROC- or RISK- per service.

### 3.7 — Service contracts (all pairs)
CON- artifact for **every** service pair (N×(N-1)/2). Template: `references/templates/contract-service-pair.md`. **Must include Mermaid `sequenceDiagram`** and `## Impact Analysis` for detected integrations. Use "No Integration Detected" section for pairs with no interaction. **Completeness check:** count must equal N×(N-1)/2.

### 3.8 — Cross-service entity comparison
For terms appearing in SCH- from different services → CON- with side-by-side field comparison, semantic mismatches, canonical writing rules. Skip for single-service reefs.

### 3.9 — Pattern and mechanism deepening
Investigate named patterns from snorkel artifacts → PROC- or DEC- per pattern. Scuba depth = "what and why" (1-3 files). Flag anything requiring 5+ files for `/reef:deep`.

### 3.10 — Per-service RISK- artifacts
Scan for TODO/FIXME/HACK, bare exceptions, hardcoded credentials, missing error handling, skipped tests → RISK- per service. Template: `references/templates/risk-service.md`. Severity by density (10+=high, 5-9=medium, 1-4=low).

### 3.11 — DEC- from observable patterns
ADR format for each planned DEC-: Context (code evidence), Decision (specific), Consequences (observable), Rationale (if determinable, else `known_unknowns`).

### 3.12 — Per-service GLOSSARY- artifacts
Extract domain terms from all artifacts for each service → GLOSSARY-{SERVICE}. Template: `references/templates/glossary-service.md`. Do NOT guess acronym expansions. Cross-reference with unified GLOSSARY-. Generate GLOSSARY-SOURCE-INDEX when all per-service glossaries are done.

### 3.13 — PROC- flow catalogs
Enumerate Prefect flows, Celery tasks, Airflow DAGs, background jobs → PROC-{SERVICE}-FLOW-CATALOG. Template: `references/templates/process-flow-catalog.md`. Include Mermaid `graph` of flow dependencies. Skip if no pipelines.

### 3.14 — PROC- multi-app comparison pairs
Detect mirrored implementations across sub-apps → document shared vs different with side-by-side tables. Skip for single-app services.

### 3.15 — SCH- per-collection (document stores)
One SCH- per MongoDB collection (3+ collections): fields, embedded vs referenced, indexes, Mermaid nesting diagram.

### 3.16 — SCH- field lineage
Trace non-trivial field origins (API input, external system, computed, copied, system-generated) → lineage table + Mermaid `flowchart`. Skip for simple CRUD entities.

---

## Step 4 — Phase 1 Briefing

After all sub-steps, read `.reef/scuba-manifest.json` and present a manifest-based summary covering:

1. **Manifest completion** — N/M completed, K skipped (per category: API-, SCH-, PROC-, CON-, RISK-, DEC-, GLOSSARY-)
2. **Skipped artifacts** with reasons
3. **Key findings** — notable patterns, heaviest couplings, complex lifecycles
4. **Phase 2 candidates** — questions code alone cannot answer (state transitions, naming overlaps, production behavior)
5. **Deep-dive flags** — items too detailed for scuba (field-by-field lineage, line-by-line execution paths)

Then:

1. **Glossary cross-check** all new artifacts against GLOSSARY- artifacts (same procedure as snorkel Step 6).
2. **Bidirectional linking pass** to ensure all new artifacts are connected in the graph (same procedure as snorkel Step 7).
3. **Add unresolved items** to `.reef/questions.json` with `"phase": "scuba"` and `"status": "unanswered"`.
4. **Run post-write commands** for all artifacts created:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Scuba Phase 1: generated N artifacts" --reef <reef-root>
   ```
5. **Render health report** using the same Unicode box-drawing format as snorkel Step 7. This gives the user an immediate visual sense of how much richer the reef got from Phase 1.

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

**Read `references/artifact-contract.md`** for frontmatter field order, body requirements, determinism rules, and validation checks. All rules apply.

**Glossary cross-check:** Before writing, compare domain terms against GLOSSARY- artifacts. Fix drift or ambiguity.

Status can be "draft" (Phase 1 or uncertain) or "active" (user-confirmed in Phase 2).

### 5.5 — Post-write commands

Run these in order after each artifact file is written and accepted:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in the log message when updating an existing artifact.

---

## Step 6 — Session management

- Track which questions have been covered in this session.
- At natural pauses, summarize progress: artifacts created or updated, questions answered, remaining gaps.
- The user can end the session at any time. Do not push to continue.
- When the user ends the session:
  1. Update `.reef/questions.json` to reflect what was answered.
  2. Run rebuild-index, rebuild-map, and lint.
  3. **Render health report** — same Unicode box-drawing format as the Phase 1 briefing. Show the final artifact counts, coverage, and freshness so the user sees the full picture of what scuba produced.

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
