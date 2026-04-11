---
description: "Re-index sources and update stale artifacts"
---

# /reef:update

Re-index all sources, detect what changed, and update affected artifacts. This is the "fix staleness" skill. `/reef:health` reports; `/reef:update` fixes.

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

### 5. Classify each changed file

| Classification | Meaning | Action |
|---|---|---|
| new | File appeared that was not previously indexed | Flag artifacts in the same module for potential new content |
| updated | Content hash changed since last snapshot | Flag artifacts that reference this file |
| renamed | Path changed but content is similar | Update `sources` refs in affected artifacts |
| deleted | File removed from disk | Warn that referencing artifacts may be invalid |
| unchanged | No movement | Skip |

### 6. Update each affected artifact

Process artifacts one at a time. For each affected artifact:

1. Read the current artifact file.
2. Re-read the changed source files it references.
3. Compare current Key Facts against source content.
4. Propose specific updates:
   - Changed Key Facts (quote the old and new).
   - New information found in sources.
   - Claims that no longer hold (source content removed or contradicted).
   - Updated `freshness_note` and `last_verified`.
5. **Glossary cross-check.** Before finalizing the update, compare the artifact's terms against GLOSSARY- artifacts. If any Key Fact or description uses a domain term inconsistently with the glossary, fix it. If the source code reveals the glossary definition is outdated, update the glossary too.
6. Present the proposed changes to the user.
7. Wait for the user to accept or skip this artifact.

**On accept:**

- Write the updated artifact, applying the same validation as `/reef:artifact`:
  - **Blocking:** YAML parseable, required fields present, id matches filename, valid enums, freshness_note not empty, Key Facts present (except Glossary).
  - **Warning:** relates_to targets exist, source refs resolve, body sections present, Related matches frontmatter.
- Frontmatter field order, determinism rules, and body structure must follow the artifact contract.
- Run snapshot:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
  ```

**On skip:**

- Leave the artifact unchanged. Move to the next one.

### 7. Post-update commands

After all artifacts have been processed (accepted or skipped), run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Update pass: refreshed N artifacts" --reef <reef-root>
```

Replace `N` with the count of artifacts that were actually updated (accepted, not skipped).

Present a summary of what changed:

```
Update complete. Refreshed 3 of 5 affected artifacts.
  SYS-INGEST — 2 Key Facts updated, 1 added
  SCH-INGEST-ORDER — freshness_note refreshed
  PROC-INGEST-ORDER-LIFECYCLE — 1 Key Fact removed (source deleted)
Skipped: API-INGEST-REST, CON-INGEST-PIPELINE-FEED
```

### 8. No changes detected

If the diff command reports no source changes after re-indexing, respond:

> "All sources unchanged since last update. API specs and ERDs have been refreshed from current code. Your reef is fresh."

Source re-extraction (Step 2) always runs regardless of the diff result — the code may have changed even if the indexed file set hasn't. The diff in Step 4 only determines whether artifacts need content updates.

---

### 9. Handling renames

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
