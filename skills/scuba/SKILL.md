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
- Read `sources/context/` and `sources/raw/` for non-code context the user has provided — requirements docs, architecture decisions, SOPs, meeting notes, roadmaps, diagrams, or any other material. These are first-class sources: cite them in artifact `sources` fields, use them to resolve known_unknowns, and prefer them over code-inferred guesses for business intent, design rationale, and process definitions. If `sources/context/` is empty, that is fine — the reef works without it, but the artifacts will be code-only.
- **New context alert.** If new context files are found that aren't yet referenced by any artifact, mention it before starting Phase 1: "I see you've added N new context files (list them). I'll use these as I deepen artifacts." No confirmation needed — just acknowledge so the user knows they'll be picked up.
- Read all GLOSSARY- artifacts — these are needed for entity comparison and glossary cross-checking.
- **Mine snorkel artifacts for deepening signals.** Read the full body (not just frontmatter) of every existing artifact — especially Key Facts, Core Concepts, and known_unknowns sections. Extract patterns, domain-specific mechanisms, and architectural findings that deserve deeper investigation. Examples of signals:
  - A named pattern (e.g., "outbox pattern", "saga orchestration", "event sourcing") → candidate for a PROC- or DEC- artifact documenting the mechanism
  - A domain-specific mechanism (e.g., "hash-based deduplication", "materialized views", "optimistic locking with version counters") → candidate for a PROC- or DEC- artifact
  - A cross-service coupling signal (e.g., "shared API client must be passed to service initializers") → candidate for deeper CON- artifact
  - A gap or uncertainty in known_unknowns that code reading could partially resolve
  - **A cross-system divergence signal** — the same concept (e.g., "case", "dataset", "project") appearing in multiple services with different definitions, different lifecycles, or different modeling approaches → flag as **PAT- candidate** for interactive mode

  **Categorize each signal by depth level:**
  - **Scuba Phase 1**: understand the mechanism — what it is, which entities/services use it, how it works. Produces PROC-, DEC-, or CON- artifacts through code reading.
  - **Phase 1 (high-confidence PAT- candidates)**: patterns that `reef.py manifest` detected automatically — cross-service entity divergences and repeated architectural patterns (same concept modeled differently, same operational pattern implemented differently). These are planned in the manifest and produced during Phase 1 sub-step 3.9. They document what diverges and how, leaving design intent as a `known_unknown` for the user to fill in later.
  - **Interactive mode (subjective PAT- candidates)**: patterns that require understanding *why* a design choice was made, not just *that* it exists — e.g., a convention applied consistently for a reason code alone doesn't explain. These emerge from human insight during the briefing. Flag them during automated deepening and surface them in the Step 4 PAT- callout.
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

This command handles the following programmatically — **do NOT duplicate this work manually:**

- **Checklist A:** SYS- updates (one per service)
- **Checklist B2:** PAT- from cross-service divergence — three detection methods:
  - Exact entity name match across services
  - Fuzzy token-overlap matching (e.g., "project" matches "acquisition project")
  - Glossary-based detection (reads GLOSSARY-UNIFIED disambiguation table)
  - Repeated operational patterns across services (AUTH, ERROR-HANDLING, etc.)
- **Checklist C:** Individual PROC- from catalog/inventory artifacts
- **Checklist D:** Operational PROC- per service (AUTH, ERROR-HANDLING)
- **Checklist E:** FE/BE contracts (detects frontend/backend repo pairs per service)
- **Checklist F (intra):** Intra-service data contracts (scans source index for hash, export, identifier, checksum, serializer, storage signals)
- **Checklist F2:** Multi-app comparison PROC- (pairwise schema comparisons for services with multiple sub-apps)
- **Checklist G:** SCH- field lineage (detects services with ingestion/ETL keywords)
- Entity tiering (Tier 1/2/3 classification, multi-app dedup)
- PROC count floor validation (`Tier 1 count + services × 3`)
- CON- service pairs, RISK-, DEC-, GLOSSARY- per service

