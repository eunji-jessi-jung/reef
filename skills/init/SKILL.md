---
description: "Bootstrap a new reef wiki from your codebase"
---

# reef:init

## MANDATORY — Read this first

You MUST complete these interactions with the user IN ORDER. Do NOT skip any. Do NOT combine them into one message. Each requires a separate user response.

1. **Print the welcome** (Step 0) — the ASCII art and orientation block. This is your FIRST output.
2. **Ask the name** (Step 2) — "What should this reef be called?" STOP and wait.
3. **Ask what it covers** (Step 3) — "Could you give a brief introduction of what this reef covers?" STOP and wait.
4. **Ask location and sources** (Step 4) — "Where should the reef live? And where are the codebases?" STOP and wait.
5. **Scan for repos** — Run `find <directory> -name .git -type d 2>/dev/null | sed 's|/.git||' | sort` — this is the ONLY correct way to find repos. Do NOT use ls, glob, or manual directory listing. Check each repo for monorepo signals and expand sub-projects if detected. Present results as a **numbered list** and ask user to select by number.
6. **Scaffold and index** (Steps 5-6) — automated, no user input.
7. **Service grouping** (Step 7) — present best guess as table, ask user to correct. STOP and wait.
8. **Discovery plan** (Step 8) — show what snorkel+source will do, estimated time/tokens. STOP and wait for confirmation.

Only after ALL interactions are complete, launch snorkel+source (Step 9).

---

## Step 0 — Welcome

**This must be your first output.** Before reading any other files, before doing anything else, print the following to the user:

```
    ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

                ~ reef ~
     structured knowledge from source code

    source code  →  questions  →  artifacts
         ↑                            |
         └────── update cycle ────────┘
```

Then print a compact orientation block:

```
- Best with Opus (Sonnet works, but Opus finds richer connections)
- Built for codebases with services, data, and interfaces
  (Not for: pure mobile, game engines, firmware, ML notebooks)
- Sweet spot: 3-15 repos that form one domain or team ecosystem
  (Bigger org? One reef per team — not one reef for everything)
- 3 quick questions from you, then full automation

Estimated cost (one-time):
  3-5 repos   ~10 min   ~80-100k tokens   Pro plan works well
  6-10 repos  ~15 min   ~150-200k tokens   Pro plan, may hit rate limits
  10-15 repos ~20 min   ~250-300k tokens   Max recommended
  (On API: roughly $3-5 for small, $10-20 for large)

- Output: draft artifacts + API specs + ERDs + question bank
- After init: /reef:scuba to deepen artifacts with domain knowledge
- Anytime: /reef:help for skill list, reef status, and what to do next
```

Do not ask for confirmation. Just present this and move to Step 1.

---

## Context Loading

Before proceeding past Step 0, read these reference files:

1. `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md` — ID conventions and artifact types.
2. `${CLAUDE_PLUGIN_ROOT}/references/methodology.md` — voice and personality. Use the Curious Researcher voice throughout.

---

## Step 1 — Check for an existing reef

Look for a `.reef/` directory in **both** the current working directory **and** its immediate child directories (one level down). Run: `find . -maxdepth 2 -name .reef -type d 2>/dev/null`

Also check any path the user explicitly provides.

- If one `.reef/` is found: read its `project.json` and check the reef's current state:
  - Count artifacts in `artifacts/`
  - Check if `sources/apis/` and `sources/schemas/` have extracted specs
  - Check if `.reef/scuba-manifest.json` exists

  Then present a status-aware recommendation:

  ```
  Found an existing reef at `{path}`: "{project name}"
    Sources:    N repos configured
    Artifacts:  N (SYS: a, SCH: b, API: c, CON: d, PROC: e, ...)
    API specs:  N extracted
    Schemas:    N extracted

  Options:
    1. Continue building — {recommendation based on state}
    2. Start a new reef — different codebases, different domain (keeps this one intact)
    3. Start fresh — delete everything and re-init from scratch
  ```

  If the user picks option 2: proceed to Step 2 as if no reef exists. The new reef will be created in a separate directory with a different name. The existing reef is left untouched.

  State-based recommendations:
  - No artifacts, no specs → "Run `/reef:snorkel` and `/reef:source` to start discovery"
  - Artifacts exist but no specs → "Run `/reef:source` to extract API specs and ERDs"
  - Artifacts + specs but no PROC-/DEC- → "Run `/reef:scuba` to deepen"
  - Scuba manifest exists with incomplete items → "Run `/reef:scuba` to continue Phase 1 (N/M artifacts remaining)"
  - Everything looks complete → "Reef looks healthy. Try `/reef:health` for a status check or `/reef:update` to refresh stale artifacts"

