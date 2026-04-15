---
description: "Extract full API specs and ERDs from source repos using a tiered protocol"
---

# reef:source

Extract complete API specifications and entity-relationship diagrams from source codebases. Uses a tiered protocol — try the fastest reliable method first, fall back gracefully. Caches successful recipes for repeat runs.

This skill runs **in parallel with snorkel** after init:

```
         ┌→ snorkel (structural artifacts)
init → ──┤                                  → scuba → deep
         └→ source  (API specs + ERDs)
```

Snorkel writes to `artifacts/`. Source writes to `sources/apis/` and `sources/schemas/`. No file conflicts. Scuba uses both.

---

## Output Structure

Source extraction writes to a service-grouped directory structure, using the service mappings from `.reef/project.json`:

```
sources/
  apis/
    {service}/
      {sub}/                    # sub-application (if applicable)
        openapi.json            # always OpenAPI 3.x JSON, regardless of extraction tier
        openapi.meta.json       # extraction metadata (tier, method, source path, timestamp)
  schemas/
    {service}/
      {sub}/
        schema.md               # Mermaid ERD + field tables
  infra/
    {service}/
      storage.md                # cloud storage path patterns and bucket layout (if detected)
      runtime.md                # Docker/K8s topology and env vars (if detected)
      queues.md                 # message queue topics and task definitions (if detected)
```

**Examples with service groupings:**
```
sources/
  apis/
    payments/
      gateway/openapi.json       # tier 2: runtime extracted
      ledger/openapi.json        # tier 2: runtime extracted
      admin/openapi.json         # tier 2: runtime extracted
    orders/
      openapi.json               # tier 2: runtime extracted (single-app repo)
    platform/
      auth/openapi.json          # tier 2: runtime extracted (swag)
      analytics/openapi.json     # tier 2: runtime extracted
    pipeline/
      gateway/openapi.json       # tier 2: runtime extracted
  schemas/
    payments/
      gateway/schema.md
      ledger/schema.md
    orders/
      schema.md
    platform/
      auth/schema.md
```

**Naming rules:**
- Service names from `project.json` `services[].name`, lowercased.
- Sub-application names from the repo structure (e.g., `applications/gateway/` → `gateway`). If the repo is a single app, no sub-directory.
- API specs are always `openapi.json` — never `.md`, never `.yaml`.
- ERDs are always `schema.md`.
- Each spec gets a companion `openapi.meta.json` recording provenance.

**Meta file format:**
```json
{
  "service": "payments",
  "sub": "gateway",
  "source_repo": "payments-backend",
  "extraction_tier": 2,
  "extraction_method": "fastapi runtime (poetry)",
  "source_path": "applications/gateway/src/app/main.py",
  "extracted_at": "2026-04-11T10:35:00Z"
}
```

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for source paths and **service groupings**. The `services` array maps repos to services — use this to determine output directory structure.
3. **Read `.reef/source-recipes.json`** if it exists — cached extraction recipes from previous runs.

### Resume detection

After loading context, scan `sources/apis/` and `sources/schemas/` for already-extracted specs:

- List all `openapi.json` files in `sources/apis/`
- List all `schema.md` files in `sources/schemas/`
- Compare against the services and sub-apps configured in `project.json`

If extractions already exist:

```
Found existing extractions:
  API specs: N (services: {list})
  Schemas:   N (services: {list})
  Missing:   {list of services/subs with no extraction}

Options:
  1. Continue — extract only what's missing
  2. Re-extract all — overwrite existing specs (useful if source code changed)
  3. Exit — extractions look complete
```

If continuing, skip services that already have both `openapi.json` and `schema.md`. If re-extracting, proceed as normal but overwrite existing files.

---

## Step 1 — Detect tech stacks

For each source repo, scan dependency files to identify API frameworks, ORMs, and package managers.

**Read `references/tech-stack-signals.md`** for the full detection tables (dependency files, framework indicators, ORM indicators, package manager signals).

Report what was detected:

