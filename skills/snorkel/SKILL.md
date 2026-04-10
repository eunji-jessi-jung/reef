---
description: "Auto-discover 3-6 draft artifacts from source code"
---

# reef-snorkel

Auto-discovery surface pass — rapidly generate 3-6 draft artifacts from source code with no questions asked.

This is the "instant value" skill. The user gets structured knowledge within minutes. Snorkel reads directory structures, READMEs, and key files (routers, models, config), then produces draft artifacts that map the landscape. Depth comes later from `/reef:scuba` and `/reef:deep`.

---

## Context Loading

Before doing anything else, load context in this order:

1. **Find the reef root.** Look for a `.reef/` directory in the current working directory, then walk up parent directories. If no reef is found, stop and say: "No reef found in this directory. Run `/reef:init` first to set one up."
2. **Read `.reef/project.json`** for project name and source paths. If the `sources` array is empty or missing, stop and say: "This reef has no sources configured. Run `/reef:init` to add source paths."
3. **Read `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`** — always. This is the rulebook. Every artifact you write must conform to this contract exactly.
4. **Read `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`** — for voice and personality guidance.
5. **Read existing artifacts** (scan `artifacts/` subdirectories) to avoid generating duplicates. If an artifact already exists for a system or schema you discover, skip it.

---

## Step 1 — Refresh the source index

Report: "Refreshing the source index..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

Parse the JSON output. Report results in natural language: number of files indexed per source, total count. If indexing fails for a source, report which path failed and continue with the others.

---

## Step 2 — Structural scan

For each source in `project.json`:

1. Read the 2-level directory tree using `ls` or Glob. Do not recurse deeply — snorkel is fast.
2. Read `README.md` if present.
3. Identify and note:
   - **Entry points**: `main.py`, `app.py`, `index.ts`, `manage.py`, or equivalent
   - **Routers/handlers**: directories like `routers/`, `routes/`, `handlers/`, `views/`, `controllers/`
   - **Models/schemas**: directories like `models/`, `schemas/`, `entities/`, files like `schema.py`, `models.py`
   - **Config files**: `pyproject.toml`, `package.json`, `docker-compose.yml`, `Dockerfile`, `.env.example`, settings files
   - **Test directories**: `tests/`, `test/`, `__tests__/`
   - **API definitions**: OpenAPI specs, GraphQL schemas, protobuf files
4. Note the tech stack: FastAPI, Django, Express, Next.js, etc.
5. **Cross-system boundaries**: if code imports from or calls another source/service, flag the boundary immediately. Note the caller, the target, and the mechanism (HTTP, gRPC, message queue, shared DB, import).

Report what you find for each source as you go: "Reading the service-a source structure...", "Found a FastAPI application with 12 router modules...", "Noticing a boundary between service-a and service-b via HTTP client in `clients/service_b.py`..."

---

## Step 3 — Generate artifacts

Generate 3-6 artifacts in this priority order. Stop after 6 — snorkel is a surface pass.

### Priority order

1. **SYS-** (system): one per source/service. This is the entry point artifact for each codebase. Always generate these first.
2. **SCH-** (schema): one per major data model found (database models, Pydantic schemas, TypeScript interfaces that represent core domain entities).
3. **API-** (api): one per API surface found (REST routers, GraphQL resolvers, gRPC services).
4. **GLOSSARY-** (glossary): if domain-specific terms are emerging that need definition.
5. **CON-** (contract): if multiple sources exist and cross-system boundaries were detected. Describes the interface between two systems.

### For each artifact

**a. Determine the template.** Read the appropriate template from `/Users/jessi/Projects/seaof-ai/reef/references/templates/` for the artifact type.

**b. Generate valid YAML frontmatter.** Follow the artifact contract exactly — all required fields in the correct order:

```yaml
---
id: SYS-INGEST
type: system
title: "Acme Ingest Service"
domain: acme
status: "draft"
last_verified: 2026-04-10
freshness_note: "Surface scan only — entry points and directory structure reviewed"
freshness_triggers:
  - src/main.py
  - src/routers/
  - pyproject.toml
known_unknowns:
  - "Internal service communication patterns not yet traced"
  - "Database migration history not reviewed"
tags:
  - fastapi
  - python
aliases:
  - ingest
relates_to:
  - type: calls
    target: "[[SYS-LABEL]]"
sources:
  - category: code
    type: directory
    ref: src/routers/
  - category: code
    type: file
    ref: src/main.py
notes: ""
---
```

Key rules for frontmatter:
- `status`: always `"draft"` for snorkel
- `last_verified`: today's date, unquoted ISO format
- `freshness_note`: honest about the scan depth — snorkel is surface-level
- `freshness_triggers`: list of key source files that would invalidate this artifact if changed
- `known_unknowns`: honest list of gaps. This is critical. Snorkel should NOT pretend to know things it does not. Be generous with unknowns.
- `relates_to`: sorted by target, each entry has `type` and `target` as `[[WIKILINK]]`
- `sources`: sorted by ref, each entry has `category`, `type`, `ref` (relative to source root, never absolute paths)

