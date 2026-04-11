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
```

**Examples with service groupings:**
```
sources/
  apis/
    cdm/
      breast/openapi.json       # tier 1: copied existing spec
      chest/openapi.json        # tier 1: copied existing spec
      manufacturer/openapi.json # tier 1: copied existing spec
      inference-result/openapi.json  # tier 3: runtime extracted
    ctl/
      openapi.json              # tier 3: runtime extracted (single-app repo)
    daip/
      authz/openapi.json        # tier 1: copied existing swagger.json
      data-lineage/openapi.json # tier 1: converted from openapi.yml
    rdp/
      prefect-gateway/openapi.json  # tier 3: runtime extracted
  schemas/
    cdm/
      breast/schema.md
      chest/schema.md
    ctl/
      schema.md
    daip/
      authz/schema.md
```

**Naming rules:**
- Service names from `project.json` `services[].name`, lowercased.
- Sub-application names from the repo structure (e.g., `applications/breast/` → `breast`). If the repo is a single app, no sub-directory.
- API specs are always `openapi.json` — never `.md`, never `.yaml`.
- ERDs are always `schema.md`.
- Each spec gets a companion `openapi.meta.json` recording provenance.

**Meta file format:**
```json
{
  "service": "cdm",
  "sub": "breast",
  "source_repo": "csg-case-curator-backend",
  "extraction_tier": 1,
  "extraction_method": "existing openapi.json",
  "source_path": "applications/breast/openapi.json",
  "extracted_at": "2026-04-11T10:35:00Z"
}
```

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for source paths and **service groupings**. The `services` array maps repos to services — use this to determine output directory structure.
3. **Read `.reef/source-recipes.json`** if it exists — cached extraction recipes from previous runs.

---

## Step 1 — Detect tech stacks

For each source repo, scan dependency files to identify API frameworks and ORMs:

**Dependency files to check:**
- Python: `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `setup.cfg`
- Node: `package.json`
- Go: `go.mod`
- Java/Kotlin: `build.gradle`, `pom.xml`
- Ruby: `Gemfile`
- Rust: `Cargo.toml`

**API framework indicators:**

| Framework | Signal |
|-----------|--------|
| FastAPI | `fastapi` in deps |
| Django REST Framework | `djangorestframework` in deps |
| Flask | `flask` in deps + `flask-restx` or `flask-smorest` |
| Express | `express` in deps |
| NestJS | `@nestjs/core` in deps |
| Go (gin/echo/chi) | `gin-gonic`, `echo`, `chi` in go.mod |
| Spring Boot | `spring-boot-starter-web` in deps |

**ORM / data layer indicators:**

| ORM | Signal | Where to find models |
|-----|--------|---------------------|
| SQLAlchemy | `sqlalchemy` in deps | `models/`, `db/models/`, files with `Base = declarative_base()` |
| Django ORM | `django` in deps | `models.py` files in each app |
| Prisma | `prisma/schema.prisma` file | The schema file itself |
| TypeORM | `typeorm` in deps | Files with `@Entity()` decorators |
| Sequelize | `sequelize` in deps | Files in `models/` |
| GORM | `gorm.io/gorm` in go.mod | Struct definitions with `gorm:` tags |
| Mongoose | `mongoose` in deps | Files with `new Schema()` |
| Beanie/ODMantic | `beanie` or `odmantic` in deps | Document model classes |
| Tortoise ORM | `tortoise-orm` in deps | Model classes inheriting from `Model` |
| Alembic | `alembic` in deps or `alembic/` directory | Migration files for ground-truth schema |

**Package manager detection:**

| Manager | Signal | Run command |
|---------|--------|-------------|
| Poetry | `pyproject.toml` with `[tool.poetry]` + `poetry.lock` | `poetry run python3 -c "..."` |
| uv | `uv.lock` or `pyproject.toml` with `[tool.uv]` | `uv run python3 -c "..."` |
| Pipenv | `Pipfile` + `Pipfile.lock` | `pipenv run python3 -c "..."` |
| pip/venv | `.venv/` or `venv/` directory | `. .venv/bin/activate && python3 -c "..."` |
| None | No lock file, no venv | `python3 -c "..."` (bare, least likely to work) |

**This is critical for tier 3.** Running bare `python3` will fail for most repos because dependencies are installed in the project's virtual environment, not system Python. Always use the package manager's run command.

**Multi-app repos:** Some repos contain multiple applications (e.g., an Nx monorepo with `applications/breast/`, `applications/chest/`). Detect each sub-application separately. Check for per-app dependency files and entry points. The package manager may be at the repo root (shared) or per-app.