```
Tech stacks detected:

| Service  | Repo / App              | API Framework | ORM/ODM      | DB         | Pkg Mgr |
|----------|-------------------------|---------------|--------------|------------|---------|
| Payments | pay-backend/gateway     | FastAPI       | SQLAlchemy   | PostgreSQL | poetry  |
| Payments | pay-backend/ledger      | FastAPI       | SQLAlchemy   | PostgreSQL | poetry  |
| Orders   | order-service           | FastAPI       | Beanie       | MongoDB    | poetry  |
| Platform | platform-auth-api       | Go (swag)     | SQL migrations | PostgreSQL | —     |
| Pipeline | pipeline-gateway        | FastAPI       | —            | —          | uv      |
```

---

## Step 1.5 — Scaffold output directories and pre-flight checks

**Scaffold first.** Before any extraction, create the full directory structure for every service/app detected in Step 1:

```bash
# For each service/app:
mkdir -p <reef-root>/sources/apis/{service}/{sub}
mkdir -p <reef-root>/sources/schemas/{service}/{sub}
mkdir -p <reef-root>/sources/infra/{service}
```

For single-app repos (no sub-applications), omit the sub-directory.

**Pre-flight checks.** Read `references/preflight-checks.md` and follow the 6-step protocol: check venv health, check tool availability, prompt for missing tools, early skip decision, fix broken venvs, determine run command.

Report the pre-flight results:

```
Pre-flight checks:

| Service  | App              | Venv    | Pkg Mgr         | Runtime possible? |
|----------|------------------|---------|-----------------|-------------------|
| Payments | gateway          | broken  | poetry          | yes (poetry install) |
| Payments | ledger           | broken  | poetry          | yes (poetry install) |
| Orders   | —                | healthy | poetry          | yes               |
| Platform | auth             | n/a     | go+swag         | yes               |
| Platform | analytics        | n/a     | n/a (fork)      | no — skip to t3   |
```

---

## Step 2 — Extract API specs (tiered)

For each repo/app where an API framework was detected, follow the tiers in order. Stop at the first success.

**All tiers must produce `openapi.json`** — valid OpenAPI 3.x JSON format. No markdown, no YAML. If the source is YAML or Swagger 2.x, convert to OpenAPI 3.x JSON.

**Design principle: live truth over speed.** A stale spec that gets one endpoint wrong destroys trust with engineers. Runtime extraction from today's code is always preferred over copying a file that may have been generated months ago.

### Tier 0 — User-provided spec

Check if the user has already placed a file at `sources/apis/{service}/{sub}/openapi.json`. If it exists and was NOT written by a previous extraction run (check `openapi.meta.json` — if missing or `extraction_method` is `"user-provided"`), treat it as authoritative. The user knows their system better than any extraction tool.

Write or update `openapi.meta.json` with `"extraction_tier": 0, "extraction_method": "user-provided"`.

Report: "Using user-provided spec for platform/auth."

**Move to the next repo/app.** Do not attempt further tiers.

### Tier 1 — Cached recipe replay

If `.reef/source-recipes.json` has a recipe for this repo/app, try it first. Cached recipes always store runtime extraction commands (never file copies), so replaying them produces a fresh spec from current code.

1. Read the cached recipe (app path, env stubs, dep stubs, command).
2. Re-create any dependency stubs in a temp directory.
3. Run the cached command.
4. If it succeeds, save the output as `openapi.json` and move on.
5. If it fails, discard the recipe and fall through to Tier 2.

Report: "Replaying cached recipe for orders..."

### Tier 2 — Runtime extraction (max 5 attempts)

**Read `references/runtime-extraction-protocol.md`** for the full protocol: generation script detection, per-framework extraction commands (FastAPI, Django, Go, NestJS), the 8-step attempt protocol (pre-read config, build PYTHONPATH, handle errors), and stub creation references.

Key principles:
- Check for existing generation scripts first (most reliable path)
- Pre-read config/settings to discover ALL env vars before first attempt
- Always use the package manager's run command — never bare `python3`
- Max 5 attempts, then fall through to Tier 3

