---
description: "Show available skills, reef status, and recommended next action"
---

# /reef:help

Show the user what reef can do, where they are, and what to do next.

---

## Step 1 — Skill reference

Print this skill list:

```
reef skills:

  Setup
    /reef:init        Bootstrap a new reef from your codebase

  Discovery (progressive depth)
    /reef:snorkel     Auto-discover draft artifacts from source code
    /reef:source      Extract full API specs and ERDs from source repos
    /reef:scuba       Deepen knowledge — automated analysis + Socratic Q&A
    /reef:deep        Exhaustive line-by-line tracing of specific areas

  Maintenance
    /reef:update      Pull sources, detect changes, generate update report for review
    /reef:artifact    Explore a topic, capture knowledge, or update an artifact
    /reef:health      Validate artifacts and report freshness
    /reef:test        Test the reef against your question bank

  Help
    /reef:help        This screen

Tip: Artifacts are wikilinked — open the reef directory as an Obsidian vault for graph visualization.
Tip: Have PRDs, SOPs, meeting notes, or design docs? Drop them in sources/context/ and scuba will use them.
```

---

## Step 2 — Reef status

Look for a `.reef/` directory in cwd or parent directories.

**If no reef found:**

```
No reef detected in this directory.
Run /reef:init to get started.
```

Stop here. Do not proceed to Step 3.

**If reef found:** Read `.reef/project.json`, scan `artifacts/`, `sources/apis/`, `sources/schemas/`, and `.reef/scuba-manifest.json` (if exists). Present a compact status:

```
Reef: {name} ({path})

  Artifacts:  N total
    SYS-: a    SCH-: b    API-: c    CON-: d
    PROC-: e   DEC-: f    GLOSSARY-: g   RISK-: h    PAT-: i

  Sources:
    API specs: N extracted (services: {list})
    Schemas:   N extracted (services: {list})

  Questions:  N total, M answered, K unanswered

  Scuba manifest: {not found | N/M completed, K remaining}
```

### 2.5 — New context alert

Scan `sources/context/` and `sources/raw/` for files not referenced by any artifact's `sources` field. If new unreferenced files exist, append an alert to the status:

```
  New context:  3 files added since last update
    sources/context/requirements/order-fulfillment-srd.pdf
    sources/context/meetings/2026-04-10-platform-knowledge-share.md
    sources/raw/data-flow-diagram.png

  I noticed you added some context. Want to explore it together?
  Run /reef:update to fold it into existing artifacts, or
  /reef:deep to use it as a starting point for exploration.
```

If no new context files, skip this section entirely.

---

## Step 3 — Recommended next action

Based on the reef state, recommend actions. Use the first matching rule:

1. **No artifacts and no sources** → "Your reef is scaffolded but empty. Run `/reef:snorkel` to start discovery (or `/reef:init` to re-run the full setup including snorkel+source)."

2. **Artifacts exist but no extracted specs** → "You have draft artifacts but no API specs or ERDs. Run `/reef:source` to extract them — scuba uses these to generate richer artifacts."

3. **Artifacts + specs exist, no PROC-/DEC-/RISK- artifacts** → "Snorkel and source are done. Run `/reef:scuba` to deepen — it will generate entity definitions, lifecycle artifacts, contracts, and pattern analysis."

4. **Scuba manifest exists with remaining items** → "Scuba Phase 1 is partially complete ({N}/{M} artifacts done). Run `/reef:scuba` to continue where you left off."

5. **Scuba manifest complete, unanswered questions remain** → "Phase 1 is done. Run `/reef:scuba` to start Phase 2 — interactive Q&A to fill in what code alone couldn't answer ({K} questions remaining)."

6. **Scuba complete (or mostly complete)** → Show all relevant options:

```
Your reef is active. Here's what you can do:

  /reef:update    — Pull latest code and update stale artifacts
  /reef:artifact  — Explore a topic, capture knowledge, or refine an artifact
  /reef:deep      — Trace critical paths line by line
  /reef:health    — Check coverage and freshness (read-only)
  /reef:test      — Test whether the reef answers your real questions
  /reef:help      — See all available skills
```

Print the recommendation clearly:

```
Suggested next step:
  {recommendation}
```

---

## Rules

- Be fast. This skill should take seconds — read metadata, don't read artifact bodies.
- No emojis. No exclamation marks.
- If the user passes an argument (e.g., `/reef:help scuba`), show the skill reference for just that skill — read its SKILL.md and present a 3-5 line summary of what it does, when to use it, and what it produces.
