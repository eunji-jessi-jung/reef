# Reef User Guide

Step-by-step walkthrough of the full Reef workflow.

## The Flow

```
/reef:init  →  snorkel + source (automatic)  →  /reef:scuba  →  /reef:deep
                                                                     ↓
                           /reef:update  ←  code changes  ←  living reef
```

## 1. Initialize — `/reef:init`

Creates the reef structure and runs first-pass discovery.

**What you do:**
- Answer 3 questions: name, description, source locations
- Confirm the detected service groupings
- Approve the discovery plan

**What Reef does (automated after your answers):**
- Scaffolds the directory structure
- Indexes all source files
- Runs **snorkel** (structural scan → draft artifacts) and **source** (API specs + ERDs) in parallel
- Generates a question bank for later deepening

**Time:** ~10-20 min depending on codebase size. No input needed after you approve the plan.

**Tools:** Source extraction may prompt you to install project build tools (poetry, swag, etc.). These are your project's own tools — you would need them to develop in the repo anyway. If you decline, Reef falls back to reading code directly, but the resulting specs may be less complete.

## 2. Deepen — `/reef:scuba`

Interactive, question-driven knowledge capture. This is where most real knowledge gets added.

**What you do:**
- Answer questions one at a time about your domain
- Correct anything Reef got wrong
- Provide context that code alone cannot reveal (decisions, ownership, history)

**What Reef does:**
- Upgrades draft artifacts using the full API specs and ERDs from source extraction
- Asks targeted questions based on gaps in existing artifacts
- Creates or updates artifacts as knowledge accumulates
- Always asks "What did I get wrong?" after writing

**When to use:** After init. This is the main working session. Run it as many times as you want — each session deepens the reef further.

## 3. Deep Dive — `/reef:deep`

Line-by-line code tracing for critical systems. Reserve for areas where shallow reading misses real behavior.

**When to use:** After scuba has established the broad picture. Use for systems where getting details wrong has consequences — auth flows, data pipelines, billing logic.

## 4. Maintain — `/reef:update`

Keeps the reef fresh as code changes.

**What it does:**
1. Re-extracts API specs and ERDs from current code (uses cached recipes — fast)
2. Re-indexes source files
3. Detects what changed since last update
4. Walks you through updating affected artifacts

**When to use:** After significant code changes — new endpoints, schema migrations, service additions. Run periodically (weekly, after sprints, before onboarding).

## 5. Check Health — `/reef:health`

Read-only report. Shows coverage, freshness, and validation issues without changing anything.

**When to use:** Before a scuba session (to see where gaps are), before onboarding someone, or to check if an update is needed.

## Artifact Types

| Type | Prefix | Answers |
|------|--------|---------|
| System | SYS- | What does this service do? |
| Schema | SCH- | What does this data mean? |
| API | API- | What can I call? |
| Process | PROC- | What happens when...? |
| Decision | DEC- | Why was it built this way? |
| Glossary | GLOSSARY- | What does this term mean? |
| Contract | CON- | What do these systems agree on? |
| Risk | RISK- | What could go wrong? |

## Tips

- **Start small.** One scuba session deepening 2-3 artifacts is better than trying to cover everything at once.
- **Correct early.** If Reef gets a fact wrong, correct it immediately. Wrong facts compound — right facts compound too.
- **Add your own docs.** Drop architecture docs, design specs, or runbooks into `sources/raw/` — scuba will use them when deepening artifacts. Especially useful for questions that code alone can't answer.
- **Open in Obsidian.** Artifacts are wikilinked with `[[artifact-id]]` syntax. Open the reef directory as an Obsidian vault to see the full knowledge graph. Enable Graph View and Dataview plugins.
- **Run update after deploys.** API specs and schemas drift silently. A 2-minute update run catches drift before it becomes tribal knowledge.
- **One reef per team.** Services that don't talk to each other belong in separate reefs.