Report what was detected:

```
Tech stacks detected:

| Service | Repo / App              | API Framework | ORM/ODM      | DB         | Pkg Mgr |
|---------|-------------------------|---------------|--------------|------------|---------|
| CDM     | cc-backend/breast       | FastAPI       | SQLAlchemy   | PostgreSQL | poetry  |
| CDM     | cc-backend/chest        | FastAPI       | SQLAlchemy   | PostgreSQL | poetry  |
| CTL     | ctl-data-server         | FastAPI       | Beanie       | MongoDB    | poetry  |
| DAIP    | aipf-authz-api          | Go (swag)     | SQL migrations | PostgreSQL | —     |
| RDP     | rdp-prefect-gateway     | FastAPI       | —            | —          | uv      |
```

---

## Step 2 — Extract API specs (tiered)

For each repo/app where an API framework was detected, follow the tiers in order. Stop at the first success.

**All tiers must produce `openapi.json`** — valid OpenAPI 3.x JSON format. No markdown, no YAML. If the source is YAML or Swagger 2.x, convert to OpenAPI 3.x JSON.

### Tier 1 — Copy existing spec

Search for existing API specs in these locations:
- Repo root: `openapi.json`, `openapi.yaml`, `swagger.json`, `swagger.yaml`
- Common subdirs: `docs/`, `static/`, `spec/`, `api/`, `scripts/`
- Build output: `build/`, `dist/`, `target/`
- Per-app directories in multi-app repos

If found:
- **JSON OpenAPI 3.x**: Copy directly.
- **YAML**: Convert to JSON using Python (`yaml.safe_load` → `json.dump`).
- **Swagger 2.x**: Copy as-is (still valid for reference; note in meta as `swagger_2`).

Save to `<reef-root>/sources/apis/{service}/{sub}/openapi.json`.
Write `openapi.meta.json` alongside it.

Report: "Found existing OpenAPI spec at `docs/openapi.json` — copying to `sources/apis/cdm/breast/openapi.json`."

**Move to the next repo/app.** Do not attempt further tiers.

### Tier 2 — Cached recipe replay

If `.reef/source-recipes.json` has a recipe for this repo/app, try it first:

1. Read the cached recipe (app path, env stubs, dep stubs).
2. Re-create any dependency stubs in a temp directory.
3. Run the cached command.
4. If it succeeds, save the output as `openapi.json` and move on.
5. If it fails, discard the recipe and fall through to Tier 3.

Report: "Replaying cached recipe for ctl-data-server..."

### Tier 3 — Runtime extraction (max 5 attempts)

This tier tries to import the application and dump its API schema at runtime.

**Step 0 — Check for an existing generation script.** Many repos include a script like `scripts/generate_api_schema.py` or `scripts/generate_openapi.py`. Search for these first:
```bash
find <repo-root> -name "generate_api*" -o -name "generate_openapi*" -o -name "openapi_gen*" | head -5
```
If found, run it using the repo's package manager (e.g., `poetry run python scripts/generate_api_schema.py`). If it succeeds and produces an OpenAPI spec, use that. This is the most reliable runtime path because the repo maintainers already solved the dependency and env var problems.

**Step 1 — Use the package manager's run command.** Always wrap Python commands with the detected package manager. Never use bare `python3` — it won't have the dependencies installed.

**FastAPI / Flask-RESTX / Flask-Smorest:**
```bash
# Poetry:
PYTHONPATH=<app-src-dir>:<stubs-dir> poetry run python3 -c "
import json
from <app_module>.main import app
print(json.dumps(app.openapi(), indent=2))
"

# uv:
PYTHONPATH=<app-src-dir>:<stubs-dir> uv run python3 -c "
import json
from <app_module>.main import app
print(json.dumps(app.openapi(), indent=2))
"
```

**Django REST Framework:**
```bash
DJANGO_SETTINGS_MODULE=<project>.settings poetry run python3 -c "
from rest_framework.schemas.openapi import SchemaGenerator
import json
generator = SchemaGenerator(title='API')
schema = generator.get_schema()
print(json.dumps(schema, indent=2))
"
```

**Go (with swag):**
```bash
swag init -g cmd/main.go -q
# Output: docs/swagger.json — copy and convert if needed
```

**NestJS / Express with swagger:**
```bash
npx ts-node -e "
const { NestFactory } = require('@nestjs/core');
const { SwaggerModule } = require('@nestjs/swagger');
// ... bootstrap and extract
"
```

