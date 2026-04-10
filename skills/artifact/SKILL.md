---
description: "Create or update a single artifact"
---

# /reef:artifact

Create or update a single artifact with full contract enforcement.

## Setup

Read these references before doing anything else:

- `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Determine mode

**Create mode** — the user names a topic or type and no matching artifact exists:

1. Determine the artifact type from context (system, schema, api, process, decision, glossary, connection, risk).
2. Generate the artifact ID following the conventions below.
3. Read the matching template from `/Users/jessi/Projects/seaof-ai/reef/references/templates/`.
4. Proceed to evidence gathering.

**Update mode** — the user names an existing artifact:

1. Read the artifact file.
2. Identify what needs changing.
3. Preserve all unaffected content.
4. Plan to bump `last_verified` in frontmatter.
5. Proceed to evidence gathering.

### 3. Gather evidence

- Read relevant source files referenced by or related to the artifact.
- Check edges: read `relates_to` targets to understand connections.
- Trace claims back to sources. Every Key Fact needs a source citation.

### 4. Write the artifact

Follow the artifact contract exactly.

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

### 5. Validate before writing

**Blocking checks** (must all pass or the artifact is not written):

- YAML frontmatter is parseable.
- All required fields are present.
- `id` matches the filename (lowercase of ID + `.md`).
- All enum fields use valid values.
- `freshness_note` is not empty.
- Key Facts section is present (except for Glossary type).

**Warning checks** (report but do not block):

- All `relates_to` targets resolve to existing artifact files.
- All `sources` refs resolve to files on disk.
- All required body sections for the type are present.
- `## Related` wikilinks match `relates_to` frontmatter entries.

Report any warnings to the user after writing.

### 6. Post-write commands

Run these in order after the artifact file is written and accepted:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in the log message when in update mode.

## Artifact ID Conventions

**Prefix by type:**

| Type | Prefix |
|---|---|
| system | SYS- |
| schema | SCH- |
| api | API- |
| process | PROC- |
| decision | DEC- |
| glossary | GLOSSARY- |
| connection | CON- |
| risk | RISK- |

**Format:** Uppercase, hyphen-separated. Examples: `SYS-INGEST`, `SCH-INGEST-ORDER`, `CON-INGEST-PIPELINE-FEED`.

**Filename:** Lowercase of the ID with `.md` extension. Example: `SYS-INGEST` becomes `sys-ingest.md`.

**Directory:** Write the file to the correct subdirectory under `artifacts/`:

| Type | Directory |
|---|---|
| system | artifacts/systems/ |
| schema | artifacts/schemas/ |
| api | artifacts/apis/ |
| process | artifacts/processes/ |
| decision | artifacts/decisions/ |
| glossary | artifacts/glossary/ |
| connection | artifacts/connections/ |
| risk | artifacts/risks/ |
