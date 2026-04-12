---
description: "Automated knowledge deepening — manifest-driven artifact generation from snorkel+source output"
---

# /reef:scuba

Automated knowledge deepening. Builds an artifact generation manifest, then systematically produces advanced artifacts from what snorkel+source already generated. After the briefing, transitions to interactive exploration if the user wants to fill remaining gaps.

Core principle: "AI found the answers. I asked the questions."

## MANDATORY — Completion checklist

You MUST complete these steps IN ORDER. Do NOT skip any. Do NOT jump ahead.

1. **Locate the reef** (Step 1)
2. **Load context** (Step 2)
3. **Build the artifact generation manifest** (Step 2.5) — explicit list of every artifact to produce
4. **Automated Deepening** (Step 3) — work through the manifest, NO user input needed
5. **Briefing** (Step 4) — present manifest completion status, coverage gaps, next steps

**CRITICAL: Automated deepening ALWAYS runs first.** Even if the user says "let's answer the questions" or "go through all of them" — this means: run the automated pass first, THEN present findings in the briefing. The user's first interaction point is the briefing (Step 4), not before. Do NOT ask the user questions until automated deepening is complete.

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
- Read `sources/infra/` for extracted infrastructure patterns — cloud storage path conventions, runtime topology, message queues. These are especially important for pipeline/orchestration services with few database entities. Infrastructure patterns feed into flow catalogs (3.13), storage-related PROC- artifacts, and service dependency analysis (3.0, 3.7).
- Read all GLOSSARY- artifacts — these are needed for entity comparison and glossary cross-checking.
- **Mine snorkel artifacts for deepening signals.** Read the full body (not just frontmatter) of every existing artifact — especially Key Facts, Core Concepts, and known_unknowns sections. Extract patterns, domain-specific mechanisms, and architectural findings that deserve deeper investigation. Examples of signals:
  - A named pattern (e.g., "outbox pattern", "saga orchestration", "event sourcing") → candidate for a PROC- or DEC- artifact documenting the mechanism
  - A domain-specific mechanism (e.g., "hash-based deduplication", "materialized views", "optimistic locking with version counters") → candidate for a PROC- or DEC- artifact
  - A cross-service coupling signal (e.g., "shared API client must be passed to service initializers") → candidate for deeper CON- artifact
  - A gap or uncertainty in known_unknowns that code reading could partially resolve
  - **A cross-system divergence signal** — the same concept (e.g., "case", "dataset", "project") appearing in multiple services with different definitions, different lifecycles, or different modeling approaches → flag as **PAT- candidate** for interactive mode

  **Categorize each signal by depth level:**
  - **Scuba Phase 1**: understand the mechanism — what it is, which entities/services use it, how it works. Produces PROC-, DEC-, or CON- artifacts through code reading.
  - **Interactive mode (PAT- candidates)**: patterns require understanding *why* a design choice was made, not just *that* it exists. A PAT- artifact documents a reusable architectural convention — the design intent, the trade-offs, the decision rule for when to use it vs alternatives. These emerge from noticing the same problem solved differently across boundaries, or the same convention applied consistently for a reason code alone doesn't explain. **Flag PAT- candidates during automated deepening but create them in interactive mode**, where the user can confirm the design intent.
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

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py manifest --reef <reef-root>
```

This command handles everything programmatically:
- Entity tiering (Tier 1/2/3 classification, multi-app dedup)
- Checklists A-D (SYS- updates, flow catalog gaps, operational PROC-, auth/error-handling)
- PROC count floor validation (`Tier 1 count + services × 3`)
- CON- service pairs, RISK-, DEC-, GLOSSARY- per service

The output includes `entity_tiering` (per-service Tier 1/2/3 counts and names) and `proc_floor` (floor check result). Report these to the user.

**After running the command, augment the manifest manually for items code cannot detect:**

- **Checklist B — SCH- field lineage:** For services with ingestion/ETL/transform logic, plan one SCH- field lineage artifact per entity group. Common signals: `*_hash` fields, snapshot tables, computed fields.
- **Checklist E — Partial questions:** Read `.reef/questions.json`. For every `status: "partial"` question, check if a planned artifact addresses it. Add missing ones.
- **Checklist F — Cross-system:** Flag PAT- candidates for interactive mode (not Phase 1). Plan PROC- multi-app comparisons and CON- entity comparisons if needed.
- **Checklist G — Domain labeling:** Cross-system artifacts (CON- between services, GLOSSARY-UNIFIED, entity comparisons) must use the project-level domain slug from `project.json`.

Add discovered items to the manifest's `planned` array and re-save `.reef/scuba-manifest.json`.

**ANTI-CONSOLIDATION RULES (CRITICAL):**

1. Never merge entity lifecycle PROC- artifacts — each entity gets its own file.
2. Never merge comparison artifacts into entity artifacts — both must exist.
3. Never merge flow PROC- into a flow catalog — catalog is an index, flows are detail.
4. Never consolidate CON- artifacts — each pair is separate.
5. Never remove a planned artifact because "it's covered by" another. Overlap is fine. Missing is not.

### Confirm before executing

Present the manifest summary (by type, new vs update counts, entity tiering, PROC floor status). Then:

```
Estimated cost:
  ~3-5 artifacts/min with parallelism
  {N} artifacts → ~{N/4} to {N/3} min