The output includes `entity_tiering` (per-service Tier 1/2/3 counts and names) and `proc_floor` (floor check result). Report these to the user.

### MANDATORY — Verify the manifest before presenting (do NOT skip)

The script handles the bulk of manifest generation, but you MUST verify its output before presenting to the user. Run through this checklist:

1. **PAT- count check.** If the reef has 2+ services and the manifest has fewer than 3 PAT- artifacts, something is wrong. Check: does GLOSSARY-UNIFIED have a disambiguation table? Are entity names parseable from schema.md files? If the script missed divergences you can see in the glossary, add them manually.

2. **CON- count check.** The manifest should have at minimum: N×(N-1)/2 service-pair contracts + FE/BE contracts (one per frontend repo) + intra-service contracts (from source index scanning). If CON- count equals exactly N×(N-1)/2 with nothing else, the FE/BE and intra-service detection may have failed — check the output.

3. **PROC floor check.** The script reports `floor_met: true/false`. If false, identify the gap and add missing PROC- items (flow catalogs for non-pipeline services, multi-app comparisons, infrastructure PROC-).

4. **Partial questions.** Read `.reef/questions.json`. For every `status: "partial"` question, check if a planned artifact addresses it. Add missing ones.

5. **Domain labeling.** Cross-system artifacts (CON- between services, GLOSSARY-UNIFIED, entity comparisons, PAT-) must use the project-level domain slug from `project.json`, not a single service's domain.

**If you add items, append them to the manifest's `planned` array and re-save `.reef/scuba-manifest.json`.**

### Minimum manifest size gate

Before presenting the manifest to the user, check the total against this formula:

```
minimum = (services × 6) + (services × (services-1) / 2) + (PAT candidates from glossary)
```

For a 4-service reef with 5 glossary disambiguation terms, the minimum is ~34. If the actual manifest total is below this minimum, **do not present it** — investigate what the script missed and augment first. A thin manifest produces a thin reef, and the user will rightfully be frustrated.

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

When launching agents for any Phase 1 batch (Batch 0-7), you MUST prepend this preamble to each agent's task prompt:

> "RULES — read before writing any artifact:
> 1. Each manifest item = one separate artifact file. Never combine multiple items into one.
> 2. Never merge entity lifecycles — PROC-PAYMENTS-ORDER-LIFECYCLE and PROC-PAYMENTS-INVOICE-LIFECYCLE are TWO files, not one overview.
> 3. Never skip an item because another artifact covers similar ground. Overlap is fine. Missing is not.
> 4. If content is thin, write it thin: minimum Key Facts + known_unknowns. Thin > missing.
> 5. Your output must contain exactly as many artifact files as manifest items assigned to you. List every artifact ID you were assigned and confirm each one was written.
> 6. DEPTH: Read at least 3 source files per artifact. Every Key Fact must cite a specific file path with `→`. Target 10-15 Key Facts, not just the minimum. If the artifact updates an existing one, read its known_unknowns first and resolve as many as you can.
> 7. When you finish, output a completion report listing every assigned artifact ID and its status (written / skipped with reason). This is mandatory — do not end without it."

This preamble exists because Phase 1 agents do not see the full skill text. Without it, agents consolidate planned artifacts into fewer, broader docs — the #1 failure mode in previous iterations.

**DO NOT delegate manifest tracking to agents.** Agents write artifacts and report what they wrote. The orchestrator (you) owns the manifest. See "Orchestrator-owned manifest tracking" below.

### Lint-on-write (MANDATORY for every artifact)

After writing each artifact file, immediately lint it before moving on:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Parse the JSON output, filter to errors for this artifact's ID. If errors are found, fix them now (ID casing, missing fields, filename mismatch, wikilink sync). Do NOT batch lint errors to the end — catch them at write-time. This applies to both automated deepening agents and interactive-mode artifact writes.

### Orchestrator-owned manifest tracking (CRITICAL)

**You (the orchestrator) own manifest tracking — not agents.** Agents write artifact files and return a completion report. After each agent returns, YOU must:

