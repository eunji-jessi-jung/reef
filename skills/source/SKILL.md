---
description: "Extract full API specs and ERDs from source repos using a tiered protocol"
---

# reef:source

Extract complete API specifications and entity-relationship diagrams from source codebases. Uses a tiered protocol — try the fastest reliable method first, fall back gracefully. Caches successful recipes for repeat runs.

This skill sits between snorkel and scuba in the core loop:

```
init → snorkel → source → scuba → deep
```

Snorkel produces structural draft artifacts. Source extracts the full runtime specs. Scuba uses both to ask deeper questions.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for source paths and service groupings.
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

Report what was detected:

```
Tech stacks detected:

| Repo              | API Framework | ORM/ODM      | DB         |
|-------------------|---------------|--------------|------------|
| order-service     | FastAPI       | SQLAlchemy   | PostgreSQL |
| pay-gateway       | Express       | Prisma       | PostgreSQL |
| inventory-api     | Go (chi)      | GORM         | PostgreSQL |
| notification-svc  | —             | —            | —          |
```

---

## Step 2 — Extract API specs (tiered)

For each repo where an API framework was detected, follow the tiers in order. Stop at the first success.

### Tier 1 — Copy existing spec

Search for existing API specs in these locations:
- Repo root: `openapi.json`, `openapi.yaml`, `swagger.json`, `swagger.yaml`
- Common subdirs: `docs/`, `static/`, `spec/`, `api/`, `scripts/`
- Build output: `build/`, `dist/`, `target/`

If found, copy directly to `<reef-root>/sources/raw/<repo-name>-api.json` (or `.yaml`).

Report: "Found existing OpenAPI spec at `docs/openapi.json` — copying directly."

**Move to the next repo.** Do not attempt further tiers.

### Tier 2 — Cached recipe replay

If `.reef/source-recipes.json` has a recipe for this repo, try it first:

1. Read the cached recipe (app path, env stubs, dep stubs).
2. Re-create any dependency stubs in a temp directory.
3. Run the cached command.
4. If it succeeds, save the output and move on.
5. If it fails, discard the recipe and fall through to Tier 3.

Report: "Replaying cached recipe for order-service..."

### Tier 3 — Runtime extraction (max 3 attempts)

This tier tries to import the application and dump its API schema at runtime. The approach depends on the framework:

**FastAPI / Flask-RESTX / Flask-Smorest:**
```bash
PYTHONPATH=<app-src-dir>:<stubs-dir> python3 -c "
import json
from <app_module>.main import app  # or wherever the app object lives
print(json.dumps(app.openapi(), indent=2))
"
```

**Django REST Framework:**
```bash
DJANGO_SETTINGS_MODULE=<project>.settings python3 -c "
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
# Output: docs/swagger.json
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
2. **Run the extraction command.**
3. **If it succeeds** — save output, cache the recipe, move on.
4. **If it fails** — read the error message:
   - **Missing environment variable** (e.g., `KeyError: 'DB_HOST'`): Add a dummy value (`"localhost"`, `"stub"`, `"true"`) and retry.
   - **Missing private package** (e.g., `ModuleNotFoundError: No module named 'internal_auth_client'`): Create a minimal stub package in a temp directory (empty `__init__.py` + stub classes that return `None` for any method call) and add to `PYTHONPATH`. Retry.
   - **Other import error**: Read the traceback to understand what's needed. If it's a fixable configuration issue, fix and retry. If it's fundamental (e.g., requires a running database connection at import time), give up.
5. **After 3 failed attempts** — report what went wrong, fall through to Tier 4.

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

This generic stub handles most import-time dependency resolution. It will NOT produce correct runtime behavior, but API schema generation typically only needs the app to initialize — it doesn't need the dependencies to actually work.

**Important:** Create stubs in a temp directory. Add to `PYTHONPATH` / `NODE_PATH`. Clean up after extraction. Never modify the source repo.

### Tier 4 — Direct code reading (fallback)

If all runtime extraction attempts fail, read the code directly:

1. **Find all route/controller files** using the framework signal from Step 1.
2. **Read every route file.** Extract: HTTP method, path, handler name, request/response types if annotated, auth guards/middleware.
3. **Write a structured API summary** to `<reef-root>/sources/raw/<repo-name>-api.md`.

```markdown
# API — <repo-name>

> Note: Extracted by reading source code directly. This may be incomplete compared to the runtime OpenAPI spec. Some computed routes, dynamic registrations, or inherited endpoints may be missing.

## Endpoints

| Method | Path | Handler | Auth | Description |
|--------|------|---------|------|-------------|
| GET | /api/v1/orders | list_orders | JWT | List all orders |
| POST | /api/v1/orders | create_order | JWT + Admin | Create a new order |
| ... | ... | ... | ... | ... |

## Route Groups
- `/api/v1/orders` — Order CRUD and management
- `/api/v1/users` — User management

