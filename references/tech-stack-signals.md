# Tech Stack Detection Signals

Reference tables for identifying API frameworks, ORMs, and package managers from dependency files. Used by reef:source Step 1.

---

## Dependency Files to Check

- Python: `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `setup.cfg`
- Node: `package.json`
- Go: `go.mod`
- Java/Kotlin: `build.gradle`, `pom.xml`
- Ruby: `Gemfile`
- Rust: `Cargo.toml`

## API Framework Indicators

| Framework | Signal |
|-----------|--------|
| FastAPI | `fastapi` in deps |
| Django REST Framework | `djangorestframework` in deps |
| Flask | `flask` in deps + `flask-restx` or `flask-smorest` |
| Express | `express` in deps |
| NestJS | `@nestjs/core` in deps |
| Go (gin/echo/chi) | `gin-gonic`, `echo`, `chi` in go.mod |
| Spring Boot | `spring-boot-starter-web` in deps |

## ORM / Data Layer Indicators

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

## Package Manager Detection

| Manager | Signal | Run command |
|---------|--------|-------------|
| Poetry | `pyproject.toml` with `[tool.poetry]` + `poetry.lock` | `poetry run python3 -c "..."` |
| uv | `uv.lock` or `pyproject.toml` with `[tool.uv]` | `uv run python3 -c "..."` |
| Pipenv | `Pipfile` + `Pipfile.lock` | `pipenv run python3 -c "..."` |
| pip/venv | `.venv/` or `venv/` directory | `. .venv/bin/activate && python3 -c "..."` |
| None | No lock file, no venv | `python3 -c "..."` (bare, least likely to work) |

**This is critical for tier 2 (runtime extraction).** Running bare `python3` will fail for most repos because dependencies are installed in the project's virtual environment, not system Python. Always use the package manager's run command.

## Multi-App Repos

Some repos contain multiple applications (e.g., an Nx monorepo with `applications/gateway/`, `applications/ledger/`). Detect each sub-application separately. Check for per-app dependency files and entry points. The package manager may be at the repo root (shared) or per-app.
