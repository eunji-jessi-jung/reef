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

Only after ALL five interactions are complete, proceed to automated steps (5-7).

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
- ~10-15 min, ~50-80k tokens depending on codebase size
- Output: draft artifacts + question bank in plain markdown
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

Ask: "Could you give a brief introduction of what this reef covers? For example: 'CSG data ecosystem — 4 services for cancer screening data management' or 'our payments platform.'"

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

After scaffolding, mention: "If you have existing docs (architecture diagrams, SRS, PRDs, design docs), you can drop them into `sources/raw/` inside the reef directory. These give the snorkel pass richer context to work with. You can also use `/reef:feed` later to add documents."

---

## Step 6 — Index

Report: "Indexing source files..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <resolved-reef-path>
```

Report results: files indexed per source, total count. If a source fails, warn and continue.

---

## Step 7 — Auto-trigger snorkel

Report: "Reef is set up. Starting discovery..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Reef initialized: <name> covering <sources>." --reef <resolved-reef-path>
```

Now execute the full `/reef:snorkel` skill. Read `/Users/jessi/Projects/seaof-ai/reef/skills/snorkel/SKILL.md` and follow its instructions from the beginning. Snorkel handles everything from here: extraction, service grouping, question generation, and artifact creation.

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration: "Scaffolding the reef...", "Indexing source files..."
- No emojis. No exclamation marks.
- Fast and automated. The user answered three questions (name, description, location+sources) and confirmed the source list. After that, do not ask for input until snorkel takes over.

---

## Error Handling

- `reef.py init` fails: report error. Common causes: directory exists, permissions.
- `reef.py index` fails for a source: warn, skip, continue with others.
- Source path does not exist: warn the user, do not include it in project.json.
- If snorkel fails mid-way: whatever artifacts were written remain on disk. The user can run `/reef:snorkel` again.