### Tier 3 — Existing spec with staleness warning (fallback)

If runtime extraction fails (environment too complex, requires running database, C extensions, etc.), check for existing spec files as a last resort.

Search for existing API specs in these locations:
- Repo root: `openapi.json`, `openapi.yaml`, `swagger.json`, `swagger.yaml`
- Common subdirs: `docs/`, `static/`, `spec/`, `api/`, `scripts/`
- Build output: `build/`, `dist/`, `target/`
- Per-app directories in multi-app repos

If found:
- **JSON OpenAPI 3.x**: Copy directly.
- **YAML**: Convert to JSON using Python (`yaml.safe_load` → `json.dump`).
- **Swagger 2.x**: Copy as-is (still valid for reference; note in meta as `swagger_2`).

**Staleness check:** Compare the spec file's `git log -1 --format=%ci <spec-file>` date against the most recent commit touching route/controller files. If the spec is older, add a warning to the meta file:

```json
{
  "extraction_tier": 3,
  "extraction_method": "existing spec (static file)",
  "staleness_warning": "Spec file last modified 2025-11-03. Route files modified as recently as 2026-04-09. Spec may be outdated.",
  "route_files_last_modified": "2026-04-09"
}
```

Report with the warning: "Copied existing spec for payments/gateway — but the spec file is 5 months older than the latest route changes. Endpoints may be missing or outdated."

**If no existing spec found either**, fall through to Tier 4.

### Tier 4 — Structured code reading (last resort)

If both runtime extraction and existing specs fail, read the code directly. This produces a spec from today's code (so it's current), but may be incomplete — computed routes, dynamic registrations, or inherited endpoints could be missing.

1. **Find all route/controller files** using the framework signal from Step 1.
2. **Read every route file.** Extract: HTTP method, path, handler name, request/response types if annotated, auth guards/middleware, tags/groups.
3. **Write a valid OpenAPI 3.0 JSON file** to `sources/apis/{service}/{sub}/openapi.json`:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Order Service API",
    "version": "extracted",
    "description": "Extracted by reading source code directly (tier 4). May be incomplete — computed routes, dynamic registrations, or inherited endpoints could be missing."
  },
  "paths": {
    "/projects": {
      "get": {
        "summary": "List projects",
        "tags": ["Projects"],
        "security": [{"bearerAuth": []}]
      },
      "post": {
        "summary": "Create project",
        "tags": ["Projects"],
        "security": [{"bearerAuth": []}]
      }
    }
  },
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    }
  }
}
```

Include ALL endpoints. Group by tags. Note auth requirements. The output must be valid JSON parseable as OpenAPI.

Write `openapi.meta.json` with `"extraction_tier": 4`.

Report: "Runtime extraction failed for order-service (missing MongoDB connection at import time). Fell back to code reading — 47 endpoints extracted, saved as OpenAPI JSON."

---

## Step 3 — Extract ERDs (tiered)

For each repo/app where an ORM/ODM was detected, follow the tiers in order.

### Tier 0 — User-provided schema

Same as API tier 0. If `sources/schemas/{service}/{sub}/schema.md` exists and was placed by the user (no meta file or meta says `"user-provided"`), treat it as authoritative.

### Tier 1 — Cached recipe replay

Same as API tier 1. If a cached ERD recipe exists, replay it.

### Tier 2 — Runtime extraction (max 5 attempts)

Use the repo's package manager (detected in Step 1) for all Python commands.

**SQLAlchemy:**
```bash
poetry run python3 -c "
from sqlalchemy import inspect, create_engine
from <app>.models import Base
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
inspector = inspect(engine)
# Dump table names, columns, foreign keys as JSON
"
```

**Django:**
```bash
poetry run python3 manage.py inspectdb
```

**Alembic:** Read the latest or consolidated migration file. It contains the ground-truth schema as `op.create_table(...)` calls. These are runtime-derived (generated by Alembic from the live models), so they are reliable ground truth.

Same 5-attempt protocol as API extraction. Same stub/env patterns. Same package manager requirement — never use bare `python3`.

### Tier 3 — Existing schema with staleness warning

Search for existing schema files as a fallback:
- Prisma: `prisma/schema.prisma` (convert to Mermaid ERD)
- Existing ERDs: `docs/erd.md`, `docs/schema.md`, `docs/database.md`
- SQL dumps: `schema.sql`, `db/schema.sql`

Apply the same staleness check as API tier 3 — compare file date against latest model file changes.

**Beanie/Mongoose:** Read the document class definitions (these are typically self-describing — fields, validators, indexes are all in the class). This is effectively code reading but the model files ARE the schema, so it is reliable. Treat as tier 3.

Save to `<reef-root>/sources/schemas/{service}/{sub}/schema.md`.

### Tier 4 — Direct code reading (last resort)

1. **Find all model/entity files** using ORM signals.
2. **Read every model file.** Extract: class/struct names, field names, field types, primary keys, foreign keys, relationships, indexes.
3. **Write a schema file** to `sources/schemas/{service}/{sub}/schema.md`:

```markdown
# Schema — {service} {sub}

