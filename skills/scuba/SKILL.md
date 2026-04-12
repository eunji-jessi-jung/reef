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
  - A named pattern (e.g., "outbox pattern", "saga orchestration", "event sourcing") → candidate for a PROC- or DEC- artifact documenting the mechanism
  - A domain-specific mechanism (e.g., "hash-based deduplication", "materialized views", "optimistic locking with version counters") → candidate for a PROC- or DEC- artifact
  - A cross-service coupling signal (e.g., "shared API client must be passed to service initializers") → candidate for deeper CON- artifact
  - A gap or uncertainty in known_unknowns that code reading could partially resolve
  - **A cross-system divergence signal** — the same concept (e.g., "case", "dataset", "project") appearing in multiple services with different definitions, different lifecycles, or different modeling approaches → flag as **PAT- candidate** for Phase 2

  **Categorize each signal by depth level:**
  - **Scuba Phase 1**: understand the mechanism — what it is, which entities/services use it, how it works. Produces PROC-, DEC-, or CON- artifacts through code reading.
  - **Scuba Phase 2 (PAT- candidates)**: patterns require understanding *why* a design choice was made, not just *that* it exists. A PAT- artifact documents a reusable architectural convention — the design intent, the trade-offs, the decision rule for when to use it vs alternatives. These emerge from noticing the same problem solved differently across boundaries, or the same convention applied consistently for a reason code alone doesn't explain. **Flag PAT- candidates during Phase 1 but create them in Phase 2**, where the user can confirm the design intent.
  - **Deep**: trace the implementation exhaustively — field-by-field lineage, exact code paths, every edge case. Produces dense, line-cited artifacts. Flag these for `/reef:deep` rather than investigating in scuba.

  Collect Phase 1 signals into a list for sub-step 3.9. Collect PAT- candidates and deep-level signals into separate lists for the Phase 1 briefing.

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

**Step 1: Generate the baseline manifest programmatically.**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py manifest --reef <reef-root>
```

This command reads `project.json`, `sources/apis/`, and `sources/schemas/` to generate a manifest with:
- API- artifacts (one per extracted OpenAPI spec)
- SCH- artifacts (one per extracted schema + per-collection for document stores)
- PROC-entity lifecycles (one per core entity extracted from schemas)
- CON- service pairs (combinatorial: N×(N-1)/2)
- RISK- per service
- DEC- placeholders per service
- GLOSSARY- per service + source index
- PROC- flow catalogs (for pipeline/orchestration services)

The manifest is saved to `.reef/scuba-manifest.json`. Read it and report the counts.

**Step 2: Augment the manifest using the mandatory checklist.**

The programmatic manifest covers what can be detected from file structure and schema headings. You MUST walk through this checklist and add items it misses. This is not optional — skipping this checklist is the primary cause of coverage gaps.

**Checklist A — SYS- updates (MANDATORY for every service):**
- [ ] For each existing SYS- artifact, plan an **update** entry. SYS- artifacts created by snorkel are thin — scuba must add: dependency table (what external systems this service depends on), "Does NOT Own" section (explicit ownership boundaries), behavior highlights (domain-specific mechanisms like versioning, dedup, caching), and runtime component inventory with tech stacks. Without this step, system artifacts stay at snorkel depth (typically 2/5 quality).

**Checklist B — SCH- field lineage (check every service):**
- [ ] For each service with ingestion, ETL, transform, or computed field logic → plan one SCH- field lineage artifact per entity group. Read ingestion/transform code directories to identify candidates. Common signals: `*_hash` fields, `*_data` snapshot tables, fields copied from external APIs, fields derived from other fields. If a service has no transform logic, skip with a note.

**Checklist C — Individual flow PROC- artifacts (check pipeline services):**
- [ ] Read any existing PROC- flow catalog. For **every flow listed in the catalog**, check if an individual PROC- artifact exists. If not, plan one. This is the most commonly missed gap — catalogs list 20+ flows but only 5-10 get individual artifacts.
- [ ] Specifically check for: analytics/reporting flows, validation flows, cleanup/maintenance flows — these are the flows most often skipped because they seem "less important" than ingestion/inference.

**Checklist D — Operational/boundary PROC- artifacts (check every service):**
- [ ] For each service, check if these operational artifacts exist. Plan any that are missing:
  - PROC-{SERVICE}-AUDIT or PROC-{SERVICE}-TRACEABILITY — if the service has audit logging, traceability, or compliance patterns
  - PROC-{SERVICE}-OPERATIONS — if the service has deployment config, feature flags, runtime controls, health checks
  - PROC-{SERVICE}-DATA-SERVING — if the service serves data to other systems or frontends (data fetch patterns, caching, pagination boundaries)
  - PROC-{SERVICE}-DATABASE-STRATEGY — if the service uses multiple databases, modal isolation, or non-obvious persistence patterns

**Checklist E — Partial questions (check questions.json):**
- [ ] Read `.reef/questions.json`. For every question with `status: "partial"`, identify which artifact would answer it more fully. If no artifact is planned for that topic, add one to the manifest.

**Checklist F — Cross-system artifacts:**
- **PAT- candidates** from snorkel signal mining (Step 2). These are NOT planned for Phase 1. Instead, list them as Phase 2 candidates. A PAT- artifact is warranted when you notice: the same concept modeled differently across systems, a recurring design convention whose rationale isn't obvious from code alone, or an architectural boundary pattern that governs how things are built.
- **PROC- multi-app comparison pairs** — for services where the same domain concept is implemented differently across sub-apps. One per {concept} × {app-pair}.
- **CON- entity comparisons** — for terms appearing in SCH- from different services with potentially different meanings.

**Checklist G — Domain labeling for cross-system artifacts:**
- [ ] Any CON- artifact between services, GLOSSARY-UNIFIED, entity comparison artifacts, and ecosystem-level RISK- artifacts must use the project-level domain slug from `project.json` (e.g., `domain: "myproject"`), NOT a single service's domain. This ensures cross-system artifacts are discoverable and don't create false "0% coverage" gaps for the shared/cross-system domain.

Add all discovered items to the manifest's `planned` array and re-save. Report the checklist results:

```
Manifest augmentation checklist:
  A. SYS- updates:           N planned (one per service)
  B. SCH- field lineage:     N planned (from N services with transform logic)
  C. Individual flow PROC-:  N planned (from flow catalog gaps)
  D. Operational PROC-:      N planned (audit, operations, data-serving, db-strategy)
  E. Partial question PROC-: N planned (from N partial questions)
  F. Cross-system:           N planned (comparisons, entity comparisons)
  G. Domain relabeling:      N artifacts to fix
