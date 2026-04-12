---
description: "Re-index sources and update stale artifacts"
---

# /reef:update

Re-index all sources, detect what changed, and update affected artifacts. This is the "fix staleness" skill. `/reef:health` reports; `/reef:update` fixes.

**Default mode is fully automatic.** All updates are applied without prompting. Use `--review` (or say "review mode") to approve each artifact individually.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Find the `.reef/` directory in cwd or parents. Read `project.json` from the reef root.

### 2. Re-extract API specs and ERDs

Run the source extraction skill to refresh API specs and ERDs from current code. This uses cached recipes from `.reef/source-recipes.json`, so it replays the exact commands that worked during the initial extraction — no stub discovery or environment debugging needed.

Read `${CLAUDE_PLUGIN_ROOT}/skills/source/SKILL.md` and follow its instructions. Key differences from a first run:

- **Tier 1 (cached recipe replay) will handle most repos.** The recipe cache stores the command, env vars, PYTHONPATH, and stub list. Replay produces a fresh spec from today's code.
- **If a cached recipe fails** (new dependency, changed env var), it falls through to Tier 2 (fresh runtime extraction) automatically.
- **This step is fully automated** — no user input needed unless a tool is missing.

After source extraction completes, report what was refreshed:

```
Source re-extraction complete. 8 API specs and 5 ERDs refreshed from current code.
```

### 3. Re-index sources

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index --reef <reef-root>
```

### 4. Detect changes

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff --reef <reef-root>
```

Present the change summary to the user:

```
Source changes since last update:
  service-a: 3 updated, 1 new, 0 deleted
  service-b: 0 changes
Affected artifacts: SYS-INGEST, SCH-INGEST-ORDER, PROC-INGEST-ORDER-LIFECYCLE
```

Build the affected list by matching changed files to artifacts that reference them in `sources`.

### 4.5. Detect new context

Scan `sources/context/` and `sources/raw/` for files that are not yet referenced by any artifact's `sources` field. These are newly added non-code context — requirements docs, design decisions, SOPs, meeting notes, roadmaps, or other material the user dropped in since the last update.

If new context files are found:

```
New context detected:
  sources/context/requirements/order-fulfillment-srd.pdf      (new)
  sources/context/decisions/overlap-constraint-adr.md          (new)
  sources/context/meetings/2026-04-10-platform-knowledge-share.md (new)
```

For each new context file:

1. Read it (supports .md, .txt, .pdf, .csv — skip binary files other than PDF).
2. Match its content against existing artifacts' `known_unknowns`. If a context doc answers or partially answers a known_unknown, flag that artifact for update.
3. Match against artifact topics more broadly — an SRD about the order fulfillment system is relevant to PROC- and SCH- artifacts covering that feature, even if they have no explicit known_unknown about it.

Collect all context-affected artifacts into the same update queue as code-affected artifacts (Step 7). When updating these artifacts:
- Cite the context doc in the artifact's `sources` field.
- Resolve any `known_unknowns` that the doc answers — move them to Key Facts with a citation.
- Add new Key Facts if the doc reveals information not captured anywhere.

Report context impact alongside code changes:

```
Context impact:
  order-fulfillment-srd.pdf → resolves 2 known_unknowns in PROC-PAYMENTS-ORDER-FINALIZATION
  overlap-constraint-adr.md → new DEC- candidate (design rationale not yet captured)
  2026-04-10-platform-knowledge-share.md → enriches SYS-PLATFORM with integration context
```

If `sources/context/` and `sources/raw/` have no new files, skip this step silently.

### 5. Classify each changed file

| Classification | Meaning | Action |
|---|---|---|
| new | File appeared that was not previously indexed | Flag artifacts in the same module for potential new content |
| updated | Content hash changed since last snapshot | Flag artifacts that reference this file |
| renamed | Path changed but content is similar | Update `sources` refs in affected artifacts |
| deleted | File removed from disk | Warn that referencing artifacts may be invalid |
| unchanged | No movement | Skip |

### 6. Detect what's new and what's gone

Before updating existing artifacts, check whether the codebase has structurally changed — new entities, removed entities, new services, or removed services.

#### 6a. What's new

Compare current source code against the reef's existing artifact coverage:

1. **New services.** Check `project.json` source paths for repos/directories that exist on disk but have no SYS- artifact.
2. **New entities.** Scan model/entity files in changed or new source files. Compare discovered entity names against existing SCH- artifacts. Any entity that has no corresponding SCH- artifact is new.
3. **New API groups.** Compare the refreshed `openapi.json` specs against existing API- artifacts. Look for new tag groups or route prefixes that aren't covered.
4. **New infrastructure.** Compare refreshed `sources/infra/` files against existing artifacts. New buckets, queues, or services that aren't referenced anywhere.

For each discovery, auto-generate a draft artifact using the same templates and conventions as snorkel. Apply the artifact contract, lint on write.

Report:

```
New discoveries:
  + SCH-ORDERS-FULFILLMENT — new entity (FulfillmentRecord model added in orders/models/fulfillment.py)
  + API-PAYMENTS-WEBHOOKS — new API group (webhooks/ routes added, 6 endpoints)
  + PROC-PIPELINE-RETRY-QUEUE — new Celery task queue detected in sources/infra/pipeline/queues.md
```

#### 6b. What's gone

Check whether entities, API groups, or services have been removed from the codebase:

