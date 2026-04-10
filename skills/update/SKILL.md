---
description: "Re-index sources and update stale artifacts"
---

# /reef:update

Re-index all sources, detect what changed, and update affected artifacts. This is the "fix staleness" skill. `/reef:health` reports; `/reef:update` fixes.

## Setup

Read these references before doing anything else:

- `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Find the `.reef/` directory in cwd or parents. Read `project.json` from the reef root.

### 2. Re-index sources

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

### 3. Detect changes

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py diff --reef <reef-root>
```

Present the change summary to the user:

```
Source changes since last update:
  service-a: 3 updated, 1 new, 0 deleted
  service-b: 0 changes
Affected artifacts: SYS-INGEST, SCH-INGEST-ORDER, PROC-INGEST-ORDER-LIFECYCLE
```

Build the affected list by matching changed files to artifacts that reference them in `sources`.

### 4. Classify each changed file

| Classification | Meaning | Action |
|---|---|---|
| new | File appeared that was not previously indexed | Flag artifacts in the same module for potential new content |
| updated | Content hash changed since last snapshot | Flag artifacts that reference this file |
| renamed | Path changed but content is similar | Update `sources` refs in affected artifacts |
| deleted | File removed from disk | Warn that referencing artifacts may be invalid |
| unchanged | No movement | Skip |

### 5. Update each affected artifact

Process artifacts one at a time. For each affected artifact:

1. Read the current artifact file.
2. Re-read the changed source files it references.
3. Compare current Key Facts against source content.
4. Propose specific updates:
   - Changed Key Facts (quote the old and new).
   - New information found in sources.
   - Claims that no longer hold (source content removed or contradicted).
   - Updated `freshness_note` and `last_verified`.
5. Present the proposed changes to the user.
6. Wait for the user to accept or skip this artifact.

**On accept:**

- Write the updated artifact, applying the same validation as `/reef:artifact`:
  - **Blocking:** YAML parseable, required fields present, id matches filename, valid enums, freshness_note not empty, Key Facts present (except Glossary).
  - **Warning:** relates_to targets exist, source refs resolve, body sections present, Related matches frontmatter.
- Frontmatter field order, determinism rules, and body structure must follow the artifact contract.
- Run snapshot:
  ```bash
  python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
  ```

**On skip:**

- Leave the artifact unchanged. Move to the next one.

### 6. Post-update commands

After all artifacts have been processed (accepted or skipped), run:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Update pass: refreshed N artifacts" --reef <reef-root>
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

### 7. No changes detected

If the diff command reports no source changes, respond:

> "All sources unchanged since last update. Your reef is fresh."

Do not run any further steps.