**For monorepos with shared libraries** (e.g., `libraries/backend-core/src/`), add all library source directories to PYTHONPATH. Run the command from the app directory if each app has its own pyproject.toml, or from the repo root if there's a single shared one.

**Protocol for each attempt:**

1. **Find the app entry point.** Read `main.py`, `app.py`, `main.go`, `index.ts`, etc. Identify the app object and its import path.
2. **Identify the package manager and working directory.** Use the detected package manager from Step 1. For monorepos, run from the directory that contains the `pyproject.toml` / `poetry.lock`.
3. **Run the extraction command** using `poetry run` / `uv run` / `pipenv run`.
4. **If it succeeds** — save output as `openapi.json`, write meta, cache the recipe, move on.
5. **If it fails** — read the error message carefully:
   - **Missing environment variable** (e.g., `KeyError: 'DB_HOST'`): Add a dummy value (`"localhost"`, `"stub"`, `"true"`, `"[]"`, `"{}"`) and retry. For JSON-valued env vars, use the appropriate empty structure.
   - **Missing private package** (e.g., `ModuleNotFoundError: No module named 'internal_auth_client'`): Create a minimal stub package in a temp directory and add to `PYTHONPATH`. Retry.
   - **Missing sub-module of a private package** (e.g., `No module named 'internal_auth_client.api.permissions_api'`): Extend the stub with the specific sub-module structure. Create nested `__init__.py` files with stub classes.
   - **Pydantic/Settings validation error**: The app uses Pydantic Settings and a required env var is missing or has the wrong type. Read the Settings class to understand what it expects, then set all required env vars.
   - **Other import error**: Read the full traceback. Identify the root cause. If it's a fixable configuration issue (missing config file, wrong working directory), fix and retry. If it's fundamental (requires a running database connection at import time, C extension not compiled), give up.
6. **After 5 failed attempts** — report what went wrong, fall through to Tier 4.

**Stub creation pattern** (for missing private packages):
```python
# Create temp dir with: <package_name>/__init__.py
# __init__.py contains:
class _Stub:
    def __init__(self, *a, **kw): pass
    def __getattr__(self, name): return lambda *a, **kw: None
    def __call__(self, *a, **kw): return self

def __getattr__(name):
    return _Stub()
```

For packages that need specific sub-modules (common with generated API clients):
```
<stub-dir>/
  <package_name>/
    __init__.py          # module-level __getattr__ returning _Stub()
    api/
      __init__.py        # same pattern
      specific_api.py    # class SpecificApi: ...
    models/
      __init__.py
    rest.py              # class RESTResponse: status=200; data=b'{}'
    configuration.py     # class Configuration: ...
    exceptions.py        # class ApiException(Exception): pass
```

This deeper stub structure handles packages where the importing code does `from package.api.specific_api import SpecificApi` rather than just `import package`.

**Important:** Create stubs in a temp directory. Add to `PYTHONPATH` / `NODE_PATH`. Clean up after extraction. Never modify the source repo.

### Tier 4 — Structured code reading (fallback)

If all runtime extraction attempts fail, read the code directly and produce a **minimal OpenAPI 3.0 JSON spec** (not markdown):

1. **Find all route/controller files** using the framework signal from Step 1.
2. **Read every route file.** Extract: HTTP method, path, handler name, request/response types if annotated, auth guards/middleware, tags/groups.
3. **Write a valid OpenAPI 3.0 JSON file** to `sources/apis/{service}/{sub}/openapi.json`:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "CTL Data Server API",
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

Write `openapi.meta.json` with `"extraction_tier": 4` so downstream consumers know the depth.

Report: "Runtime extraction failed for ctl-data-server (missing MongoDB connection at import time). Fell back to code reading — 47 endpoints extracted, saved as OpenAPI JSON."

---

## Step 3 — Extract ERDs (tiered)

For each repo/app where an ORM/ODM was detected, follow the tiers in order.

### Tier 1 — Copy existing schema

Search for existing schema files:
- Prisma: `prisma/schema.prisma` (convert to Mermaid ERD)
- Existing ERDs: `docs/erd.md`, `docs/schema.md`, `docs/database.md`
- SQL dumps: `schema.sql`, `db/schema.sql`
- SQL migrations: `migrations/`, `alembic/versions/`, `db/migration/`

For SQL migrations: read the migration files (especially consolidated or latest migrations) and reconstruct the schema from `CREATE TABLE` / `op.create_table()` statements.