```

**Step 3: Pre-execution coverage gap detection.**

Before pruning, run the gap detection logic that would otherwise only run in the Phase 1 briefing (Step 4). This catches structural gaps while they can still be added to the manifest:

1. **Entity-to-PROC ratio:** For each service, count entities in SCH- artifacts vs planned PROC- entity lifecycles. If a service has 15 entities but only 5 planned PROC-, add the missing ones.
2. **Flow catalog coverage:** For each PROC- flow catalog, compare listed flows against planned individual PROC- artifacts. Add any uncovered flows.
3. **Service pair coverage:** Count planned CON- artifacts vs N×(N-1)/2 required pairs. Add any missing pairs.
4. **Question coverage:** For each unanswered or partial question, check if a planned artifact addresses it. Flag uncovered questions.

Add any gaps found to the `planned` array.

**Step 4: Review and prune.**

Scan the manifest for entries that are clearly not worth a full artifact:
- Reference/lookup entities with only 2-3 trivial fields (move to `skipped` with reason)
- Duplicate coverage (entity already well-covered by an existing artifact)

Do NOT prune aggressively — a thin artifact is better than a missing one. Only skip entries that are genuinely trivial.

### Summary

Print the full manifest with counts:

```
Artifact generation manifest:
  SYS-  updates:           N planned (deepening existing snorkel artifacts)
  API-  artifacts:         N planned (M new, K updates)
  SCH-  artifacts:         N planned (M new, K updates)
  SCH-  per-collection:    N planned
  SCH-  field lineage:     N planned (from checklist B)
  PROC- entities:          N planned (from X core entities across Y schemas)
  PROC- auth:              N planned
  PROC- flow catalogs:     N planned
  PROC- individual flows:  N planned (from checklist C — flow catalog gaps)
  PROC- operational:       N planned (from checklist D — audit, ops, data-serving)
  PROC- comparisons:       N planned
  CON-  contracts:         N planned (M new, K updates)
  RISK- per service:       N planned
  DEC-  observable:        N planned
  GLOSSARY- per service:   N planned
  ──────────────
  Phase 1 total:           N artifacts

  Phase 2 candidates (require human input):
  PAT-  patterns:          N candidates (from cross-system divergence signals)
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

**VALIDATION: Before proceeding to Phase 1, verify that the `planned` array is NOT empty.** If it is, you have not completed this step — go back and enumerate artifacts from each category above. The manifest must contain every artifact that Phase 1 will produce, enumerated BEFORE execution begins. Do not build the manifest retrospectively after writing artifacts.

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

