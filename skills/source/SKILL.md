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
      breast/openapi.json       # tier 2: runtime extracted
      chest/openapi.json        # tier 2: runtime extracted
      manufacturer/openapi.json # tier 2: runtime extracted
      inference-result/openapi.json  # tier 2: runtime extracted
    ctl/
      openapi.json              # tier 2: runtime extracted (single-app repo)
    daip/
      authz/openapi.json        # tier 2: runtime extracted (swag)
      data-lineage/openapi.json # tier 2: runtime extracted
    rdp/
      prefect-gateway/openapi.json  # tier 2: runtime extracted
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

**This is critical for tier 2 (runtime extraction).** Running bare `python3` will fail for most repos because dependencies are installed in the project's virtual environment, not system Python. Always use the package manager's run command.

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

**Design principle: live truth over speed.** A stale spec that gets one endpoint wrong destroys trust with engineers. Runtime extraction from today's code is always preferred over copying a file that may have been generated months ago.

### Tier 1 — Cached recipe replay

If `.reef/source-recipes.json` has a recipe for this repo/app, try it first. Cached recipes always store runtime extraction commands (never file copies), so replaying them produces a fresh spec from current code.

1. Read the cached recipe (app path, env stubs, dep stubs, command).
2. Re-create any dependency stubs in a temp directory.
3. Run the cached command.
4. If it succeeds, save the output as `openapi.json` and move on.
5. If it fails, discard the recipe and fall through to Tier 2.

Report: "Replaying cached recipe for ctl-data-server..."

### Tier 2 — Runtime extraction (max 5 attempts)

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

**Protocol for each attempt:**

1. **Find the app entry point.** Read `main.py`, `app.py`, `main.go`, `index.ts`, etc. Identify the app object and its import path.

2. **Pre-read the config/settings class BEFORE your first attempt.** This is the single most impactful step — it prevents 2-3 wasted attempts on missing env vars. Look for:
   - Pydantic `BaseSettings` classes (common in FastAPI apps)
   - Config dataclasses or plain classes reading `os.environ`
   - `.env.example` or `.env.template` files
   
   From the settings class, extract ALL required env vars and set dummy values upfront. Common patterns:
   - Database URLs: `"localhost"`, `"stub"`, `"5432"`, `"27017"`
   - Auth/JWT secrets: `"stub"`
   - URLs: `"https://stub"`
   - JSON-valued vars: `"[]"`, `"{}"`, `'{"key": "stub"}'`
   - Boolean flags: `"true"`, `"false"`
   - Cache/timeout values: `"30"`, `"512"`

3. **Build the PYTHONPATH for monorepos.** If the repo has shared libraries (e.g., `libraries/backend-core/src/`), add ALL library source directories to PYTHONPATH. Example for a monorepo with 4 shared libraries:
   ```
   PYTHONPATH=app/src:libraries/backend-core/src:libraries/auth/src:libraries/cc-schema/src:libraries/cc-primitive/src:<stubs-dir>
   ```

4. **Identify the package manager and working directory.** Use the detected package manager from Step 1. For monorepos, run from the directory that contains the `pyproject.toml` / `poetry.lock`. If the project's venv is broken or missing, use `uv` as a fallback:
   ```bash
   # Create a fresh venv and install deps
   uv venv --python 3.11
   uv pip install -r <(poetry export -f requirements.txt --without-hashes 2>/dev/null || echo "")
   # Or install key packages directly
   uv pip install fastapi uvicorn pydantic sqlalchemy
   ```

5. **Run the extraction command** using `poetry run` / `uv run` / `pipenv run`.

6. **If it succeeds** — save output as `openapi.json`, write meta, cache the recipe (including env stubs and PYTHONPATH), move on.

7. **If it fails** — read the error message carefully:
   - **Missing environment variable** (e.g., `KeyError: 'DB_HOST'`): You missed it in the pre-read. Add the dummy value and retry.
   - **Missing private package from a private registry** (e.g., `ModuleNotFoundError: No module named 'internal_auth_client'`): This is common in enterprise repos. The package is hosted on a private PyPI/Artifact Registry and can't be pip-installed without auth. Create a comprehensive stub — see below.
   - **Missing sub-module** (e.g., `No module named 'auth_client.api.permissions_api'`): The stub needs deeper structure. Read the import statements in the traceback to understand exactly which sub-modules and classes are needed.
   - **Decorator/function signature mismatch**: Some stubs need to return actual decorators, not just `None`. If a stub is used as `@check_authorization(...)`, the stub must return a callable that returns a decorator. See stub patterns below.
   - **Broken venv / wrong Python version**: Use `uv` to create a fresh venv with the right Python version.
   - **Other import error**: Read the full traceback. If fixable, fix and retry. If fundamental (requires a running database, C extension), give up.

8. **After 5 failed attempts** — report what went wrong, fall through to Tier 3 (existing spec) or Tier 4 (code reading).

