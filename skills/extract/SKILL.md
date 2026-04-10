---
description: "Detect tech stack and generate reusable scripts to extract OpenAPI specs and ERD diagrams"
---

# reef:extract

Scan source codebases for their tech stack, generate reusable extraction scripts, run them, and save the output to the reef's `sources/raw/`. The scripts persist in the reef so they can be re-run later when the codebase changes.

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

**API framework detection:**

| Framework | Signal | OpenAPI extraction method |
|-----------|--------|--------------------------|
| FastAPI | `fastapi` in deps | `python -c "from {app_module} import app; import json; print(json.dumps(app.openapi()))" > openapi.json` |
| Django REST Framework | `djangorestframework` in deps | `drf-spectacular` or `drf-yasg` — check if already installed, generate schema |
| Flask | `flask` in deps + `flask-restx` or `flask-smorest` or `apispec` | Framework-specific; check which OpenAPI plugin is used |
| Express | `express` in deps + `swagger-jsdoc` or `@nestjs/swagger` | Run the swagger generation script |
| NestJS | `@nestjs/core` in deps | `npx ts-node -e "..."` using SwaggerModule |
| Go (gin/echo/chi) | `gin-gonic`, `echo`, `chi` in go.mod | Check for `swaggo/swag`; if present, run `swag init` |
| Spring Boot | `springdoc-openapi` or `springfox` in deps | Hit `/v3/api-docs` or generate via build task |

**ORM / data layer detection:**

| ORM | Signal | ERD extraction method |
|-----|--------|----------------------|
| SQLAlchemy | `sqlalchemy` in deps | Find model files, parse model classes, generate ERD via `eralchemy2` or manual Mermaid |
| Alembic | `alembic/` directory | Read migration files for schema history |
| Django ORM | `django` in deps + `models.py` files | `python manage.py graph_models -a` via django-extensions |
| Prisma | `prisma/schema.prisma` file | Parse schema.prisma directly — it is already a readable data model |
| TypeORM | `typeorm` in deps | Find entity files, parse decorators |
| Sequelize | `sequelize` in deps | Find model definitions |
| GORM | `gorm.io/gorm` in go.mod | Find struct definitions with gorm tags |
| Mongoose | `mongoose` in deps | Find schema definitions |
| Tortoise ORM | `tortoise-orm` in deps | Find model files, parse model classes |

Report what you found per repo:

```
Tech stack detected:

| Repo                      | API Framework | ORM          | DB         |
|---------------------------|---------------|--------------|------------|
| csg-case-curator-backend  | FastAPI       | SQLAlchemy   | PostgreSQL |
| ctl-data-server           | FastAPI       | SQLAlchemy   | PostgreSQL |
| aipf-authz-api            | Go (chi)      | GORM         | PostgreSQL |
| rdp-prefect-gateway       | Go (net/http) | —            | —          |
| ...                       | ...           | ...          | ...        |
```

---

## Step 2 — Generate extraction scripts

Create a `scripts/` directory inside the reef root. Generate one script per extraction type, per repo. Scripts must be **reusable** — the user or CI can re-run them whenever the codebase changes.

### OpenAPI extraction script

For each repo where an API framework was detected, generate a script at:
`<reef-root>/scripts/extract-openapi-<repo-name>.sh`

The script should:
1. `cd` into the source repo
2. Set up the minimal environment needed (activate venv if present, install extraction deps if missing)
3. Extract the OpenAPI spec to stdout or a file
4. Copy the output to `<reef-root>/sources/raw/<repo-name>-openapi.json`

**Example for FastAPI:**
```bash
#!/bin/bash
# Extract OpenAPI spec from <repo-name>
# Re-run this script whenever the API changes.
set -euo pipefail

REPO_DIR="<absolute-path-to-repo>"
OUTPUT="<absolute-path-to-reef>/sources/raw/<repo-name>-openapi.json"

cd "$REPO_DIR"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Extract OpenAPI spec from FastAPI app
# Adjust the import path if the app is not at app.main:app
python3 -c "
from app.main import app
import json
spec = app.openapi()
print(json.dumps(spec, indent=2))
" > "$OUTPUT"

echo "OpenAPI spec saved to $OUTPUT"
```

**Important:** The script is a starting point. The import path (`app.main:app`) must be adapted based on what the structural scan reveals about the actual app entry point. Read the repo's main module, `__main__.py`, or framework config to find the correct import.