1. Parse the agent's completion report to get the list of artifact IDs it wrote.
2. Verify each claimed artifact actually exists on disk (`artifacts/{type}/{filename}.md`).
3. For each verified artifact, move it from `planned` to `completed` in `.reef/scuba-manifest.json` with a timestamp.
4. For any assigned artifact the agent did NOT write, check if it's in the agent's skip list with a reason. If so, move to `skipped`. If the agent simply didn't mention it, that artifact was **silently dropped** — add it to a `dropped` recovery list.

**After EVERY batch completes, run the batch verification gate** (see below). Do NOT proceed to the next batch until this passes.

### Batch verification gate (MANDATORY between every batch)

After all agents in a batch return, before starting the next batch:

1. Count: `assigned` (items given to agents in this batch), `written` (verified on disk), `skipped` (with reason), `dropped` (unaccounted for).
2. **If `dropped > 0`:** Re-launch agents for the dropped items. Include the original preamble plus: "These items were assigned to a previous agent that failed to produce them. You MUST write each one. There are only {N} items — do not stop until all {N} are written."
3. **If after retry `dropped` is still > 0:** Write them yourself (the orchestrator). A thin artifact with minimum Key Facts is acceptable. Zero is not.
4. Re-verify: `completed + skipped` for this batch must equal `assigned`. Only then proceed.
5. Log: "Batch {N} complete: {written} written, {skipped} skipped, {dropped} recovered."

**Invariant check:** After every batch, verify `completed.length + skipped.length + planned.length` equals the original manifest total. If not, items are being lost — stop and investigate before continuing.

### Minimum depth validation per artifact

After writing each artifact, validate it against the minimum depth bar for its type. If an artifact fails validation, read more source code and deepen it before marking it complete.

| Type | Min Key Facts | Target Key Facts | Required Sections | Required Visuals |
|------|---------------|------------------|-------------------|------------------|
| SYS- | 8 | 12-15 | Overview, Key Facts, Responsibilities, "Does NOT Own", Core Concepts, Dependencies table, Runtime Components, Related | — |
| API- | 8 | 10-12 | Overview, Key Facts, Source of Truth, Resource Map, Worked Example, Related | — |
| SCH- | 6 | 10-12 | Overview, Key Facts, Entities (with field tables), Worked Examples (queries + enum tables), Related | Mermaid `erDiagram` (mandatory) |
| PROC- (entity lifecycle) | 8 | 12-15 | Purpose, Key Facts, Fields table, Relationships, Creation path, States/Transitions, Worked Examples (queries + enum tables), Agent Guidance, Related | Mermaid `stateDiagram-v2` if status field exists |
| PROC- (flow/pipeline) | 8 | 10-12 | Purpose, Key Facts, Input/Output, Steps/Phases, Error Handling, Related | Mermaid `flowchart` or `sequenceDiagram` |
| PROC- (operational) | 6 | 8-10 | Purpose, Key Facts, Scope, Current State, Related | — |
| CON- | 6 | 8-10 | Parties, Key Facts, Agreement, Current State, Impact Analysis, Related | Mermaid `sequenceDiagram` |
| DEC- | 5 | 8-10 | Context, Decision, Key Facts, Rationale, Consequences, Related | — |
| RISK- | 5 | 8-10 | Description, Key Facts, Findings table, Recommended Actions, Related | — |
| PAT- | 6 | 8-10 | Overview, Key Facts, Where It Appears, Design Intent, Trade-offs, Agent Guidance, Related | — |
| GLOSSARY- | N/A | N/A | Overview, Terms table, Related | — |

An artifact that does not meet its minimum Key Facts count is **not complete**. Read additional source files to find more verifiable claims before marking it done.

**Known-unknowns resolution (for updates):** When updating an existing artifact, read its `known_unknowns` list first. For each item, attempt to resolve it by reading the relevant source code. Resolved items become Key Facts (with `→ source`). Unresolvable items stay in `known_unknowns`. This is the single highest-ROI quality action — the gaps are already identified.

**Parallelism — CRITICAL for time efficiency.** The 16 sub-steps are NOT all sequential. Execute in 8 parallel batches. Each batch is scoped narrowly so agents cannot lose focus or silently drop items.

