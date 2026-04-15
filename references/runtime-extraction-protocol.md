# Runtime Extraction Protocol (Tier 2)

Tier 2 tries to import the application and dump its API schema at runtime. Max 5 attempts. Used by reef:source Step 2.

---

## Step 0 — Check for an existing generation script

This is the single most reliable runtime path — the repo maintainers already solved the dependency and env var problems. Always check this first.

Search in these locations (in order):
```bash
# Per-app scripts (for monorepos):
ls <app-dir>/scripts/generate_api_schema.py 2>/dev/null
ls <app-dir>/scripts/generate_openapi.py 2>/dev/null

# Repo-root scripts:
ls <repo-root>/scripts/generate_api_schema.py 2>/dev/null
ls <repo-root>/scripts/generate_openapi.py 2>/dev/null

# Broader search if nothing found:
find <repo-root> -name "generate_api*" -o -name "generate_openapi*" -o -name "openapi_gen*" 2>/dev/null | head -5
```

If found, run it with the project's package manager and the same env vars / PYTHONPATH / stubs you would use for inline extraction:
```bash
PYTHONPATH=<stubs>:<app-src>:<lib-paths> poetry run python scripts/generate_api_schema.py
```

The script typically writes `openapi.json` to its own directory or to stdout. Check both. If the script succeeds, use its output and move to the next repo.

## Step 1 — Use the package manager's run command

Always wrap Python commands with the run command determined in pre-flight. Prefer `poetry run python` when poetry is available. Never use bare `python3`.

**FastAPI / Flask-RESTX / Flask-Smorest:**
```bash
PYTHONPATH=<app-src-dir>:<stubs-dir> poetry run python3 -c "
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

## Steps 2-8 — Attempt protocol

2. **Pre-read the config/settings class BEFORE your first attempt.** Look for Pydantic `BaseSettings`, config classes reading `os.environ`, `.env.example` files. Extract ALL required env vars and set dummy values upfront:
   - Database URLs: `"localhost"`, `"stub"`, `"5432"`, `"27017"`
   - Auth/JWT secrets: `"stub"`
   - URLs: `"https://stub"`
   - JSON-valued vars: `"[]"`, `"{}"`, `'{"key": "stub"}'`
   - Boolean flags: `"true"`, `"false"`

3. **Build the PYTHONPATH for monorepos.** Add ALL shared library source directories:
   ```
   PYTHONPATH=app/src:libraries/backend-core/src:libraries/auth/src:<stubs-dir>
   ```

4. **Identify the package manager and working directory.** For monorepos, run from the directory with `pyproject.toml` / `poetry.lock`. If venv is broken:
   ```bash
   uv venv --python 3.11
   uv pip install -r <(poetry export -f requirements.txt --without-hashes 2>/dev/null || echo "")
   ```

5. **Run the extraction command** using `poetry run` / `uv run` / `pipenv run`.

6. **If it succeeds** — save output as `openapi.json`, write meta, cache the recipe, move on.

7. **If it fails** — read the error message carefully:
   - **Missing environment variable** (e.g., `KeyError: 'DB_HOST'`): Add the dummy value and retry.
   - **Missing private package** (e.g., `ModuleNotFoundError`): Create a comprehensive stub — see `references/stub-patterns.md`.
   - **Missing sub-module**: The stub needs deeper structure. Read import statements in the traceback.
   - **Decorator/function signature mismatch**: Stub must return a callable that returns a decorator. See stub patterns.
   - **Broken venv / wrong Python version**: Use `uv` to create a fresh venv.
   - **Other import error**: Read full traceback. If fundamental (running database, C extension), give up.

8. **After 5 failed attempts** — report what went wrong, fall through to Tier 3 or Tier 4.

**Stub creation:** Read `references/stub-patterns.md` for stub patterns. Create stubs in a temp directory. Add to `PYTHONPATH` / `NODE_PATH`. Clean up after extraction. Never modify the source repo.
