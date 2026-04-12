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

**Step 2: Augment the manifest with Claude-discovered items.**

The programmatic manifest covers what can be detected from file structure and schema headings. Review it and add items it cannot detect:

- **PAT- candidates** from snorkel signal mining (Step 2). These are NOT planned for Phase 1. Instead, list them as Phase 2 candidates. A PAT- artifact is warranted when you notice: the same concept modeled differently across systems, a recurring design convention whose rationale isn't obvious from code alone, or an architectural boundary pattern that governs how things are built. Examples: FK vs link table choice, cross-system entity comparison (same word, different meaning), orchestration vs individual execution model, control plane vs data plane separation.
- **PROC- multi-app comparison pairs** — for services where the same domain concept is implemented differently across sub-apps (parallel directory structures, similar-but-not-identical models). One per {concept} × {app-pair}. These require reading source code to detect mirrored structures.
- **SCH- field lineage** — for core entities with complex data origins (ingestion pipelines, ETL, computed fields). One per entity group. Requires reading ingestion/transform code to identify.
- **CON- entity comparisons** — for terms appearing in SCH- from different services with potentially different meanings.

Add these to the manifest's `planned` array and re-save.

**Step 3: Review and prune.**

Scan the manifest for entries that are clearly not worth a full artifact:
- Reference/lookup entities with only 2-3 trivial fields (move to `skipped` with reason)
- Duplicate coverage (entity already well-covered by an existing artifact)

Do NOT prune aggressively — a thin artifact is better than a missing one. Only skip entries that are genuinely trivial.

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
  CON-  contracts:       N planned (M new, K updates)
  RISK- per service:     N planned
  DEC-  observable:      N planned
  GLOSSARY- per service: N planned
  ──────────────
  Phase 1 total:         N artifacts

  Phase 2 candidates (require human input):
  PAT-  patterns:        N candidates (from cross-system divergence signals)
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

1. **Manifest completion** — N/M completed, K skipped (per category: API-, SCH-, PROC-, CON-, RISK-, DEC-, GLOSSARY-, PAT-)
2. **Skipped artifacts** with reasons
3. **Key findings** — notable patterns, heaviest couplings, complex lifecycles

### Coverage gap detection (domain-agnostic)

Scan the reef's current artifacts for structural gaps. These are detectable from the reef itself — no external baseline needed:

**Repetition gaps** — the same concept appearing across services with different implementations:
- Scan GLOSSARY- artifacts for terms flagged with disambiguation notes or appearing in 2+ service glossaries with different definitions → each is a **PAT- candidate** (cross-system entity comparison)
- Scan SCH- artifacts for entities with similar names across services but different field structures → PAT- candidate
- Scan PROC- artifacts for the same lifecycle pattern applied differently (e.g., "auth" exists for every service — do they follow the same pattern or diverge?) → PAT- candidate if they diverge in an interesting way

**Depth gaps** — services or areas with thin coverage relative to their complexity:
- For each service: count PROC- artifacts vs number of entities in that service's SCH-. If a service has 15+ entities but only 3 PROC-, its entity lifecycles are under-documented.
- For pipeline/orchestration services: count individual flow PROC- artifacts vs flows listed in any flow catalog. If a flow catalog lists 20 flows but only 1 PROC- exists, per-flow documentation is a gap.
- For multi-app services (multiple sub-applications under one repo): check if comparison artifacts exist. If a service has 3+ apps with parallel structures but no comparison PROC- or PAT-, that's a gap.

**Boundary gaps** — cross-system areas without contracts:
- Count service pairs (N services → N*(N-1)/2 pairs). Compare against CON- artifact count. Flag uncovered pairs that have known integration points (visible from API calls, shared entities, or `relates_to` edges between services).

Present gaps as a prioritized list with **pre-formulated prompts** the user can pick from:

```
Phase 2 opportunities (pick a number, or explore something else):

  Undocumented areas:
  1. Pipeline Service lists 20 flows in its catalog but none have
     their own documentation
     → "Document individual pipeline flows" (est. ~15 artifacts)
  2. Core Service has 12 entities but only 6 have lifecycle docs
     → "Document remaining entity lifecycles"

  Cross-system patterns worth capturing:
  3. "order" and "item" appear in both Service A and Service B
     glossaries with different definitions — how do they relate?
  4. Three services define "project" differently — worth clarifying
  5. Service A uses both FK and link tables for relationships —
     what's the decision rule?
```

**Presentation rules:**
- **Never use artifact type prefixes (PAT-, PROC-, SCH-) in user-facing text.** The user thinks in questions and topics, not artifact types. Reef picks the right type internally when writing.
- **Frame gaps as questions or observations**, not as "missing artifact X." Say "none have their own documentation" not "0 per-flow PROC- artifacts."
- **Frame cross-system patterns as insights**, not as "PAT- candidates." Say "three services define Project differently — worth clarifying?" not "Create a PAT- comparing Project."
- **The key: every gap comes with a concrete next action.** The user doesn't need to formulate the prompt — they pick a number.

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

**CRITICAL: The user answers first.** Phase 2 is Socratic — "AI found the answers. I asked the questions." The user is the domain expert. Always ask, listen, THEN investigate. Never launch an investigation before the user has had a chance to answer.

For each question or topic:

1. **Present the question.** One at a time. Do not dump a list.
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