**Stub creation — the simple stub:**
```python
# For packages where only top-level import matters
# <stub-dir>/<package_name>/__init__.py
class _Stub:
    def __init__(self, *a, **kw): pass
    def __getattr__(self, name): return lambda *a, **kw: None
    def __call__(self, *a, **kw): return self

def __getattr__(name):
    return _Stub()
```

**Stub creation — the comprehensive stub (for generated API clients, auth libraries):**

When the simple stub fails because the code imports specific sub-modules and classes, build a deeper structure. This is common with generated API clients (OpenAPI-generated SDKs):

```
<stub-dir>/
  <package_name>/
    __init__.py                    # module-level __getattr__
    api/
      __init__.py                  # module-level __getattr__
      permissions_api.py           # class PermissionsApi: def __init__(self, api_client=None): pass
      resource_api.py              # class ResourceApi: ...
      user_api.py                  # class UserApi: ...
    models/
      __init__.py                  # module-level __getattr__
    rest.py                        # class RESTResponse: status=200; data=b'{}'
    api_client.py                  # class ApiClient: def __init__(self, configuration=None): ...
    configuration.py               # class Configuration: def __init__(self, host=None): ...
    exceptions.py                  # class ApiException(Exception): pass
    decorators/
      __init__.py
      authz_decorators.py          # see decorator pattern below
```

**Decorator stub pattern** — when a private package provides decorators used in route definitions:
```python
# decorators/authz_decorators.py
class AuthzConfig: pass
class AuthzError(Exception): pass

def check_authorization(*args, **kwargs):
    """Return a no-op decorator that preserves the original function."""
    def decorator(fn):
        return fn
    return decorator
```

The key insight: `check_authorization` is used as `@check_authorization(resource=..., action=...)` — it must be a function that returns a decorator, not a plain function. Getting this wrong causes `TypeError: 'NoneType' object is not callable`.

**Important:** Create stubs in a temp directory. Add to `PYTHONPATH` / `NODE_PATH`. Clean up after extraction. Never modify the source repo.

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

Report with the warning: "Copied existing spec for cdm/breast — but the spec file is 5 months older than the latest route changes. Endpoints may be missing or outdated."

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

Write `openapi.meta.json` with `"extraction_tier": 4`.

Report: "Runtime extraction failed for ctl-data-server (missing MongoDB connection at import time). Fell back to code reading — 47 endpoints extracted, saved as OpenAPI JSON."

---

## Step 3 — Extract ERDs (tiered)

For each repo/app where an ORM/ODM was detected, follow the tiers in order.

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

## Step 4 — Cache successful recipes

After all repos are processed, write `.reef/source-recipes.json`:

```json
{
  "version": 1,
  "recipes": {
    "cdm/breast": {
      "api": {
        "tier": 2,
        "method": "fastapi_oneshot",
        "command": "python3 -c \"from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))\"",
        "app_path": "applications/breast/src",
        "env_stubs": {"DB_HOST": "localhost", "AUTH_SECRET": "stub"},
        "dep_stubs": ["aipf_authz_client"],
        "output": "sources/apis/cdm/breast/openapi.json",
        "last_success": "2026-04-11"
      },
      "erd": {
        "tier": 2,
        "method": "alembic_migration_reading",
        "source_path": "applications/breast/alembic/versions/",
        "output": "sources/schemas/cdm/breast/schema.md",
        "last_success": "2026-04-11"
      }
    },
    "ctl": {
      "api": {
        "tier": 2,
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
- **Only cache runtime extraction recipes** (tier 2). Never cache tier 3 (existing file copies) — those would just replay a stale copy forever.
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
| CDM     | breast           | tier 2 (runtime)     | tier 2 (Alembic)     |
| CDM     | chest            | tier 2 (runtime)     | tier 2 (Alembic)     |
| CTL     | —                | tier 2 (runtime)     | tier 3 (Beanie models)|
| DAIP    | authz            | tier 2 (runtime/swag)| tier 2 (migrations)  |
| RDP     | prefect-gateway  | tier 2 (runtime)     | —                    |

Recipes cached to .reef/source-recipes.json for future runs.
```

Then suggest next step:

"API specs and ERDs are now in `sources/apis/` and `sources/schemas/`. The reef has the full picture of your services' APIs and data models.

- `/reef:scuba` — deepen the draft artifacts using these specs. This is where the real knowledge gets built."

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
- **5 attempts max for runtime extraction.** Be smarter about stubbing (read the error, stub specifically), but do not enter an endless debugging spiral. Fall back gracefully.
- **Cache what works.** Repeat runs should be fast.
- **Transparency over silence.** Report which tier succeeded for each repo. If a tier failed, say why briefly.
- **Completeness matters.** List ALL endpoints, ALL tables, ALL fields. This is reference material for scuba and deep.
- **Write meta files.** Every `openapi.json` gets an `openapi.meta.json` so downstream consumers know the provenance.