**c. Write body sections** per the artifact contract and template:

- `## Overview` — 2-4 sentence summary of what this system/schema/API is
- `## Key Facts` — each fact linked to a source file with `→` syntax:
  ```
  - Built on FastAPI with 12 router modules → src/routers/
  - Uses SQLAlchemy ORM with PostgreSQL → src/models/base.py
  - Authentication via JWT middleware → src/middleware/auth.py
  ```
- Type-specific sections as defined by the template (e.g., `## Components` for SYS-, `## Fields` for SCH-, `## Endpoints` for API-)
- `## Related` — wikilinks matching the frontmatter `relates_to`:
  ```
  - [[SYS-LABEL]] — calls via HTTP client
  - [[SCH-INGEST-ORDER]] — primary data model
  ```

**d. Write the file** to the correct subdirectory:
- SYS- artifacts → `artifacts/systems/`
- SCH- artifacts → `artifacts/schemas/`
- API- artifacts → `artifacts/apis/`
- GLOSSARY- artifacts → `artifacts/glossaries/`
- CON- artifacts → `artifacts/contracts/`

Filename is the lowercase version of the ID with `.md` extension (e.g., `SYS-INGEST` → `sys-ingest.md`, `SCH-INGEST-ORDER` → `sch-ingest-order.md`).

**e. Snapshot the artifact.** After writing each artifact, run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
```

**f. Present to the user.** Show the artifact content. One at a time — do not batch-dump all artifacts at once. The user should see each artifact appear, then the next.

---

## Step 4 — Wrap up

After all artifacts are written (3-6, then stop), run these commands:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Snorkel pass: generated N artifacts" --reef <reef-root>
```

Replace `N` with the actual count.

Summarize what was created: list the artifact IDs, their types, and a one-line description of each.

Then invite depth:

"These are surface-level drafts. Each has known unknowns listed in the frontmatter — those are the gaps snorkel could not fill from a quick scan. Two ways to go deeper:

- `/reef:scuba` — guided exploration where you direct which artifacts get deepened through Socratic questioning.
- `/reef:deep` — exhaustive line-by-line tracing of a specific area. Best when you know exactly what you want mapped."

---

## Voice and Personality

Use Curious Researcher voice throughout:

- Present-participle narration for progress: "Reading the service-a source structure...", "Found a FastAPI application with 12 router modules...", "Noticing a boundary between service-a and service-b...", "Writing the system artifact for service-a..."
- No emojis. No exclamation marks.
- Honest about uncertainty. Snorkel drafts should have substantial `known_unknowns`. When you are guessing, say so. When you see something you cannot fully trace in a surface pass, note it as an unknown rather than filling in a plausible-sounding answer.
- When reading code that calls another system, flag the boundary immediately: "This file imports an HTTP client for service-b — that is a cross-system boundary worth tracking."
- Do not narrate every file you read. Summarize at the source level, call out interesting findings.

---

## Key Rules

- **Always read the artifact contract before writing any artifact.** The contract is the law.
- **Artifact IDs**: uppercase prefix + uppercase domain/name, hyphen-separated. Examples: `SYS-INGEST`, `SCH-INGEST-ORDER`, `API-INGEST-REST`, `CON-INGEST-LABEL`.
- **Filenames**: lowercase version of the ID with `.md` extension.
- **Source refs are always relative** to the source root, never absolute paths.
- **Stop after 3-6 artifacts.** Snorkel is a surface pass. Do not try to document everything.
- **Do not over-read.** Read directory structure, README, key files (routers, models, config, entry points). Do not trace every function or read every file. That is what scuba and deep are for.
- **Cross-system contracts always-on.** When reading code that calls another system, flag the boundary. If 2+ sources exist, actively look for CON- opportunities.
- **No questions asked.** Snorkel does not prompt the user for input. It reads, generates, and reports. The user watches artifacts appear.

---

## Error Handling

- **No reef found**: "No reef found in this directory. Run `/reef:init` first to set one up."
- **No sources configured**: "This reef has no sources configured. Run `/reef:init` to add source paths."
- **Source path does not exist**: warn the user, skip that source, continue with the rest.
- **`reef.py` command fails**: report the error message from JSON output. Suggest how to fix it. Do not silently swallow errors.
- **`reef.py` not found**: check that `/Users/jessi/Projects/seaof-ai/reef/scripts/reef.py` exists. If not, tell the user: "The reef.py script is missing. The plugin may not be fully installed."
- **No interesting structures found in a source**: still generate a SYS- artifact, but note in `known_unknowns` that the structure was not recognizable and deeper investigation is needed.

---

## Important

- Always use `/Users/jessi/Projects/seaof-ai/reef` to reference the plugin's own files. Never hardcode paths to the plugin directory.
- All `reef.py` commands output JSON to stdout. Parse it. Report results in natural language. The user should never see raw JSON unless they ask for it.
- This skill is non-interactive. No questions, no pauses for input. Read, generate, report. The user invokes `/reef:snorkel` and watches the artifacts roll in.
