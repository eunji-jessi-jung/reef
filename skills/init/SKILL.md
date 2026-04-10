---
description: "Bootstrap a new reef wiki from your codebase"
---

# reef:init

Bootstrap a new reef and immediately start discovering knowledge. The user answers three questions (name, location, sources), then reef handles everything: scaffold, index, auto-generate discovery questions, and run a snorkel pass. By the end, the user has draft artifacts and a question bank without having to think about either upfront.

---

## Context Loading

Read these reference files before starting:

1. `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md` — ID conventions and artifact types.
2. `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md` — voice and personality. Use the Curious Researcher voice throughout.

---

## Step 0 — Welcome

Before anything else, orient the user. This may be their first time hearing about Reef.

Print the following (adapt naturally, but hit these points):

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
- 3 quick questions from you, then full automation
- ~10-15 min, ~50-80k tokens depending on codebase size
- Output: draft artifacts + question bank in plain markdown
- After init: /reef:scuba to deepen, /reef:feed to add docs
```

Do not ask for confirmation. Just present this and move to Step 1.

---

## Step 1 — Check for an existing reef

Look for a `.reef/` directory in the current working directory and in any path the user provides.

- If `.reef/` exists: read `.reef/project.json` and report what you find. Ask: "This directory already has a reef. Continue building on it, or start fresh?"
- If reset: delete the existing reef directories and proceed.
- If continue: suggest `/reef:snorkel` or `/reef:scuba` instead and exit.
- If no reef exists: proceed to Step 2.

---

## Step 2 — Three questions, then go

Ask these one at a time. Keep it tight.

**Name:** "What should this reef be called?" — becomes the directory name (e.g., `my-reef`, `payments-reef`).

**Location:** "Where should it live?" — default: new directory in cwd. User can specify any path.

**Sources:** Auto-discover git repos in the current working directory. Scan two levels deep for directories containing `.git/`.

Present what you find:

> "I found N codebases in {cwd}:
>
> - repo-a
> - repo-b
> - repo-c
> - ...
>
> Cover all of them, or exclude some?"

The user either confirms ("all" / "yes" / "looks right") or excludes ("skip repo-c and repo-d"). Apply their answer.

- If no git repos are found in cwd, ask: "No codebases found here. What directory should I scan?"
- Multiple sources: "Good — that is how Reef discovers cross-system contracts."
- Single source: "You can add more later."

That is it for user input. Everything from here is automated.

---

## Step 3 — Scaffold

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

After scaffolding, mention: "If you have existing docs (architecture diagrams, SRS, PRDs, design docs), you can drop them into `sources/raw/` inside the reef directory. These give the snorkel pass richer context to work with. You can also use `/reef:feed` later to add documents."

---

## Step 4 — Index

Report: "Indexing source files..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <resolved-reef-path>
```

Report results: files indexed per source, total count. If a source fails, warn and continue.

---

## Step 5 — Auto-generate discovery questions

This is the critical step. After indexing, generate a tailored question bank for each source based on what the structural scan reveals. These questions steer snorkel and later become the `/reef:test` north star.

**How to generate questions:**

1. Read `/Users/jessi/Projects/seaof-ai/reef/references/understanding-template.md` — the 33 baseline questions across 7 phases.

2. For each source, do a quick structural scan:
   - Read `CLAUDE.md` first (if present), then `README.md` — these are the richest signal for what the repo is, which service or product it belongs to, and how it fits into the larger system. Extract the service/product identity.
   - Read the 2-level directory tree
   - Identify entry points, routers, models, config, tests
   - Note the tech stack