## Middleware
- JWT validation on all `/api/*` routes
```

Report: "Runtime extraction failed for order-service (missing database connection at import time). Fell back to reading route files directly — 23 endpoints found across 4 router files."

---

## Step 3 — Extract ERDs (tiered)

For each repo where an ORM/ODM was detected, follow the tiers in order.

### Tier 1 — Copy existing schema

Search for existing schema files:
- Prisma: `prisma/schema.prisma` (this IS the model — convert to Mermaid)
- Existing ERDs: `docs/erd.md`, `docs/schema.md`, `docs/database.md`
- SQL dumps: `schema.sql`, `db/schema.sql`

If found, copy or convert to `<reef-root>/sources/raw/<repo-name>-erd.md`.

### Tier 2 — Cached recipe replay

Same as API tier 2. If a cached ERD recipe exists, replay it.

### Tier 3 — Runtime extraction (max 3 attempts)

**SQLAlchemy:**
```python
from sqlalchemy import inspect, create_engine
from <app>.models import Base  # or wherever models are defined
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
inspector = inspect(engine)
# Dump table names, columns, foreign keys
```

**Django:**
```bash
python3 manage.py inspectdb
```

**Beanie/Mongoose:** Read the document class definitions (these are typically self-describing — fields, validators, indexes are all in the class).

**Alembic:** Read the latest migration file. It contains the ground-truth schema as `op.create_table(...)` calls.

Same 3-attempt protocol as API extraction. Same stub/env patterns.

### Tier 4 — Direct code reading (fallback)

1. **Find all model/entity files** using ORM signals.
2. **Read every model file.** Extract: class/struct names, field names, field types, primary keys, foreign keys, relationships, indexes.
3. **Write a Mermaid ERD** to `<reef-root>/sources/raw/<repo-name>-erd.md`:

```markdown
# ERD — <repo-name>

> Note: Extracted by reading model source code directly. Computed fields, dynamic relationships, or migration-only columns may be missing.

\`\`\`mermaid
erDiagram
    orders {
        UUID id PK
        UUID customer_id FK
        VARCHAR status
        TIMESTAMP created_at
    }
    order_items {
        UUID id PK
        UUID order_id FK
        UUID product_id FK
        INT quantity
    }
    orders ||--o{ order_items : "contains"
\`\`\`
```

Include ALL tables/collections and ALL fields. Mark PK and FK. Show relationship cardinality.

---

## Step 4 — Cache successful recipes

After all repos are processed, write `.reef/source-recipes.json`:

```json
{
  "version": 1,
  "recipes": {
    "order-service": {
      "api": {
        "tier": 2,
        "method": "fastapi_oneshot",
        "command": "python3 -c \"from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))\"",
        "app_path": "applications/orders/src",
        "env_stubs": {
          "DB_HOST": "localhost",
          "DB_PORT": "5432",
          "AUTH_SECRET": "stub"
        },
        "dep_stubs": ["internal_auth_client"],
        "last_success": "2026-04-11"
      },
      "erd": {
        "tier": 1,
        "method": "copy_existing",
        "source_path": "prisma/schema.prisma",
        "last_success": "2026-04-11"
      }
    },
    "notification-svc": {
      "api": null,
      "erd": null
    }
  }
}
```

- Only cache recipes that succeeded.
- Set `null` for repos with no API or no data layer.
- The `tier` field records which tier succeeded, for diagnostics.

---

## Step 5 — Re-index and report

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Source extraction: N API specs, M ERDs extracted" --reef <reef-root>
```

Report what was generated:

```
Source extraction complete:

| Repo              | API          | ERD          |
|-------------------|--------------|--------------|
| order-service     | tier 3 (runtime) | tier 1 (prisma) |
| pay-gateway       | tier 1 (existing spec) | tier 4 (code reading) |
| inventory-api     | tier 3 (runtime) | tier 3 (runtime) |
| notification-svc  | —            | —            |

Recipes cached to .reef/source-recipes.json for future runs.
```

Then suggest next step:

"API specs and ERDs are now in `sources/raw/`. The reef has the full picture of your services' APIs and data models.

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
- **No API framework or ORM detected in any repo**: "No API frameworks or data models detected in any source repo. If your services have APIs, you can manually add specs to `sources/raw/`."
- **All tiers fail for a repo**: Report what was tried and why it failed. Move on to the next repo. Partial success is normal.
- **Temp directory cleanup**: Always clean up stub directories, even on failure. Use try/finally.
- **Source repo not found at path**: Warn, skip, continue.

---

## Key Rules

- **Never modify source repos.** Stubs go in temp directories. Output goes in the reef's `sources/raw/`.
- **3 attempts max for runtime extraction.** Do not enter a debugging spiral. Fall back gracefully.
- **Cache what works.** Repeat runs should be fast.
- **Transparency over silence.** Report which tier succeeded for each repo. If a tier failed, say why briefly.
- **Completeness matters.** List ALL endpoints, ALL tables, ALL fields. This is reference material for scuba and deep.