- If multiple `.reef/` directories found: list them with the same status summary for each. Ask which one to use, or offer to start fresh.
- If start fresh: delete the existing reef directories and proceed to Step 2.
- If no reef exists anywhere: proceed to Step 2.

---

## Step 2 — Ask the name

Ask: "What should this reef be called?" — becomes the directory name (e.g., `my-reef`, `payments-reef`).

Wait for the user's answer before proceeding.

---

## Step 3 — Ask what it covers

Ask:

"How would you describe this project to a new teammate in a sentence or two?

Example: 'It's our e-commerce backend — about 6 services handling orders, payments, and fulfillment.'"

Save the user's answer to `.reef/project.json` under a `description` field later during scaffolding. This front-loads domain context (service names, ecosystem, product area) so service grouping and question generation are more accurate.

Wait for the user's answer before proceeding.

---

## Step 4 — Ask location and sources

Ask both together: "Where should the reef live? (default: new directory here) And where are the codebases I should scan?"

Default location: new directory in cwd named after the reef. Default scan directory: current working directory. The user can override either.

**Sources:** Once the user provides a scan directory, you MUST use this exact command to find repos:

```bash
find <directory> -name .git -type d 2>/dev/null | sed 's|/.git||' | sort
```

Do NOT use ls, glob, or manually list directories. The find command is the ONLY reliable way to discover all git repos at any depth.

**Monorepo detection:** After finding git repos, check each one for monorepo signals. A repo is a monorepo if it contains ANY of:

- `pnpm-workspace.yaml`
- `nx.json`
- `turbo.json`
- `lerna.json`
- `package.json` with a `"workspaces"` field
- `Cargo.toml` with a `[workspace]` section
- `go.work` file
- A `packages/`, `services/`, or `apps/` directory containing 2+ subdirectories with their own `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, or `setup.py`

If monorepo signals are found:
1. Discover sub-projects by reading the workspace config (e.g., pnpm-workspace.yaml `packages` globs, nx.json projects, turbo.json, Cargo workspace members) or listing immediate subdirectories of `packages/`, `services/`, or `apps/`.
2. List each sub-project as a separate source in the numbered list, indented under the parent repo, e.g.:
   ```
    3. my-monorepo/ (monorepo — 4 sub-projects detected)
       3a. my-monorepo/services/payments
       3b. my-monorepo/services/catalog
       3c. my-monorepo/packages/shared-auth
       3d. my-monorepo/apps/admin-ui
   ```
3. The user can select sub-projects individually (e.g., "3a, 3b" or "all of 3" or "3 except 3c").
4. Selected sub-projects are recorded as **sub-apps within the parent repo's source entry**, not as separate top-level sources. The parent repo is the source; sub-projects are sub-apps within it. This matters for service grouping (Step 7) — sub-apps from the same repo always belong to the same service.

If no monorepo signals are found, treat the repo as a single source as usual.

**Present as a numbered list** so the user can select by number:

> I found N codebases under {directory}:
>
>  1. repo-a
>  2. repo-b
>  3. repo-c
>  ...
>
> Which ones? (e.g., "all", "1,3,5", "all except 2")

The user responds with numbers, ranges, or exclusions. Apply their answer.

- If no git repos are found, ask: "No codebases found there. Try a different directory?"
- Multiple sources: "Good — that is how Reef discovers cross-system contracts."
- Single source: "You can add more later."

**After selection, offer to pull latest:**

> "Want me to `git pull` each repo to make sure they're up to date? (yes / no — I'll pull them myself / skip)"

If yes: run `git -C <repo-path> pull` for each selected repo. Report results briefly ("3/3 up to date" or "repo-a: 5 commits pulled, repo-b: up to date"). If a pull fails (uncommitted changes, auth issue), warn and continue with the stale copy.

If no or skip: move on.

That is it for user input. Everything from here is automated.

---

## Step 5 — Scaffold

Report: "Scaffolding the reef..."

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py init <resolved-reef-path>
```