### Manifest completion tracking (CRITICAL)

After each artifact is written, you MUST update `.reef/scuba-manifest.json`:
1. Move the item from `planned` to `completed` with a timestamp.
2. If an artifact is skipped, move it to `skipped` with a `reason` field.
3. After each batch completes, verify that `completed.length + skipped.length + planned.length` equals the original total. If not, investigate — items are being lost.

This is not optional. The manifest is the single source of truth for what scuba produced. If it shows `completed: []` after a full run, the tracking failed and the next run cannot resume correctly.

### Minimum depth validation per artifact

After writing each artifact, validate it against the minimum depth bar for its type. If an artifact fails validation, read more source code and deepen it before marking it complete.

| Type | Minimum Key Facts | Required Sections | Required Visuals |
|------|-------------------|-------------------|------------------|
| SYS- | 6 | Overview, Key Facts, Responsibilities, "Does NOT Own", Core Concepts, Dependencies table, Related | — |
| API- | 6 | Overview, Key Facts, Source of Truth, Resource Map, Worked Example, Related | — |
| SCH- | 5 | Overview, Key Facts, Entities (with field tables), Related | Mermaid `erDiagram` (mandatory) |
| PROC- (entity lifecycle) | 8 | Purpose, Key Facts, States/Transitions table, Agent Guidance, Related | Mermaid `stateDiagram-v2` if status field exists |
| PROC- (flow/pipeline) | 6 | Purpose, Key Facts, Input/Output, Steps/Phases, Error Handling, Related | Mermaid `flowchart` or `sequenceDiagram` |
| PROC- (operational) | 5 | Purpose, Key Facts, Scope, Current State, Related | — |
| CON- | 6 | Parties, Key Facts, Agreement, Current State, Impact Analysis, Related | Mermaid `sequenceDiagram` |
| DEC- | 5 | Context, Decision, Key Facts, Rationale, Consequences, Related | — |
| RISK- | 4 | Description, Key Facts, Findings table, Recommended Actions, Related | — |
| GLOSSARY- | N/A | Overview, Terms table, Related | — |

An artifact that does not meet its minimum Key Facts count is **not complete**. Read additional source files to find more verifiable claims before marking it done.

**Parallelism — CRITICAL for time efficiency.** The 16 sub-steps are NOT all sequential. Execute in 5 parallel batches:

| Batch | Sub-steps | What | Parallelism |
|-------|-----------|------|-------------|
| 0. Foundation | 3.0 | SYS- artifact updates | One agent per service |
| 1. Spec Layer | 3.1, 3.2 | API patterns + Schema docs | One agent per service |
| 2. Entity Deep-Dive | 3.3, 3.15, 3.16 | Entity lifecycles + per-collection SCH- + field lineage | One agent per service |
| 3. Service Signals | 3.4, 3.6, 3.10, 3.13 | Auth + error handling + risks + flow catalogs | One agent per service |
| 4. Cross-Service | 3.5, 3.7, 3.8, 3.14 | FE/BE contracts + service pairs + entity comparisons + multi-app comparisons | One agent per pair |
| 5. Synthesis | 3.9, 3.11, 3.12 | Patterns + DEC- + GLOSSARY- per service | One agent per category |

Batch 0 runs first — SYS- updates must complete before other artifacts reference them. Within each subsequent batch, launch one Agent per service (or per pair for Batch 4). Batches 1-3 can run concurrently since they read different aspects of the same code. Batch 4 depends on Batch 1-2 results (needs SCH- and GLOSSARY- artifacts). Batch 5 depends on all prior batches.

**Minimum execution:** 4 sequential rounds (Batch 0, then Batches 1-3 together, then 4, then 5), each internally parallel.

**Read `references/scuba-phase1-substeps.md`** for full details on each sub-step. Summary of each:

### 3.0 — SYS- artifact update (MANDATORY — runs before all other sub-steps)

Snorkel creates SYS- artifacts as thin overviews. Scuba MUST deepen them. For each existing SYS- artifact:

