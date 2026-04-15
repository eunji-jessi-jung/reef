---
description: "Scan for new context files and connect them to the reef"
---

# /reef:feed

Detect new or changed context files in `sources/context/` and `sources/raw/`, then help the user connect them to existing artifacts.

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Index context files

Run the indexer:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index-context --reef {reef_root}
```

This scans `sources/context/` and `sources/raw/`, compares against the previous `.reef/context-index.json`, and returns:

- `new` — files added since last index
- `changed` — files with different content since last index
- `removed` — files that were in the previous index but are now gone
- `unreferenced` — files not referenced by any artifact's `sources` field

### 3. Report

**If nothing new, changed, or unreferenced:** Say so and stop.

```
Nothing new. All N context files are indexed and referenced.
```

**If there are results**, present a compact summary:

```
Context scan:
  Total:         N files indexed
  New:           X files
  Changed:       Y files
  Unreferenced:  Z files (not linked to any artifact)
```

Then list each new, changed, or unreferenced file with its path.

### 4. Connect new context to artifacts

For each new or changed file that is readable (`.md`, `.txt`, `.csv` — skip binaries):

1. Read the file content.
2. Read `${reef_root}/index.md` to see all existing artifacts.
3. Identify which artifacts this context is most relevant to — match by topic, entities mentioned, domain overlap. Consider:
   - Does it answer any `known_unknowns` in existing artifacts?
   - Does it describe requirements, decisions, or processes for a documented entity?
   - Does it introduce something not yet covered by any artifact?
4. Present findings per file:

```
sources/context/requirements/order-srd.md
  Relevant to: SCH-ORDERS-CORE, PROC-ORDERS-FULFILLMENT
  Answers known unknown in SCH-ORDERS-CORE: "What triggers order expiration?"
  New topic not yet covered: order escalation workflow
```

### 5. Ask the user

After presenting findings, ask:

```
Want me to update the relevant artifacts to reference these files?
If any file introduces a new topic, I can create a draft artifact for it via /reef:artifact.
```

**If the user approves updates:**
- Add the context file path to each relevant artifact's `sources` frontmatter field.
- Update the artifact's `freshness_note` to mention the new context.
- Do NOT rewrite artifact content — just add the source reference. The user can run `/reef:scuba` or `/reef:deep` to fold the content in.

**If the user wants a new artifact:**
- Tell them to run `/reef:artifact` with the topic. Do not create artifacts directly from this skill.

### 6. Log

Append to the evolution log:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "feed: indexed N context files, X new, Y changed, Z unreferenced" --reef {reef_root}
```
