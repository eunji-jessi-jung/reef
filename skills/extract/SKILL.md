---
description: "Detect tech stack and extract API summaries and ERD diagrams by reading source code directly"
---

# reef:extract

Scan source codebases for their tech stack, then read model and route files directly to produce API summaries and ERD diagrams. No scripts, no runtime dependencies — Claude reads the code and writes the output. Results are saved to the reef's `sources/raw/`.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for source paths and service groupings.

---

## Step 1 — Detect tech stacks

For each source repo, scan for framework and ORM indicators. Read the dependency files first — this is the fastest signal:

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
| Flask | `flask` in deps + `flask-restx` or `flask-smorest` or `apispec` |
| Express | `express` in deps |
| NestJS | `@nestjs/core` in deps |
| Go (gin/echo/chi) | `gin-gonic`, `echo`, `chi` in go.mod |
| Spring Boot | `spring-boot-starter-web` in deps |

**ORM / data layer indicators:**

| ORM | Signal | Where to find models |
|-----|--------|---------------------|
| SQLAlchemy | `sqlalchemy` in deps | `models/`, `db/models/`, files with `Base = declarative_base()` |
| Django ORM | `django` in deps | `models.py` files in each app |
| Prisma | `prisma/schema.prisma` file | The schema file itself is the model |
| TypeORM | `typeorm` in deps | Files with `@Entity()` decorators |
| Sequelize | `sequelize` in deps | Files in `models/` |
| GORM | `gorm.io/gorm` in go.mod | Struct definitions with `gorm:` tags |
| Mongoose | `mongoose` in deps | Files with `new Schema()` |
| Beanie/ODMantic | `beanie` or `odmantic` in deps | Document model classes |
| Tortoise ORM | `tortoise-orm` in deps | Model classes inheriting from `Model` |

Report what you found per repo:

```
Tech stack detected:

| Repo                      | API Framework | ORM/ODM      | DB         |
|---------------------------|---------------|--------------|------------|
| csg-case-curator-backend  | FastAPI       | SQLAlchemy   | PostgreSQL |
| ctl-data-server           | FastAPI       | Beanie       | MongoDB    |
| aipf-authz-api            | Go (chi)      | GORM         | PostgreSQL |
| rdp-prefect-gateway       | Go (net/http) | —            | —          |
```

---

## Step 2 — Extract ERD by reading model files

For each repo where an ORM/ODM was detected:

1. **Find all model/entity files.** Use the ORM signal from Step 1 to locate them (e.g., glob for `**/models.py`, `**/models/*.py`, `**/entities/*.ts`, `**/schema.prisma`, etc.).
2. **Read every model file.** Extract: class/struct names, field names, field types, primary keys, foreign keys, relationships, indexes.
3. **Write a Mermaid ERD** to `<reef-root>/sources/raw/<repo-name>-erd.md`:

```markdown
# ERD — <repo-name>

\`\`\`mermaid
erDiagram
    users {
        UUID id PK
        VARCHAR email
        VARCHAR name
        TIMESTAMP created_at
    }
    projects {
        UUID id PK
        UUID owner_id FK
        VARCHAR name
        VARCHAR status
    }
    users ||--o{ projects : "owns"
\`\`\`
```

**Guidelines:**
- Include ALL tables/collections, not just the "important" ones.
- Include ALL fields with their types.
- Mark PK and FK explicitly.
- Show relationships with cardinality (`||--o{`, `}o--o{`, etc.).
- For MongoDB/document stores, show embedded documents as separate entities with a note about embedding vs referencing.

**Special cases:**
- **Prisma:** The schema file is already a complete, readable model. Read it, convert to Mermaid, save.
- **Alembic/migration files:** If model files are unclear, read the latest migration files for the ground truth schema.
- **No model files found:** Skip this repo for ERD. Note it in the report.

---

## Step 3 — Extract API summary by reading route files

For each repo where an API framework was detected:

1. **Check for existing specs first.** Look for `openapi.json`, `openapi.yaml`, `swagger.json`, or `swagger.yaml` in the repo root, `docs/`, `static/`, or `scripts/` directories. If found, copy it directly to `sources/raw/<repo-name>-openapi.json` and skip to the next repo.
2. **Find all route/controller files.** Use the framework signal from Step 1 (e.g., glob for `**/routers/*.py`, `**/routes/*.ts`, `**/controllers/*.go`, etc.).
3. **Read every route file.** Extract: HTTP method, path, handler name, request/response types if annotated, auth guards/middleware.
4. **Write an API summary** to `<reef-root>/sources/raw/<repo-name>-api.md`:

```markdown
# API — <repo-name>

## Endpoints

| Method | Path | Handler | Auth | Description |
|--------|------|---------|------|-------------|
| GET | /api/v1/projects | list_projects | JWT | List all projects |
| POST | /api/v1/projects | create_project | JWT + Admin | Create a new project |
| GET | /api/v1/projects/{id} | get_project | JWT | Get project by ID |
| ... | ... | ... | ... | ... |

## Route Groups

- `/api/v1/projects` — Project CRUD and management
- `/api/v1/users` — User management
- `/api/v1/auth` — Authentication endpoints

## Middleware

- JWT validation on all `/api/*` routes
- Rate limiting on auth endpoints
- CORS configured for frontend origins
```

**Guidelines:**
- List ALL endpoints, not just the main ones. Completeness matters for a reference doc.
- Group by route prefix or resource.
- Note versioning if present (v1, v2, etc.).
- Include auth requirements per endpoint or group if they differ.
- Add a brief description for each endpoint inferred from the handler name and request/response types.

**Special cases:**
- **Existing OpenAPI spec found:** Copy as-is. It's the source of truth.
- **Multiple API versions:** Document all versions. Note which are current vs legacy.
- **No route files found:** Skip this repo for API. Note it in the report.

---

## Step 4 — Report and re-index

Report what was generated:

```
Extraction complete:

| Repo                      | ERD | API |
|---------------------------|-----|-----|
| csg-case-curator-backend  | yes | yes |
| ctl-data-server           | yes | yes |
| aipf-authz-api            | yes | yes (existing openapi.json) |
| rdp-prefect-gateway       | —   | —   |
```

Then re-index:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

---

## Standalone vs. Init Integration

This skill can be run two ways:

- **Standalone:** User runs `/reef:extract` on an existing reef. Follow all steps above.
- **Called from init:** During `/reef:init` Step 5, after the structural scan detects API frameworks or ORMs. In this case, skip Context Loading (already done) and skip re-indexing in Step 4 (init handles it).

---

## Voice and Personality

- Curious Researcher voice.
- No emojis. No exclamation marks.
- Report what was detected, what was extracted, what was skipped. Be matter-of-fact.
- When model or route files can't be found, note it and move on. Do not block.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No API framework or ORM detected in any repo**: "No API frameworks or data models detected. You can manually add specs to `sources/raw/` or run `/reef:extract` again after checking the repos."
- **Model files not where expected**: Try alternative common locations. If still not found, skip and note in report.
- **Partial success**: Normal. Some repos have APIs but no data layer, or vice versa. Report per-repo.