3. **Infer service groupings.** Try to group repos into services using these signals, in order:
   - **Explicit identity** from CLAUDE.md/README.md (e.g., "authentication service for the CTL ecosystem")
   - **Shared name prefixes or postfixes** (e.g., `ctl-authenticator` + `ctl-data-server` + `ctl-office`, or `ai-platform-foundation` + `ai-platform-foundation-admin`)
   - **Acronym expansion** — check if a repo prefix is an acronym of another repo's full name (e.g., `rdp-prefect-gateway` prefix "rdp" matches "research-data-pipeline" initials R.D.P.). This is a strong grouping signal.
   - **Shared infrastructure** references (e.g., same Keycloak realm, same database, same API gateway, both using Prefect)

   Then present your best guess as a table and ask the user to confirm or correct — this is the **one** question you ask between indexing and snorkel:

   > I found N repos. I think they group like this:
   >
   > | Service          | Repos                                    |
   > |------------------|------------------------------------------|
   > | {best guess}     | repo-1, repo-2                           |
   > | {best guess}     | repo-3, repo-4, repo-5                   |
   > | ?                | repo-6 (no clear signal)                 |
   >
   > Any corrections?

   The user responds in natural language (e.g., "Case Curator is actually called CDM. repo-6 belongs to CTL. The last two are RDP."). Parse their corrections, apply them, and save the service groupings to `.reef/project.json` under a `services` field:
   ```json
   {
     "services": [
       { "name": "CTL", "full_name": "Closing the Loop", "sources": ["ctl-authenticator", "ctl-data-server", "ctl-office", "radiology-annotation-frontend"] }
     ]
   }
   ```

4. Adapt the baseline questions to what you found. For each source, generate 8-15 specific questions. The questions should be:
   - **Concrete, not generic.** Instead of "What are the core entities?", write "What are the core entities in service-a and how do Study, Case, and Image relate?" if you see those model names.
   - **Answerable from code.** Every question should be something Claude can investigate by reading source files. Skip questions about ops/monitoring/team structure — those need human input and belong in scuba.
   - **Ordered by discovery priority:** System boundaries first, then data model, then behavior, then cross-system contracts.

5. For multi-source reefs, add cross-system questions. Use the service groupings from step 3:
   - **Within a service** (repos that belong to the same product): "How do {repo-a} and {repo-b} divide responsibilities within {service}?" / "What is the frontend-backend contract between {repo-a} and {repo-b}?"
   - **Across services**: "What data flows from {service-a} to {service-b}?" / "What contracts exist between {service-a} and {service-b}?" / "Where do {service-a} and {service-b} share entities or schemas?"

**Question format:**

Write to `.reef/questions.json`:
```json
{
  "questions": [
    {
      "id": "Q-001",
      "text": "What are the system boundaries and external dependencies of service-a?",
      "source": "service-a",
      "phase": "orientation",
      "added": "2026-04-10",
      "status": "unanswered"
    }
  ]
}
```

Report: "Generated N discovery questions across M sources. These will steer the snorkel pass."

Show the user the questions briefly — a numbered list, grouped by source. Do not ask for approval. They can refine later.

---

## Step 6 — Auto-trigger snorkel

Report: "Starting the snorkel pass..."

Now execute the full `/reef:snorkel` skill. Read `/Users/jessi/Projects/seaof-ai/reef/skills/snorkel/SKILL.md` and follow its instructions from Step 2 onward (skip Step 1 since the index is already fresh).

The snorkel pass will use the question bank you just generated to produce richer, more directed artifacts.

---

## Step 7 — Log

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Reef initialized: <name> covering <sources>. Generated <N> questions, <M> draft artifacts." --reef <resolved-reef-path>
```

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration: "Scaffolding the reef...", "Indexing source files...", "Generating discovery questions..."
- No emojis. No exclamation marks.
- Fast and automated. The user answered three questions and now watches things happen. Do not ask for input during steps 3-6.
- When reporting the question bank, be brief. The user wants to see artifacts, not a wall of questions.

---

## Error Handling

- `reef.py init` fails: report error. Common causes: directory exists, permissions.
- `reef.py index` fails for a source: warn, skip, continue with others.
- Source path does not exist: warn the user, do not include it in project.json.
- If snorkel fails mid-way: whatever artifacts were written remain on disk. The user can run `/reef:snorkel` again.