Save to `<reef-root>/sources/schemas/{service}/{sub}/schema.md`.

### Tier 2 — Cached recipe replay

Same as API tier 2. If a cached ERD recipe exists, replay it.

### Tier 3 — Runtime extraction (max 5 attempts)

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

**Beanie/Mongoose:** Read the document class definitions (these are typically self-describing — fields, validators, indexes are all in the class). No runtime extraction needed — treat as tier 4.

**Alembic:** Read the latest or consolidated migration file. It contains the ground-truth schema as `op.create_table(...)` calls. No runtime extraction needed — treat as tier 1 if migration files exist.

Same 5-attempt protocol as API extraction. Same stub/env patterns. Same package manager requirement — never use bare `python3`.

### Tier 4 — Direct code reading (fallback)

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

## Step 4 — Cache successful recipes

After all repos are processed, write `.reef/source-recipes.json`:

```json
{
  "version": 1,
  "recipes": {
    "cdm/breast": {
      "api": {
        "tier": 1,
        "method": "existing openapi.json",
        "source_path": "applications/breast/openapi.json",
        "output": "sources/apis/cdm/breast/openapi.json",
        "last_success": "2026-04-11"
      },
      "erd": {
        "tier": 4,
        "method": "SQLAlchemy model reading",
        "source_path": "applications/breast/src/app/models/",
        "output": "sources/schemas/cdm/breast/schema.md",
        "last_success": "2026-04-11"
      }
    },
    "ctl": {
      "api": {
        "tier": 3,
        "method": "fastapi_oneshot",
        "command": "python3 -c \"from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))\"",
        "app_path": "src",
        "env_stubs": {"DB_HOST": "localhost", "AUTH_SECRET": "stub"},
        "dep_stubs": ["internal_auth_client"],
        "output": "sources/apis/ctl/openapi.json",
        "last_success": "2026-04-11"
      },
      "erd": null
    }
  }
}
```

- Recipe keys use the service/sub path (matching the output directory), not repo names.
- Only cache recipes that succeeded.
- Set `null` for repos with no API or no data layer.
- The `tier` field records which tier succeeded, for diagnostics.

---

## Step 5 — Log and report

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Source extraction: N API specs, M ERDs extracted" --reef <reef-root>
```

**Do not run `reef.py index` or `rebuild-index` or `rebuild-map` here.** Source only writes to `sources/` and `.reef/source-recipes.json` — it does not create artifacts. Re-indexing is handled by snorkel (if running in parallel) or by the next skill that runs (scuba, update, etc.). This avoids race conditions with snorkel's reef.py calls.

Report what was generated:

```
Source extraction complete:

| Service | App              | API                  | ERD                  |
|---------|------------------|----------------------|----------------------|
| CDM     | breast           | tier 1 (existing)    | tier 4 (code reading)|
| CDM     | chest            | tier 1 (existing)    | tier 4 (code reading)|
| CTL     | —                | tier 3 (runtime)     | tier 4 (code reading)|
| DAIP    | authz            | tier 1 (existing)    | tier 1 (migrations)  |
| RDP     | prefect-gateway  | tier 3 (runtime)     | —                    |

Recipes cached to .reef/source-recipes.json for future runs.
```

Then suggest next step:

"API specs and ERDs are now in `sources/apis/` and `sources/schemas/`. The reef has the full picture of your services' APIs and data models.

- `/reef:scuba` — deepen the draft artifacts using these specs. This is where the real knowledge gets built."

---

## Repeat Runs

When `/reef:source` is run again (e.g., after code changes or via `/reef:update`):

1. Load `.reef/source-recipes.json`.
2. For each repo with a cached recipe, try the cached recipe first (Tier 2).
3. If the cached recipe fails (dependency changed, new env var, etc.), fall through to the full tiered protocol starting at Tier 1.
4. Update the recipe cache with any new successes.

This means first runs are slow (discovery + stubbing), but repeat runs are fast (replay cached commands).

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
- **5 attempts max for runtime extraction.** Be smarter about stubbing (read the error, stub specifically), but do not enter an endless debugging spiral. Fall back gracefully.
- **Cache what works.** Repeat runs should be fast.
- **Transparency over silence.** Report which tier succeeded for each repo. If a tier failed, say why briefly.
- **Completeness matters.** List ALL endpoints, ALL tables, ALL fields. This is reference material for scuba and deep.
- **Write meta files.** Every `openapi.json` gets an `openapi.meta.json` so downstream consumers know the provenance.