| Batch | Sub-steps | What | Parallelism | Max items/agent |
|-------|-----------|------|-------------|-----------------|
| 0. Foundation | 3.0 | SYS- artifact updates | One agent per service | 1 |
| 1. Spec Layer | 3.1, 3.2 | API patterns + Schema docs | One agent per service | ~3-5 |
| 2. Entity Deep-Dive | 3.3, 3.15, 3.16 | Entity lifecycles + per-collection SCH- + field lineage | One agent per service | ~5-15 |
| 3. Service Signals | 3.4, 3.6, 3.10, 3.13 | Auth + error handling + risks + flow catalogs | One agent per service | ~4 |
| 4a. Service Pair CON | 3.7 | Service-pair contracts (N×(N-1)/2) | One agent per pair | 1 |
| 4b. Intra-service CON | 3.7b | Intra-service data contracts | One agent per service | ~1-3 |
| 4c. Comparisons | 3.5, 3.8, 3.14 | FE/BE contracts + entity comparisons + multi-app comparisons | One agent per service | ~2-5 |
| 5a. PAT | 3.9 | Pattern artifacts from manifest + deepening signals | One agent for ALL PAT items | all PAT |
| 5b. DEC + GLOSSARY | 3.11, 3.12 | Decisions + per-service glossaries | One agent per service | ~2 |

**Why 8 batches instead of 6:** Previous iterations showed that bundling CON service-pairs with intra-service CON and comparisons into one batch caused agents to complete the first sub-step and silently drop the rest. Same for bundling PAT with DEC/GLOSSARY. Each artifact type that has been dropped in prior iterations now gets its own batch.

**Batch 4b is critical.** Intra-service CON artifacts (identifier conventions, export formats, path construction, auth models, event schemas) are the most commonly dropped artifact type. They require scanning service internals for specific signal files — a different task than writing service-pair contracts. A dedicated agent per service ensures they are not lost.

**Batch 5a is critical.** PAT artifacts require reading artifacts from multiple services to compare divergences. They are a synthesis task, not a per-service task. One dedicated agent handles ALL manifest-planned PAT items plus any PAT candidates flagged during Phase 1. This agent gets the full list of PAT IDs and must write every one.

Batch 0 runs first. Batches 1-3 run concurrently. Batches 4a-4c run concurrently (after 1-3). Batches 5a-5b run concurrently (after 4a-4c).

**Minimum execution:** 4 sequential rounds (Batch 0 → Batches 1-3 → Batches 4a-4c → Batches 5a-5b), each internally parallel. Run the **batch verification gate** between every round.

**Read `references/scuba-phase1-substeps.md`** for full details on every sub-step (3.0–3.16). The reference file is the source of truth for what each sub-step does, what templates to use, and what completeness checks to run.

### Sub-step → Batch dispatch table

| Sub-step | Batch | Artifact type | Key constraint |
|----------|-------|--------------|----------------|
| 3.0 SYS- update | 0 | SYS- | Must run first; one agent/service |
| 3.1 API patterns | 1 | API- | Requires Worked Example |
| 3.2 Schema docs | 1 | SCH- | Requires Mermaid erDiagram |
| 3.3 Entity lifecycles | 2 | PROC- lifecycle | One per Tier 1 entity; stateDiagram if status field |
| 3.4 Auth boundaries | 3 | PROC- operational | One per service |
| 3.5 FE/BE contracts | 4c | CON- | Skip if no frontend repos |
| 3.6 Error handling | 3 | PROC- or RISK- | One per service |
| 3.7 Service pair CON | 4a | CON- pair | **One agent per pair**; count must = N×(N-1)/2 |
| 3.7b Intra-service CON | 4b | CON- intra | **Dedicated agent per service**; items tagged `checklist-F-intra` |
| 3.8 Entity comparison | 4c | CON- | Skip for single-service reefs |
| 3.9 PAT- generation | 5a | PAT- | **ONE agent for ALL PAT items**; must write every manifest-planned PAT |
| 3.10 RISK- | 3 | RISK- | Severity by density |
| 3.11 DEC- | 5b | DEC- | ADR format |
| 3.12 GLOSSARY- | 5b | GLOSSARY- | Per-service + SOURCE-INDEX |
| 3.13 Flow catalogs | 3 | PROC- flow | Skip if no pipelines |
| 3.14 Multi-app comparison | 4c | PROC- comparison | Skip for single-app services |
| 3.15 Per-collection SCH- | 2 | SCH- | 3+ collections only |
| 3.16 Field lineage | 2 | SCH- lineage | Skip for simple CRUD |

