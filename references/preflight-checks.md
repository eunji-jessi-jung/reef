# Pre-Flight Checks Protocol

Before attempting runtime extraction, check what tools and environments are available. This prevents burning 5 attempts on a fundamentally broken setup. Used by reef:source Step 1.5.

---

## 1. Check Venv Health

For each repo/app, if a `.venv/` or `venv/` exists, test if the Python binary resolves:

```bash
.venv/bin/python --version 2>/dev/null
```

- If it resolves: venv is healthy, use it.
- If it fails (broken symlink, wrong machine): mark as "broken venv". Check if `uv` is available to fix it (see below).
- If no venv exists: check for package manager (poetry/uv) that can create one.

## 2. Check Tool Availability

Record what's available on this machine:
- `poetry --version` / `python3 -m poetry --version`
- `uv --version` / `python3 -m uv --version`
- `go version` (for Go repos)
- `swag --version` (for Go API extraction)
- `node --version` / `npx --version` (for Node repos)

## 3. Prompt for Missing Tools

If a tool is missing but would unlock runtime extraction, tell the user what to install. These are the project's own build tools — the user would need them to develop in that repo anyway. Present all missing tools at once so the user can install them in one go:

```
Some tools are missing that would enable live-truth extraction:

poetry  — needed for 4 repos (payments/gateway, payments/ledger, orders, ...)
          Install: pip install poetry  (or: pipx install poetry)

swag    — needed for 1 repo (platform/auth, Go API docs)
          Install: go install github.com/swaggo/swag/cmd/swag@latest

Want to install them now, or continue without? (I'll fall back to
existing specs for repos that need the missing tools.)
```

**Wait for the user's response.** If they install the tools, re-check availability and proceed with runtime extraction. If they decline, proceed with fallbacks — do not block.

## 4. Early Skip Decision

If runtime extraction is structurally impossible for a repo AND the user declined to install tools, skip to tier 3/4 without burning attempts:
- Go repo but no `go` or `swag` installed → skip to tier 3
- Java/Kotlin repo but no JVM → skip to tier 3
- Broken venv AND no `uv` or `poetry` to fix it → skip to tier 3
- Report: "Skipping runtime extraction for platform/auth — Go project, `swag` not installed."

## 5. Fix Broken Venvs (if tools available)

**Preferred: `poetry install`** — if poetry is available, this is the most reliable path. It reads pyproject.toml and poetry.lock, installs everything (including transitive deps), and handles private registries if configured:
```bash
cd <app-dir> && poetry install --no-root
```

**Fallback: `uv`** — if poetry is not available but uv is:
```bash
# uv available as command:
cd <app-dir> && uv venv --python 3.13 --clear
uv pip install --python .venv/bin/python -r <(python3 -c "
import re
with open('poetry.lock') as f:
    content = f.read()
pkgs = re.findall(r'\[\[package\]\]\nname = \"(.+?)\"\nversion = \"(.+?)\"', content)
for name, ver in pkgs:
    if name not in ('private-pkg-1', 'private-pkg-2'):  # skip private packages
        print(f'{name}=={ver}')
")

# uv available only as module:
python3 -m uv venv --python 3.13 --clear
python3 -m uv pip install --python .venv/bin/python <packages>
```
**Important:** Skip private/internal packages during pip install — they'll be handled by stubs. To identify private packages, look for packages that fail to resolve from PyPI or that reference internal registries in `pyproject.toml`.

## 6. Determine the Run Command

Based on what's available, choose the best way to execute Python in the project's environment:
- **`poetry run python`** — best option. Poetry activates the correct venv and sets up the environment. Use this when poetry is available.
- **`.venv/bin/python`** — good option. Direct venv access. Use when poetry is not available but the venv is healthy (or was just fixed).
- **`uv run python`** — works when uv manages the project.
- **bare `python3`** — last resort. Almost never works for projects with dependencies.