1. Re-read the full source code entry points, config, and dependency files for the service.
2. **Add or update these sections:**
   - `## Dependencies` — table with columns: System | Integration Type | Purpose | Auth Method. List every external system this service depends on (databases, caches, message queues, identity providers, other services).
   - `## Does NOT Own` — explicit list of what this service does NOT own. This prevents scope creep and clarifies boundaries. Example: "Payments does NOT own user profiles — that is the Identity service's responsibility."
   - `## Domain Behavior Highlights` — 3-5 bullet points on domain-specific mechanisms (versioning strategies, dedup patterns, caching semantics, async operation models). These are the things a new engineer would need to know beyond "what endpoints exist."
   - `## Runtime Components` — table with columns: Component | Tech Stack | Purpose | Entry Point. List every deployable unit (backend apps, frontend apps, workers, cron jobs).
3. **Update Key Facts** to meet the minimum bar (>= 6). Add facts about component count, shared libraries, tech stack choices, deployment model.
4. **Update `relates_to`** to link to all child artifacts (SCH-, API-, PROC-, CON-, RISK-) that exist or are planned. SYS- artifacts with `relates_to: []` are broken — they should be the root of the artifact graph for their service.

This sub-step runs first because all other sub-steps produce artifacts that should link back to the updated SYS- entry point. Run one agent per service, all in parallel.

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

### 4.0 — Manifest reconciliation (MANDATORY before briefing)

Before presenting results, verify the manifest is accurate:

1. Read `.reef/scuba-manifest.json`. Count `planned`, `completed`, and `skipped` entries.
2. Scan `artifacts/` directory for all actual artifact files. Count them.
3. **If `completed` is empty but artifacts exist:** The manifest was not updated during Phase 1. This is a tracking failure. Fix it now:
   - For each artifact file in `artifacts/`, check if it matches a `planned` entry by ID.
   - If it matches, move it to `completed` with `timestamp: "reconciled"`.
   - If it doesn't match any planned entry (artifact was created beyond the manifest), add it to `completed` with `source: "unplanned"`.
   - Re-save the manifest.
4. **Report the reconciliation:** "Manifest reconciled: N planned items matched to artifacts, M unplanned artifacts discovered, K items still pending."

This step ensures the manifest is a truthful record of what was produced, enabling accurate resume on the next run.

### 4.1 — Summary

Present a manifest-based summary covering:

1. **Manifest completion** — N/M completed, K skipped (per category: API-, SCH-, PROC-, CON-, RISK-, DEC-, GLOSSARY-, PAT-)
2. **Skipped artifacts** with reasons
3. **Key findings** — notable patterns, heaviest couplings, complex lifecycles

### Coverage gap detection (post-Phase-1 validation)

Re-run the same 4 gap checks from Step 2.5 Step 3 (entity-to-PROC ratio, flow catalog coverage, service pair coverage, question coverage), but this time against **actual artifacts produced**, not just planned items.

Additionally, scan for **repetition gaps** — PAT- candidates where the same concept appears across services with different implementations:
- GLOSSARY- terms appearing in 2+ service glossaries with different definitions
- SCH- entities with similar names across services but different field structures
- PROC- lifecycle patterns applied differently across services

Present all gaps as a numbered list with **pre-formulated prompts** the user can pick from. Each gap gets a concrete next action.

**Presentation rules:**
- **Never use artifact type prefixes** in user-facing text. Frame gaps as questions or observations. Say "none have their own documentation" not "0 per-flow PROC- artifacts."
- **Every gap comes with a concrete next action.** The user picks a number, not formulates a prompt.

4. **Deep-dive flags** — items too detailed for scuba (field-by-field lineage, line-by-line execution paths)

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
5. **Auto-fix lint errors.** Phase 1 agents can produce lint errors at scale (ID casing, missing fields, dangling wikilinks, frontmatter issues). These MUST be fixed before the briefing — 4 errors per artifact is not acceptable quality, and presenting unfixed errors undermines trust.

   Run `reef.py lint` and parse the JSON output. For each error category:
   - **ID/filename mismatch:** rename file or fix frontmatter `id` field
   - **Missing required fields:** add the field with a sensible default or `"TBD"`
   - **Dangling `relates_to` targets:** remove the entry or create the missing artifact stub
   - **Wikilink/frontmatter sync:** update `## Related` section to match `relates_to` or vice versa
   - **ID casing convention:** fix to match `{TYPE}-{SERVICE}-{NAME}` uppercase convention
   - **Missing Key Facts source links:** add `→ source TBD` placeholder

   **Batch fix with agents:** Group errors by artifact file. Launch one agent per file (all in a single message) to read the artifact, fix all its lint errors, and re-write. After all agents complete, re-run `reef.py lint` to verify zero errors remain. If errors persist, fix manually (no more than 2 fix rounds).

   **Target: zero lint errors before the briefing.**

6. **Render health report** using the same Unicode box-drawing format as snorkel Step 7. This gives the user an immediate visual sense of how much richer the reef got from Phase 1.