1. **Removed source files.** For each deleted source file, check if any artifact's `sources` field exclusively references that file. If an artifact's sources are all gone, the artifact is orphaned.
2. **Removed entities.** For each SCH- artifact, verify the model/table it documents still exists in source code. If the model file is deleted or the class/table is removed, the artifact is orphaned.
3. **Removed API groups.** For each API- artifact, verify the route group still exists in the refreshed `openapi.json`. If the tag/prefix is gone, the artifact is orphaned.
4. **Removed services.** If a service's source path no longer exists on disk, all its artifacts are orphaned.

**Do not auto-delete orphaned artifacts.** Mark them and ask the user:

1. Add `status: orphaned` to the artifact's frontmatter.
2. Add a `freshness_note` explaining what was removed and when.
3. Present the list and ask the user which to delete:

```
Potentially orphaned (source code removed):

  1. SCH-ORDERS-LEGACY-CART — model class LegacyCart no longer found in orders/models/
  2. API-PLATFORM-ANALYTICS-V1 — route prefix /api/v1/analytics/ absent from refreshed spec
  3. PROC-PIPELINE-NIGHTLY-SYNC — referenced source file pipeline/jobs/nightly_sync.py deleted

These artifacts have been marked as orphaned.
Delete any? Enter numbers (e.g. "1, 3"), "all", or "none" to keep them for now.
```

- **On delete:** Remove the artifact file, clean up `relates_to` references in other artifacts that pointed to it, and run `rebuild-index` and `rebuild-map`.
- **On keep:** Leave them marked as orphaned. `/reef:health` will continue to surface them until they are deleted or their status is restored.

### 7. Update each affected artifact

Process artifacts one at a time. For each affected artifact:

1. Read the current artifact file.
2. Re-read the changed source files it references.
3. Compare current Key Facts against source content.
4. Determine specific updates:
   - Changed Key Facts (old value → new value).
   - New information found in sources.
   - Claims that no longer hold (source content removed or contradicted).
   - Updated `freshness_note` and `last_verified`.
5. **Glossary cross-check.** Compare the artifact's terms against GLOSSARY- artifacts. If any Key Fact or description uses a domain term inconsistently with the glossary, fix it. If the source code reveals the glossary definition is outdated, update the glossary too.

**Default mode (auto-accept):**

Apply all updates immediately. After each write:

- Validate against the artifact contract:
  - **Blocking:** YAML parseable, required fields present, id matches filename, valid enums, freshness_note not empty, Key Facts present (except Glossary).
  - **Warning:** relates_to targets exist, source refs resolve, body sections present, Related matches frontmatter.
- Frontmatter field order, determinism rules, and body structure must follow the artifact contract.
- **Lint immediately after writing:**
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
  ```
  Filter to errors for this artifact's ID. Fix any errors before moving on.
- Run snapshot:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
  ```

**Review mode (`--review`):**

Present the proposed changes to the user before each write. Wait for the user to accept or skip.

- **On accept:** Write, lint, snapshot (same as auto-accept).
- **On skip:** Leave the artifact unchanged. Move to the next one.

### 8. Post-update commands

After all artifacts have been processed, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Update pass: refreshed N artifacts, added M new, marked K orphaned" --reef <reef-root>
```

Replace `N`, `M`, `K` with actual counts.

Present a full summary:

```
Update complete.

Refreshed: 3 artifacts
  SYS-INGEST — 2 Key Facts updated, 1 added
  SCH-INGEST-ORDER — freshness_note refreshed
  PROC-INGEST-ORDER-LIFECYCLE — 1 Key Fact removed (source deleted)

New: 2 artifacts created
  SCH-ORDERS-FULFILLMENT — new entity discovered
  API-PAYMENTS-WEBHOOKS — new API group (6 endpoints)

Orphaned: 1 artifact marked
  SCH-ORDERS-LEGACY-CART — model class removed from source

Unchanged: 12 artifacts (sources not affected)
```

### 9. No changes detected

If the diff command reports no source changes after re-indexing, **still run Steps 6a and 6b** — structural changes (new/removed entities) can exist even when individual file hashes haven't changed (e.g., a new file was added but no existing files were modified).

If neither diff nor structural detection finds anything:

> "All sources unchanged since last update. API specs and ERDs have been refreshed from current code. Your reef is fresh."

Source re-extraction (Step 2) always runs regardless of the diff result — the code may have changed even if the indexed file set hasn't. The diff in Step 4 only determines whether artifacts need content updates.

---

### 10. Handling renames

If the user asks to rename a service (e.g., "we renamed Orders to Fulfillment"), this cascades across the reef:

1. **Identify all affected files.** Search for the old name in:
   - Artifact filenames (e.g., `SYS-ORDERS.md` → `SYS-FULFILLMENT.md`)
   - Artifact `id` fields in frontmatter
   - `relates_to` entries in other artifacts
   - `[[wikilinks]]` in body text
   - `.reef/project.json` services array
   - `.reef/questions.json`
   - `sources/apis/` and `sources/schemas/` directory names

2. **Present the full list of changes** to the user before making any edits. Example:
   ```
   Renaming "orders" → "fulfillment" affects:
     - 3 artifact files to rename (SYS-ORDERS, SCH-ORDERS-CORE, API-ORDERS-REST)
     - 3 artifact IDs to update in frontmatter
     - 7 relates_to references across other artifacts
     - 4 wikilinks in body text
     - 1 service entry in project.json
     - 2 source directories (apis/orders/, schemas/orders/)
   ```

3. **On confirmation**, apply all changes atomically:
   - Rename files
   - Update IDs, relates_to, wikilinks, project.json
   - Rename source directories
   - Run rebuild-index, rebuild-map
   - Log the rename

4. **Run snapshot** on every modified artifact.