**Batches 4b and 5a are the most critical.** Intra-service CON and PAT artifacts are the most commonly dropped types in prior iterations. They each have dedicated batches with isolated agents specifically to prevent this. Do NOT merge them with other batches for "efficiency."

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

Then present the completion message and next steps. The tone should be celebratory — the user just completed a significant journey. Frame what they now have in terms of practical value, not artifact counts.

```
🎉 Scuba complete. Your reef is ready for real work.

You now have a structured knowledge base covering {N} artifacts across
{S} services. This isn't just documentation — it's a working reference
you can use to:

  • Write scripts against your data model without reading source code
  • Create test datasets using the right fields and relationships
  • Draft tech proposals grounded in actual architecture
  • Write requirements docs with full cross-service context
  • Onboard teammates by pointing them at the reef instead of
    scheduling walkthrough meetings

The automated pipeline is done. What you have compounds from here —
every question you explore makes the reef smarter.

Have SRDs, design docs, SOPs, or meeting notes? Drop them into
sources/context/ — the reef gets sharper when it knows the why
behind the code, not just the what.
```

After the celebration, present coverage gaps as numbered options (same as above).

### PAT- verification (MANDATORY — not optional, not interactive)

All manifest-planned PAT- artifacts MUST be generated during Phase 1 (Batch 5a, sub-step 3.9). They are NOT deferred to interactive mode. Interactive mode is for subjective PAT candidates only — patterns the user might want to explore that weren't auto-detected.

**Verification:** After Batch 5a completes, check that every PAT- entry in the manifest is in `completed`. If any are missing, this is a Batch 5a failure — re-run the batch verification gate (re-launch an agent for the missing PAT items).

**Briefing presentation:** Report completed PAT artifacts as part of the standard briefing. If subjective PAT candidates were flagged during Phase 1 (patterns noticed but not in the manifest), present them:

```
📐 Additional pattern candidates: {N}

Phase 1 noticed {N} patterns that weren't in the automated manifest.
These may benefit from your domain context:

  {numbered list with plain-language descriptions}

Pick a number to create it now, or I can generate all {N} automatically.
```

**Rules:**
- Manifest-planned PAT- are never presented as options — they are already written.
- Subjective PAT- candidates are optional. The user chooses whether to pursue them.
- Phrase each as the design question it answers, not an artifact ID.
- If the user says "generate all," create each using `references/templates/pattern.md`. Mark as `status: draft`.

Then, **only if gaps exist that would benefit from line-by-line tracing**, add a soft lead-in to deep — framed through the gaps, not as a sales pitch:

```
Some areas have surface-level coverage where the real complexity lives
in execution paths and edge cases:

  {top 2-3 areas from deep-dive flags, phrased as curiosity hooks —
   e.g., "How does the finalization flow actually enforce overlap
   constraints?" not "PROC-PAYMENTS-ORDER-FINALIZATION needs deep tracing"}

When you're curious about those, `/reef:deep` traces them line by line.
No rush — the reef is already useful without it.
```

**Rules for the deep lead-in:**
- Only show if Step 4's deep-dive flags identified concrete candidates.
- Maximum 3 items. Pick the highest gap-to-value ratio (areas where scuba flagged known unknowns that matter for real tasks).
- Phrase each as a question the user might actually wonder about, not an artifact ID or type prefix.
- Never pressure. "When you're curious" / "when you're ready" — not "you should" or "recommended next step."

