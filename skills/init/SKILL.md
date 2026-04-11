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
5. **Scan for repos** — Run `find <directory> -name .git -type d 2>/dev/null | sed 's|/.git||' | sort` — this is the ONLY correct way to find repos. Do NOT use ls, glob, or manual directory listing. Present results and ask user to confirm.
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
- Sweet spot: 3-15 repos that form one domain or team ecosystem
  (Bigger org? One reef per team — not one reef for everything)
- 3 quick questions from you, then full automation

Estimated cost (one-time):
  3-5 repos   ~10 min   ~80-100k tokens   Pro plan works well
  6-10 repos  ~15 min   ~150-200k tokens   Pro plan, may hit rate limits
  10-15 repos ~20 min   ~250-300k tokens   Max recommended
  (On API: roughly $3-5 for small, $10-20 for large)

- Output: draft artifacts + API specs + ERDs + question bank
- After init: /reef:scuba to deepen, /reef:feed to add docs
```

Do not ask for confirmation. Just present this and move to Step 1.

---

## Context Loading

Before proceeding past Step 0, read these reference files:

1. `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md` — ID conventions and artifact types.
2. `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md` — voice and personality. Use the Curious Researcher voice throughout.

---

## Step 1 — Check for an existing reef

Look for a `.reef/` directory in the current working directory and in any path the user provides.

- If `.reef/` exists: read `.reef/project.json` and report what you find. Ask: "This directory already has a reef. Continue building on it, or start fresh?"
- If reset: delete the existing reef directories and proceed.
- If continue: suggest `/reef:snorkel` or `/reef:scuba` instead and exit.
- If no reef exists: proceed to Step 2.

---

## Step 2 — Ask the name

Ask: "What should this reef be called?" — becomes the directory name (e.g., `my-reef`, `payments-reef`).

Wait for the user's answer before proceeding.

---

## Step 3 — Ask what it covers

Ask:

"Could you give a brief introduction of what this reef covers? Three things help:

- **Domain** — what area (e.g., payments, infrastructure, data pipeline)
- **Purpose** — what it does in one sentence
- **Scale** — roughly how many services

Example: 'e-commerce platform — 6 services for order processing, payments, and fulfillment'"

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

Present what you find:

> "I found N codebases under {directory}:
>
> - repo-a
> - repo-b
> - repo-c
> - ...
>
> Cover all of them, or exclude some?"

The user either confirms ("all" / "yes" / "looks right") or excludes ("skip repo-c and repo-d"). Apply their answer.

- If no git repos are found, ask: "No codebases found there. Try a different directory?"
- Multiple sources: "Good — that is how Reef discovers cross-system contracts."
- Single source: "You can add more later."

That is it for user input. Everything from here is automated.

---

## Step 5 — Scaffold

Report: "Scaffolding the reef..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py init <resolved-reef-path>
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

Do not mention `sources/raw/` or `/reef:feed` here — it goes by too fast and gets buried. Snorkel's wrap-up is the better place to suggest feeding docs, after the user has seen artifacts and knows what gaps exist.

---

## Step 6 — Index

Report: "Indexing source files..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <resolved-reef-path>
```

Report results: files indexed per source, total count. If a source fails, warn and continue.

---

## Step 7 — Infer service groupings

Read `CLAUDE.md` first (if present), then `README.md` for each source. Extract service/product identity. Also use the reef description from `.reef/project.json` as context.

Try to group repos into services using these signals, in order:
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
    { "name": "Payments", "full_name": "Payments Platform", "description": "Payment processing, gateway integration, and ledger management", "sources": ["pay-gateway", "pay-ledger", "pay-admin", "checkout-frontend"] }
  ]
}
```

---

## Step 8 — Present discovery plan and confirm

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Reef initialized: <name> covering <sources>." --reef <resolved-reef-path>
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

1. **Snorkel** — Read `/Users/jessi/Projects/seaof-ai/reef/skills/snorkel/SKILL.md` and follow its instructions. Produces structural draft artifacts.
2. **Source** — Read `/Users/jessi/Projects/seaof-ai/reef/skills/source/SKILL.md` and follow its instructions. Extracts full API specs and ERDs.

Use the Agent tool to run these concurrently. Both are fully automated — no user input needed. When both complete, summarize results from both and suggest `/reef:scuba` as the next step.

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