Update `.reef/project.json` with the source paths:
```json
{
  "sources": [
    { "name": "service-a", "path": "/absolute/path/to/service-a" }
  ]
}
```

Read the existing project.json first, then update — do not overwrite other fields.

Do not explain `sources/context/` here — it goes by too fast and gets buried. Snorkel's wrap-up is the better place to suggest adding docs, after the user has seen artifacts and knows what gaps exist.

---

## Step 6 — Index

Report: "Indexing source files..."

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index --reef <resolved-reef-path>
```

Report results: files indexed per source, total count. If a source fails, warn and continue.

---

## Step 7 — Infer service groupings

Read `CLAUDE.md` first (if present), then `README.md` for each source. Extract service/product identity. Also use the reef description from `.reef/project.json` as context.

Try to group repos into services using these signals, in order:
- **Monorepo sub-apps always stay together.** Sub-projects from the same parent repo are sub-apps of one service, never separate services. The service name comes from the parent repo. The sub-apps become artifact-level distinctions (e.g., SCH-PLATFORM-AUTHZ, SCH-PLATFORM-LINEAGE), not service-level ones.
- **Explicit identity** from CLAUDE.md/README.md (e.g., "authentication service for the payments ecosystem")
- **Shared name prefixes or postfixes** (e.g., `pay-gateway` + `pay-ledger` + `pay-admin`, or `order-service` + `order-worker`)
- **Acronym expansion** — check if a repo prefix is an acronym of another repo's full name (e.g., `ofs-worker` prefix "ofs" matches "order-fulfillment-service" initials O.F.S.)
- **Shared infrastructure** references (e.g., same auth provider, same database, same message broker)

Present your best guess as a table — include both service names and inferred one-line descriptions. Descriptions front-load richer context for snorkel; service names alone are not enough to generate good artifacts.

> I think these repos group like this:
>
> | Service          | Description                              | Repos                                    |
> |------------------|------------------------------------------|------------------------------------------|
> | {best guess}     | {inferred description}                   | repo-1, repo-2                           |
> | {best guess}     | {inferred description}                   | repo-3, repo-4, repo-5                   |
> | ?                | {unclear}                                | repo-6 (no clear signal)                 |
>
> Any corrections — names, descriptions, or groupings?

The user responds in natural language. Parse their corrections, apply them, and save to `.reef/project.json` under a `services` field:
```json
{
  "services": [
    { "name": "Payments", "full_name": "Payments Platform", "description": "Payment processing, gateway integration, and ledger management", "sources": ["pay-gateway", "pay-ledger", "pay-admin", "checkout-frontend"] },
    { "name": "Platform", "full_name": "Data-AI Platform", "description": "Centralized identity, authorization, and data lineage", "sources": ["platform-monorepo"], "sub_apps": ["authz-api", "data-lineage", "shared-auth"] }
  ]
}
```

For monorepo services, the `sub_apps` field lists the sub-projects within the parent repo. Artifacts use the sub-app name as a suffix (e.g., `SCH-PLATFORM-AUTHZ`, `API-PLATFORM-DATA-LINEAGE`).

---

## Step 8 — Present discovery plan and confirm

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Reef initialized: <name> covering <sources>." --reef <resolved-reef-path>
```