Then ask:

> "Ready for Phase 2? Here's what I found that could use your input — or explore something else entirely."

Present the coverage gaps and cross-system patterns from the gap detection above as a single numbered list. No artifact type prefixes in user-facing text. The user picks a number or names their own topic.

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

Read `${CLAUDE_PLUGIN_ROOT}/references/scuba-question-patterns.md` for the full set of Socratic question templates (C1-C10). Present one at a time — not as a dumped list.

### 5.3 — Question-by-question flow

**CRITICAL: The user answers first.** Phase 2 is Socratic — "AI found the answers. I asked the questions." The user is the domain expert. Always ask, listen, THEN investigate. Never launch an investigation before the user has had a chance to answer.

For each question or topic:

1. **Present the question.** One at a time. Do not dump a list. **Show progress:** "Question 3 / 8" (or "Topic 3 / 8" if user-directed). Count is based on the selected question set from Step 5.2. If the user adds topics mid-session, update the denominator.
2. **Wait for the user's answer.** Let them talk. Ask follow-ups if something is unclear. Three possible outcomes:
   - **User answers** → go to step 3 (verify).
   - **User says "I don't know" / "not sure"** → offer to investigate: "I can go trace this in the code if you'd like — want me to investigate?" If yes, go to step 3a. If no, skip to the next question.
   - **User says "skip"** → move to the next question.
3. **Verify against code.** After the user answers, go read the relevant source code to find evidence that supports or contradicts what the user said. Report findings briefly: "The code confirms X — found at `src/service.py:L42`. However, I also found Y which might be worth noting." Then record verified findings in existing artifacts or create a new one if warranted.
   - **3a. Self-directed investigation** (when user didn't know): Read the relevant source code, trace the behavior, and report back with findings. Keep investigations focused — read the most relevant 3-5 files, not the entire codebase. Present what you found and ask the user to confirm or correct your interpretation.
4. **Abort mechanism.** If an investigation is taking more than ~30 seconds of tool calls (5+ file reads with no clear answer emerging), stop and report what you found so far: "I have not found a clear answer yet. Here is what I see so far: [summary]. Want me to keep digging, or move on?" Do not let a single investigation block the entire Phase 2 flow.
5. **Synthesize what was learned:**
   - Fact — what was established (from user + code evidence)
   - Why it matters — how it connects to the system understanding
   - Source — user statement, code reference, or both
   - Confidence — high/medium/low
   - Open question — anything the answer raised but did not resolve
6. **When enough material accumulates for an artifact,** propose creating or updating one. Explain what artifact type, what ID, and what it would cover.
7. **After each artifact is written,** move to the next question. The user will speak up if something is wrong.

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

**Domain labeling rule:** Cross-system artifacts must use the project-level domain slug from `project.json`, not a single service's domain. This applies to:
- CON- artifacts between services (e.g., CON-PAYMENTS-IDENTITY → project-level domain)
- GLOSSARY-UNIFIED or GLOSSARY-SHARED → project-level domain
- CON- entity comparison artifacts → project-level domain
- RISK- artifacts about ecosystem-level concerns → project-level domain
- PAT- artifacts about cross-system patterns → project-level domain

This ensures cross-system artifacts are discoverable and don't create false coverage gaps for the shared domain.

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
  4. Remind the user: "Artifacts are wikilinked — open the reef directory as an Obsidian vault to explore the knowledge graph."
  5. If unanswered questions remain that look like they could be answered by existing docs (architecture specs, PRDs, design docs), mention: "Have docs that might fill these gaps? Drop them in `sources/raw/` and the next scuba pass will use them."
  6. **What's Next — show the user what the reef is *for* now:**
     - **Agent context:** Point dev agents (Claude Code, Cursor, Copilot) at the reef directory as context. Artifacts give agents accurate domain knowledge instead of re-deriving from code every time.
     - **Onboarding:** New teammates open the reef in Obsidian and explore the knowledge graph. Faster ramp-up than reading code or asking questions.
     - **Documentation:** Artifacts are already structured docs. Export to Confluence, Notion, or a static site if the team needs a shared reference outside Obsidian.
     - **Audit and review:** Before architecture reviews, compliance audits, or incident postmortems — `/reef:health` shows coverage gaps; artifacts surface risks and decisions.
     - **Living reference:** Run `/reef:update` after code changes to keep artifacts fresh. The reef compounds — each update costs less than the first build.

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
- After writing an artifact in Phase 2, move to the next question. The user will correct if needed.
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