If the user picks a gap or asks to explore a topic, enter **interactive mode** (below).

---

## Interactive Mode

When the user wants to explore gaps after the briefing — or returns later to deepen artifacts.

### Mode selection (MANDATORY before starting)

Before asking the first question, present the mode choice:

```
How would you like to explore these gaps?

  1. I'll answer — you ask me questions one at a time, I provide domain context
  2. Reef answers — reef investigates the code and fills in answers autonomously,
     then shows me what it found for review
```

Wait for the user to choose. Do NOT proceed without a selection.

- **Option 1 → Human-guided mode** (rules below)
- **Option 2 → Self-guided mode**: For each question, read source code to find the answer yourself. Present each finding as: "Q: {question} — My finding: {answer with source citations}. Does this match your understanding?" The user reviews and corrects. This is faster but may miss domain context that isn't in code.

### Human-guided mode rules

**Core principle:** "AI found the answers. I asked the questions." The user is the domain expert. Claude reads code; the user knows context.

0. **Load the question agenda first.** Read `.reef/questions.json` and collect all `"status": "unanswered"` or `"status": "partial"` questions. These are the primary agenda — they were surfaced during prior discovery and are waiting for domain input. Present the count: "I have {N} questions from previous discovery, plus {M} new ones from coverage gaps. Starting with the discovery backlog. (Question 1 / {total})"
1. **One question at a time, with progress.** Show "Question {N} / {total}" with each question. Read `${CLAUDE_PLUGIN_ROOT}/references/scuba-question-patterns.md` for question templates. Present one, wait for the answer, then verify against code. Never dump a list.
2. **User answers first.** Ask, listen, THEN investigate. If the user says "I don't know," offer to trace it in code. If they say "skip," move on.
3. **WAIT for the user's response after each question.** Do NOT answer your own question. Do NOT proceed to the next question without user input. Do NOT auto-complete remaining questions after receiving one answer. Each question is a turn: you ask → user responds → you verify → you ask the next one. **This is a hard rule — violating it defeats the purpose of interactive mode.**
4. **Verify against code.** After the user answers, read relevant source files to confirm or contradict. Report briefly: "The code confirms X — found at `src/service.py:L42`."
5. **Write findings immediately.** After verifying an answer, update the relevant artifact right away — add verified facts to Key Facts, resolve known_unknowns, update sections. Do NOT batch artifact updates. A session that ends unexpectedly should not lose user-confirmed facts. Also update the question's status in `.reef/questions.json` to `"answered"`.
6. **Abort if stuck.** If 5+ file reads yield no clear answer, stop and report what you have so far. Ask whether to keep digging or move on.
7. **Create new artifacts from findings.** When a verified answer doesn't fit an existing artifact, propose a new one (type, ID, scope). Follow `references/artifact-contract.md`. Cross-system artifacts use the project-level domain slug from `project.json`. Status is `"active"` when user-confirmed, `"draft"` otherwise.
8. **Post-write:** lint, snapshot, rebuild-index, rebuild-map, log — same as Phase 1.
9. **At pauses,** summarize: artifacts created/updated, questions answered, remaining gaps.

### Self-guided mode rules

1. **Load the question agenda first** — same as human-guided mode rule 0. Read `.reef/questions.json` for unanswered/partial questions. These come first.
2. **Work through questions autonomously.** For each question (backlog first, then coverage gaps), answer by reading source code. Use `scuba-question-patterns.md` for framing.
3. **Present findings in batches of 3-5.** After investigating 3-5 questions, pause and show the user what you found. Format: question, finding, source citation. Ask: "Anything to correct or add before I continue?"
4. **User corrections are gold.** If the user corrects a finding, that correction takes priority over code evidence — it's domain knowledge the code doesn't capture. Update the finding and note the source as "domain expert input."
5. **Write findings immediately** — same as human-guided mode. Update artifacts and question bank after each batch review, not at the end.
6. **Create new artifacts the same way** as human-guided mode (propose, confirm, write, lint).
7. **Post-write and pause rules** are the same as human-guided mode.

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