### ERD extraction script

For each repo where an ORM was detected, generate a script at:
`<reef-root>/scripts/extract-erd-<repo-name>.sh`

The script should:
1. `cd` into the source repo
2. Find all model definitions
3. Generate a Mermaid ERD diagram (preferred — portable, readable, renders in Obsidian)
4. Save to `<reef-root>/sources/raw/<repo-name>-erd.md`

**For SQLAlchemy — generate Mermaid by parsing models:**
```bash
#!/bin/bash
# Extract ERD from <repo-name> SQLAlchemy models
# Re-run this script whenever models change.
set -euo pipefail

REPO_DIR="<absolute-path-to-repo>"
OUTPUT="<absolute-path-to-reef>/sources/raw/<repo-name>-erd.md"

cd "$REPO_DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python3 -c "
# Parse SQLAlchemy models and output Mermaid ERD
# Adjust the import path to match the project's model location
from app.db.models import Base
from sqlalchemy import inspect

print('# ERD — <repo-name>')
print()
print('\`\`\`mermaid')
print('erDiagram')

for mapper in Base.registry.mappers:
    cls = mapper.class_
    table = cls.__tablename__
    columns = inspect(cls).columns
    print(f'    {table} {{')
    for col in columns:
        col_type = str(col.type).split('(')[0]
        pk = ' PK' if col.primary_key else ''
        fk = ' FK' if col.foreign_keys else ''
        print(f'        {col_type} {col.name}{pk}{fk}')
    print('    }')

# Print relationships
for mapper in Base.registry.mappers:
    cls = mapper.class_
    table = cls.__tablename__
    for col in inspect(cls).columns:
        for fk in col.foreign_keys:
            ref_table = fk.column.table.name
            print(f'    {ref_table} ||--o{{ {table} : \"\"')

print('\`\`\`')
" > "$OUTPUT"

echo "ERD saved to $OUTPUT"
```

**For Prisma — just copy and wrap:**
```bash
#!/bin/bash
# Prisma schema is already a readable data model. Copy it as-is.
cp "<repo-dir>/prisma/schema.prisma" "<reef-root>/sources/raw/<repo-name>-schema.prisma"
```

**For cases where model parsing fails or no ORM is detected:** Fall back to reading model/entity files directly and generating Mermaid by hand (Claude reads the model source files and writes the ERD). Note this in the script as a comment.

---

## Step 3 — Run the scripts

Run each generated script. For each one:

1. Execute it
2. If it succeeds: report what was generated and where it was saved
3. If it fails: report the error, suggest what to fix (usually the import path or missing venv), and move on. The script is still saved — the user can fix and re-run it.

Report:

```
Extraction complete:

| Repo                      | OpenAPI | ERD     |
|---------------------------|---------|---------|
| csg-case-curator-backend  | yes     | yes     |
| ctl-data-server           | yes     | yes     |
| aipf-authz-api            | failed  | yes     |
| rdp-prefect-gateway       | —       | —       |

Scripts saved to <reef-root>/scripts/. Re-run them anytime with:
  bash <reef-root>/scripts/extract-openapi-<repo-name>.sh
  bash <reef-root>/scripts/extract-erd-<repo-name>.sh
```

---

## Step 4 — Re-index

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

The newly generated files in `sources/raw/` are now part of the reef's index and will inform future snorkel, scuba, and deep passes.

---

## Standalone vs. Init Integration

This skill can be run two ways:

- **Standalone:** User runs `/reef:extract` on an existing reef. Follow all steps above.
- **Called from init:** During `/reef:init` Step 5, after the structural scan detects API frameworks or ORMs. In this case, skip Step 1 context loading (already done) and skip Step 4 re-indexing (init handles it). Just generate scripts, run them, report results.

---

## Voice and Personality

- Curious Researcher voice.
- No emojis. No exclamation marks.
- Report what was detected, what was generated, what succeeded and failed. Be matter-of-fact.
- When a script fails, diagnose briefly and move on. Do not block on failures.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No API framework or ORM detected in any repo**: "No extractable API specs or data models found. The repos may use patterns I did not recognize — you can manually add specs to `sources/raw/`."
- **Script fails**: Save the script anyway. Report the error. Suggest the likely fix (wrong import path, missing dependency, no venv). The user can fix and re-run.
- **Partial success**: Report per-repo. Some repos will have OpenAPI but no ERD, or vice versa. This is normal.