Proceed? (yes / skip to interactive mode / adjust scope)
```

If the user wants to adjust scope, let them remove categories. **Do NOT start without user confirmation.**

---

## Step 3 — Phase 1: Automated Deepening

No user input after confirmation. Work through the manifest systematically — every planned artifact must be addressed (completed or explicitly skipped with reason). Report progress as you go: "Writing API-PAYMENTS-GATEWAY (1/9 API artifacts)..."

All artifacts are `status: "draft"`. Interactive mode can promote to `"active"` with user confirmation.

**CRITICAL — DO NOT CONSOLIDATE, MERGE, OR SKIP PLANNED ARTIFACTS.** If the manifest says to produce PROC-PAYMENTS-ORDER-LIFECYCLE and PROC-PAYMENTS-INVOICE-LIFECYCLE, you produce TWO separate artifacts — not one combined "entity overview." If you cannot find enough content for an artifact, write it thin (minimum Key Facts + known_unknowns listing what you couldn't determine). A thin artifact is infinitely better than a missing one. The manifest is the contract — every item in `planned` must appear in either `completed` or `skipped` (with an explicit reason). "Covered by another artifact" is NOT a valid skip reason.

**MANDATORY AGENT PROMPT PREAMBLE — include in EVERY agent prompt for Phase 1 batches:**

When launching agents for any Phase 1 batch (Batch 0-5), you MUST prepend this preamble to each agent's task prompt:

> "RULES — read before writing any artifact:
> 1. Each manifest item = one separate artifact file. Never combine multiple items into one.
> 2. Never merge entity lifecycles — PROC-PAYMENTS-ORDER-LIFECYCLE and PROC-PAYMENTS-INVOICE-LIFECYCLE are TWO files, not one overview.
> 3. Never skip an item because another artifact covers similar ground. Overlap is fine. Missing is not.
> 4. If content is thin, write it thin: minimum Key Facts + known_unknowns. Thin > missing.
> 5. After writing each artifact, move it from `planned` to `completed` in the manifest.
> 6. Your output must contain exactly as many artifact files as manifest items assigned to you.
> 7. DEPTH: Read at least 3 source files per artifact. Every Key Fact must cite a specific file path with `→`. Target 10-15 Key Facts, not just the minimum. If the artifact updates an existing one, read its known_unknowns first and resolve as many as you can."

This preamble exists because Phase 1 agents do not see the full skill text. Without it, agents consolidate planned artifacts into fewer, broader docs — the #1 failure mode in previous iterations.

### Lint-on-write (MANDATORY for every artifact)

After writing each artifact file, immediately lint it before moving on:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Parse the JSON output, filter to errors for this artifact's ID. If errors are found, fix them now (ID casing, missing fields, filename mismatch, wikilink sync). Do NOT batch lint errors to the end — catch them at write-time. This applies to both automated deepening agents and interactive-mode artifact writes.

### Manifest completion tracking (CRITICAL)

After each artifact is written and lint-clean, you MUST update `.reef/scuba-manifest.json`:
1. Move the item from `planned` to `completed` with a timestamp.
2. If an artifact is skipped, move it to `skipped` with a `reason` field.
3. After each batch completes, verify that `completed.length + skipped.length + planned.length` equals the original total. If not, investigate — items are being lost.

This is not optional. The manifest is the single source of truth for what scuba produced. If it shows `completed: []` after a full run, the tracking failed and the next run cannot resume correctly.

### Minimum depth validation per artifact

After writing each artifact, validate it against the minimum depth bar for its type. If an artifact fails validation, read more source code and deepen it before marking it complete.

| Type | Min Key Facts | Target Key Facts | Required Sections | Required Visuals |
|------|---------------|------------------|-------------------|------------------|
| SYS- | 8 | 12-15 | Overview, Key Facts, Responsibilities, "Does NOT Own", Core Concepts, Dependencies table, Runtime Components, Related | — |
| API- | 8 | 10-12 | Overview, Key Facts, Source of Truth, Resource Map, Worked Example, Related | — |
| SCH- | 6 | 10-12 | Overview, Key Facts, Entities (with field tables), Related | Mermaid `erDiagram` (mandatory) |
| PROC- (entity lifecycle) | 8 | 12-15 | Purpose, Key Facts, Fields table, Relationships, Creation path, States/Transitions, Agent Guidance, Related | Mermaid `stateDiagram-v2` if status field exists |
| PROC- (flow/pipeline) | 8 | 10-12 | Purpose, Key Facts, Input/Output, Steps/Phases, Error Handling, Related | Mermaid `flowchart` or `sequenceDiagram` |
| PROC- (operational) | 6 | 8-10 | Purpose, Key Facts, Scope, Current State, Related | — |
| CON- | 6 | 8-10 | Parties, Key Facts, Agreement, Current State, Impact Analysis, Related | Mermaid `sequenceDiagram` |
| DEC- | 5 | 8-10 | Context, Decision, Key Facts, Rationale, Consequences, Related | — |
| RISK- | 5 | 8-10 | Description, Key Facts, Findings table, Recommended Actions, Related | — |
| GLOSSARY- | N/A | N/A | Overview, Terms table, Related | — |

An artifact that does not meet its minimum Key Facts count is **not complete**. Read additional source files to find more verifiable claims before marking it done.

**Known-unknowns resolution (for updates):** When updating an existing artifact, read its `known_unknowns` list first. For each item, attempt to resolve it by reading the relevant source code. Resolved items become Key Facts (with `→ source`). Unresolvable items stay in `known_unknowns`. This is the single highest-ROI quality action — the gaps are already identified.

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

### PROC count gate (MANDATORY — prevents process collapse)

Before presenting results, count actual PROC- artifacts in `artifacts/processes/`. Compare against the manifest:

```
PROC- artifact check:
  Manifest planned:     {N} PROC- artifacts
  Actually produced:    {M} PROC- artifacts
  Tier 1 entities:      {T1} (from manifest entity_tiering)
  Tier 1 coverage:      {M_entity}/{T1} ({%})