Now present a discovery plan to the user. Tailor the details based on what was found during indexing — number of sources, detected frameworks, file counts. The explanation must be **concrete and scannable** — bullet lists, not prose. The user needs to understand what will happen, what tools are involved, and what they might be asked to do.

```
Reef is set up. Here is what happens next.

Two things will run in parallel — both fully automated:

**1. Snorkel** (structural discovery)
- Reads directory trees, READMEs, and key source files in each repo
- Generates discovery questions about architecture and design
- Produces 3-6 draft artifacts per service (SYS-, SCH-, API-, CON-)
- Builds the question bank for later deepening with /reef:scuba

**2. Source** (API specs + data model extraction)
- Detects tech stacks in each repo (frameworks, ORMs, package managers)
- Extracts live API specs by importing your app at runtime
  - For Python (FastAPI, Django, Flask): runs `app.openapi()` via your project's venv
  - For Go (gin/echo/chi): uses `swag` to generate from annotations
  - For Node (NestJS, Express): uses Swagger module extraction
- Extracts entity-relationship diagrams from ORM models (SQLAlchemy, Prisma, etc.)
- Caches successful recipes so future re-extractions are instant

**About tools:**
- Source extraction uses your project's own build tools (poetry, uv, go, swag, etc.)
- If a tool is missing, you will be asked whether to install it
  - Example: `pip install poetry` or `go install github.com/swaggo/swag/cmd/swag@latest`
- If you decline, Reef falls back to copying existing spec files or reading code directly
  - Fallback specs may be **out of date** — Reef will flag this with a staleness warning

**No input needed** unless a missing tool prompt appears.

Estimated time: ~10-15 minutes for <N> repos
Estimated tokens: ~50-80k (scales with codebase size)

Ready to start?
```

Replace `<N>` with the actual source count.

**Wait for the user to confirm before proceeding.** The user might want to adjust scope, take a break, or run it later.

---

## Step 9 — Launch snorkel and source

After the user confirms, report: "Starting discovery and source extraction..."

Launch **two skills in parallel**:

1. **Snorkel** — Read `${CLAUDE_PLUGIN_ROOT}/skills/snorkel/SKILL.md` and follow its instructions. Produces structural draft artifacts.
2. **Source** — Read `${CLAUDE_PLUGIN_ROOT}/skills/source/SKILL.md` and follow its instructions. Extracts full API specs and ERDs.

Use the Agent tool to run these concurrently. Both are fully automated — no user input needed.

When both complete:

1. **Run the snorkel audit** to check for missing mandatory artifacts:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py audit --reef <reef-root>
   ```
   If the audit reports missing artifacts, launch targeted agents to fill the gaps. Each missing artifact is independent — launch one agent per gap, all in a single message. The agents should read the snorkel skill's Step 4 for artifact format, then generate the specific missing artifact.

2. **Run the health report** to give the user an immediate visual summary of coverage:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff --reef <reef-root>
   ```
   Render the health report using the same Unicode box-drawing format defined in the snorkel skill's wrap-up step. This is the payoff moment after a long wait — the user needs the visual satisfaction of seeing coverage bars and artifact counts.

3. **Summarize** results from both agents (artifacts created, API specs extracted, questions answered).

4. **Suggest next steps:** `/reef:scuba` to deepen artifacts, `/reef:test` to check coverage. Mention that artifacts are wikilinked and can be opened as an Obsidian vault for graph visualization.

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration: "Scaffolding the reef...", "Indexing source files..."
- No emojis. No exclamation marks.
- Fast and automated. The user answered questions (name, description, location+sources), confirmed sources, corrected service groupings, and approved the discovery plan. After that, do not ask for input — snorkel and source run unattended.

---

## Error Handling

- `reef.py init` fails: report error. Common causes: directory exists, permissions.
- `reef.py index` fails for a source: warn, skip, continue with others.
- Source path does not exist: warn the user, do not include it in project.json.
- If snorkel fails mid-way: whatever artifacts were written remain on disk. The user can run `/reef:snorkel` again.