> Extracted by reading model source code directly (tier 4). Computed fields, dynamic relationships, or migration-only columns may be missing.

## Tables

### {table_name}
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| created_at | DateTime(tz) | auto |

## Relationships

\`\`\`mermaid
erDiagram
    orders ||--o{ order_items : "contains"
    orders }o--|| customers : "belongs to"
\`\`\`
```

Include ALL tables/collections and ALL fields. Mark PK and FK. Show relationship cardinality in the Mermaid diagram.

---

## Step 3.5 — Extract infrastructure patterns

**Read `${CLAUDE_PLUGIN_ROOT}/references/infra-extraction.md`** for the full protocol: detection signals, output file templates (storage.md, runtime.md, queues.md), skip conditions, and report format.

Also read `references/tech-stack-signals.md` — the Infrastructure / Storage Indicators section — for dependency-level detection signals.

Output to `sources/infra/{service}/`. If no infrastructure signals are found for a service, skip it. Do not create empty files.

---

## Step 4 — Cache successful recipes

After all repos are processed, write `.reef/source-recipes.json`:

```json
{
  "version": 1,
  "recipes": {
    "{service}/{sub}": {
      "api": { "tier": 2, "method": "...", "command": "...", "app_path": "...", "env_stubs": {}, "dep_stubs": [], "output": "...", "last_success": "ISO date" },
      "erd": { "tier": 2, "method": "...", "source_path": "...", "output": "...", "last_success": "ISO date" }
    }
  }
}
```

- Recipe keys use the service/sub path, not repo names.
- **Only cache runtime extraction recipes** (tier 2). Never cache tier 3 — those would replay a stale copy forever.
- Set `null` for repos with no API or no data layer.

---

## Step 5 — Log and report

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Source extraction: N API specs, M ERDs, K infra patterns extracted" --reef <reef-root>
```

**Do not run `reef.py index` or `rebuild-index` or `rebuild-map` here.** Source only writes to `sources/` and `.reef/source-recipes.json` — it does not create artifacts. Re-indexing is handled by snorkel (if running in parallel) or by the next skill that runs (scuba, update, etc.). This avoids race conditions with snorkel's reef.py calls.

Report what was generated, split into two sections — live truth and gaps:

```
Source extraction complete.

