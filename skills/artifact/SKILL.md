---
description: "Create or update a single artifact"
---

# /reef:artifact

Create or update a single artifact with full contract enforcement.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Determine mode

**Create mode** — the user names a topic or type and no matching artifact exists:

1. Determine the artifact type from context (system, schema, api, process, decision, glossary, connection, risk).
2. Generate the artifact ID following the conventions below.
3. Read the matching template from `${CLAUDE_PLUGIN_ROOT}/references/templates/`.
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

**Read `references/artifact-contract.md`** for frontmatter field order, body requirements, determinism rules, and validation checks. All rules apply.

### 5. Glossary cross-check

Before writing, cross-check the artifact against any existing GLOSSARY- artifacts in the reef:

1. Read all GLOSSARY- artifacts in `artifacts/glossary/`.
2. Scan the artifact's Key Facts, Overview, and Core Concepts for domain terms that appear in the glossary.
3. If any term is used with a meaning that contradicts or drifts from the glossary definition, **fix the artifact text** to align with the glossary — or, if the artifact's usage is more accurate, update the glossary entry instead.
4. If any glossary-defined term is used ambiguously (e.g., "Order" without specifying Payments or Fulfillment when the glossary flags it as ambiguous), add the disambiguation.

This step prevents subtle hallucination where artifacts drift from established definitions over successive updates. Skip this step only if no GLOSSARY- artifact exists yet.

### 6. Validate before writing

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

### 7. Post-write commands

Run these in order after the artifact file is written and accepted:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
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
