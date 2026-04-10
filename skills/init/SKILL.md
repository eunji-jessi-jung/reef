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

**Sources:** "What codebases does it cover? Give me the paths."

Accept one or more paths. For each path:

1. **Verify it exists.** If not, warn and skip.
2. **Check if it is a git repo** (has `.git/` inside). If yes, use it directly.
3. **If it is NOT a git repo**, look one level down for subdirectories that contain `.git/`. If found, use those as the actual sources instead of the parent. Report: "Found N git repos inside {path}: {repo-a}, {repo-b}, ..."
4. **If no .git found at either level**, use the path as-is but warn: "No git repo detected at {path} — using it as a plain directory source."

Then:
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
   - Read the 2-level directory tree
   - Read README.md if present
   - Identify entry points, routers, models, config, tests
   - Note the tech stack
3. Adapt the baseline questions to what you found. For each source, generate 8-15 specific questions. The questions should be:
   - **Concrete, not generic.** Instead of "What are the core entities?", write "What are the core entities in service-a and how do Study, Case, and Image relate?" if you see those model names.
   - **Answerable from code.** Every question should be something Claude can investigate by reading source files. Skip questions about ops/monitoring/team structure — those need human input and belong in scuba.
   - **Ordered by discovery priority:** System boundaries first, then data model, then behavior, then cross-system contracts.

4. For multi-source reefs, add cross-system questions:
   - "What data flows from {source-a} to {source-b}?"
   - "What contracts exist between {source-a} and {source-b}?"
   - "Where do {source-a} and {source-b} share entities or schemas?"

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