Live truth (runtime-extracted from today's code):

| Service  | App              | API          | ERD              |
|----------|------------------|--------------|------------------|
| Payments | gateway          | 70 endpoints | 30 tables        |
| Payments | ledger           | 63 endpoints | 28 tables        |
| Payments | admin            | 10 endpoints | 4 tables         |
| Orders   | —                | 87 endpoints | 7 collections    |
| Pipeline | gateway          | 6 endpoints  | —                |

Not live truth (may be outdated):

| Service  | App           | API                              | ERD              | Why                        |
|----------|---------------|----------------------------------|------------------|----------------------------|
| Platform | auth          | 66 endpoints (8 months stale)    | 16 tables (migr) | Go — no swag on machine    |
| Platform | analytics     | 28 endpoints (unknown freshness) | —                | Fork of OSS project        |

Recipes cached to .reef/source-recipes.json for future runs.
```

**For specs that are not live truth**, tell the user they can provide their own:

```
Two specs could not be runtime-extracted and may be outdated.
You can replace them with up-to-date versions:

  sources/apis/platform/auth/openapi.json      — place a valid OpenAPI 3.x JSON file here
  sources/apis/platform/analytics/openapi.json — place a valid OpenAPI 3.x JSON file here

The directory structure is already in place. Drop in your files and
run /reef:source again — it will detect them as user-provided (tier 0)
and skip extraction for those.
```

Then suggest next step:

"API specs and ERDs are now in `sources/apis/` and `sources/schemas/`.

- `/reef:scuba` — deepen the draft artifacts using these specs."

---

## Repeat Runs

When `/reef:source` is run again (e.g., after code changes or via `/reef:update`):

1. Load `.reef/source-recipes.json`.
2. For each repo with a cached recipe, try the cached recipe first (Tier 1). Since only runtime recipes are cached, replaying always produces fresh output from current code.
3. If the cached recipe fails (dependency changed, new env var, etc.), fall through to Tier 2 (fresh runtime extraction).
4. Update the recipe cache with any new successes.

This means first runs are slow (discovery + stubbing), but repeat runs are fast (replay cached runtime commands). Every run produces live-truth specs — never stale copies.

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration.
- No emojis. No exclamation marks.
- Report each tier attempted and its outcome. Be transparent about fallbacks.
- When runtime extraction fails, explain why in one sentence. Do not dump full tracebacks unless the user asks.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No sources**: "No sources configured. Run `/reef:init` to add source paths."
- **No service groupings in project.json**: Fall back to using repo names as service names. Warn that output structure would be better with service groupings from `/reef:init`.
- **No API framework or ORM detected in any repo**: "No API frameworks or data models detected in any source repo. If your services have APIs, you can manually add specs to `sources/apis/`."
- **All tiers fail for a repo**: Report what was tried and why it failed. Move on to the next repo. Partial success is normal.
- **Temp directory cleanup**: Always clean up stub directories, even on failure. Use try/finally.
- **Source repo not found at path**: Warn, skip, continue.
- **YAML conversion fails**: Try Python yaml first, fall back to json module if the YAML is simple enough. Report if conversion fails.

---

## Key Rules

- **Never modify source repos.** Stubs go in temp directories. Output goes in the reef's `sources/`.
- **API specs are always `openapi.json`.** Valid OpenAPI 3.x JSON format, regardless of extraction tier.
- **Use service groupings for directory structure.** Map repos to services using `project.json`.
- **Scaffold directories before extraction.** Create all output directories upfront so users know where to place manual specs even if extraction fails.
- **No hard dependencies.** The skill should work with whatever tools are on the machine. If `uv` is missing, try `poetry`. If `poetry` is missing, try bare `python3`. If `go` is missing, skip to tier 3. Never fail because a tool isn't installed — degrade gracefully and tell the user what would help.
- **Fail fast on broken environments.** Check venv health and tool availability before attempting extraction. Do not burn 5 attempts when the first one is guaranteed to fail.
- **5 attempts max for runtime extraction.** Be smarter about stubbing (read the error, stub specifically), but do not enter an endless debugging spiral. Fall back gracefully.
- **User-provided specs are tier 0.** If the user places a file in the right location, trust it unconditionally. They know their system.
- **Cache what works.** Repeat runs should be fast. Only cache runtime recipes — never static file copies.
- **Transparency over silence.** Split the report into "live truth" and "not live truth". If a spec is stale, say so explicitly and tell the user where to place an updated version.
- **Completeness matters.** List ALL endpoints, ALL tables, ALL fields. This is reference material for scuba and deep.
- **Write meta files.** Every `openapi.json` gets an `openapi.meta.json` so downstream consumers know the provenance.