```

**If `M < N × 0.7` (more than 30% of planned PROC- were lost):** This is a process collapse. Phase 1 agents consolidated or skipped artifacts instead of generating them. Do NOT proceed to the briefing. Instead:
1. Identify which planned PROC- items are in neither `completed` nor `skipped`.
2. Re-generate the missing ones — include the agent prompt preamble from Step 3. Launch one agent per missing PROC- artifact.
3. Re-count and report.

**If Tier 1 entity coverage is below 70%:** Core entities are missing lifecycle artifacts. Add the missing Tier 1 entities before proceeding. Do NOT add Tier 2/3 entities to fill the gap — that creates bloat, not coverage.

This gate exists because iterations 4→5 showed a 60% PROC collapse (67→27) that devastated coverage. The fix is mechanical: count what was planned vs what was produced, and fill gaps before moving on.

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

Present the coverage gaps and cross-system patterns from the gap detection above as a single numbered list. No artifact type prefixes in user-facing text. The user picks a number or names their own topic.

Then present next steps:

```
Scuba complete. The reef now has {N} artifacts at draft depth.

Next steps:
- Pick a gap above to explore interactively — I'll ask questions, verify against code, and create artifacts from your answers.
- `/reef:deep` — exhaustive line-by-line tracing of a specific area.
- `/reef:test` — see how well the reef answers your questions right now.
- `/reef:health` — check artifact freshness and coverage.
```

If the user picks a gap or asks to explore a topic, enter **interactive mode** (below).

---

## Interactive Mode

When the user wants to explore gaps after the briefing — or returns later to deepen artifacts — follow these rules:

**Core principle:** "AI found the answers. I asked the questions." The user is the domain expert. Claude reads code; the user knows context.

1. **One question at a time.** Read `${CLAUDE_PLUGIN_ROOT}/references/scuba-question-patterns.md` for question templates. Present one, wait for the answer, then verify against code. Never dump a list.
2. **User answers first.** Ask, listen, THEN investigate. If the user says "I don't know," offer to trace it in code. If they say "skip," move on.
3. **Verify against code.** After the user answers, read relevant source files to confirm or contradict. Report briefly: "The code confirms X — found at `src/service.py:L42`."
4. **Abort if stuck.** If 5+ file reads yield no clear answer, stop and report what you have so far. Ask whether to keep digging or move on.
5. **Create artifacts from findings.** When enough material accumulates, propose an artifact (type, ID, scope). Follow `references/artifact-contract.md`. Cross-system artifacts use the project-level domain slug from `project.json`. Status is `"active"` when user-confirmed, `"draft"` otherwise.
6. **Post-write:** lint, snapshot, rebuild-index, rebuild-map, log — same as Phase 1.
7. **At pauses,** summarize: artifacts created/updated, questions answered, remaining gaps. Update `.reef/questions.json`.

---

## Key Rules

- Never invent facts. If uncertain, add to `known_unknowns`.
- Honest gaps beat confident lies.
- The user is the domain expert. Claude reads code; the user knows context.
- **Phase 1 must complete fully before entering interactive mode.**
- **Phase 1 artifacts are all `status: draft`** unless analysis is highly confident.
- Interactive mode can promote artifacts to `status: active` based on user confirmation.

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
