# Reef User Guide

Reef builds a structured knowledge wiki from your source code. The AI reads code and does the bookkeeping. You bring domain knowledge and decide what matters. Output is plain markdown, Obsidian-native, local-first.

## Getting Started

### Install

```
/plugin marketplace add eunji-jessi-jung/reef
/plugin install reef@eunji-jessi-jung-reef
```

### Build your first reef

```
/reef:init
```

Reef will ask you three things: a name for the reef, a short description, and where your source repos live. After you answer, it scaffolds the directory and runs two automated passes in parallel:

- **Snorkel** scans code structure and produces draft artifacts
- **Source** extracts API specs and entity-relationship diagrams

This takes 10-20 minutes depending on codebase size. No input needed after you approve the plan.

### Deepen it

```
/reef:scuba
```

This is where most real knowledge gets added. Reef reads your code, cross-references the API specs and ERDs it extracted, and asks you questions that code alone can't answer — why decisions were made, who owns what, what breaks in practice.

You answer questions one at a time. Reef writes and updates artifacts as knowledge accumulates. You can stop anytime and resume later. Each session deepens the reef further.

After scuba, your reef is useful. You don't need to "finish" it.

**No one to ask?** Scuba assumes a domain expert is sitting with you. When nobody is —
the authors left, you arrived last week, or you kicked the run off overnight — pick
owner-absent mode, and finish with:

```
/reef:ask
```

Reef resolves every gap the sources can still settle, then writes the rest to
`.reef/questions-for-owner.md` as a ranked question bank. Each entry says what the answer
would unblock and what has already been checked, so whoever does know can answer in
twenty minutes without redoing the search.

## What you can do with a reef

- **Feed it to dev agents.** Point Claude Code, Cursor, or Copilot at the reef directory as context. Agents with reef artifacts understand your domain, not just your syntax.
- **Onboard teammates.** Open in Obsidian and explore the knowledge graph. Faster ramp-up than reading code cold.
- **Export as docs.** Artifacts are structured markdown with frontmatter. Copy into Confluence, Notion, or a static site.
- **Keep it alive.** `/reef:update` after code changes. Each update costs a fraction of the initial build.

## Skills

Run `/reef:help` to see the full list anytime. Here's the overview:

| Phase | Skill | What it does |
|-------|-------|-------------|
| Build | `/reef:init` | Scaffold + auto-discover |
| Build | `/reef:scuba` | Deepen through Q&A |
| Build | `/reef:deep` | Line-by-line tracing of critical areas |
| Build | `/reef:ask` | Collect open gaps into a question bank for the owner |
| Anytime | `/reef:artifact` | Explore a topic, capture knowledge, or refine an artifact |
| Maintain | `/reef:update` | Pull latest code, detect changes, update artifacts |
| Maintain | `/reef:health` | Coverage and freshness report |
| Validate | `/reef:test` | Test the reef against your question bank |

### `/reef:artifact` — the everyday skill

You don't need to know artifact types or IDs. Just talk naturally:

- *"I want to dig deeper into how split finalization works"* — Reef searches artifacts and source code, proposes where the knowledge belongs.
- *"We should document that the queue uses RabbitMQ"* — Reef finds where this fact fits and writes it.
- *"Update SCH-ORDERS-CORE"* — direct update if you know the artifact.

### `/reef:update` — after code changes

Pulls latest source code, re-extracts specs, and generates an update report showing what changed:
- **Enrichments** — new models or endpoints found for existing artifacts
- **Refreshes** — existing content needs updating
- **New entities** — something that needs a new artifact
- **Orphaned** — source code was removed

You review and approve changes before anything gets written. Reports are persistent — you can pause and resume later.

### `/reef:deep` — for critical systems

Line-by-line code tracing with precise citations. Use after scuba for systems where getting details wrong has consequences: auth flows, data pipelines, billing logic.

### `/reef:ask` — when the expert is missing

Harvests `known_unknowns` from every artifact, resolves the ones that were merely
unfinished work, clusters what is left, and ranks it by what each answer would unblock.
Output is `.reef/questions-for-owner.md`.

The four parts of every entry — the question, why it matters, what was already checked,
and which files hold the answer — exist so the bank costs the owner reading time and
nothing else. Run it after an unattended build, or before a walkthrough with whoever owns
the system; it makes a better agenda than a blank page.

## Artifact types

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
| Pattern | PAT- | What problem does this solve repeatedly? |

## Tips

- **Start small.** One scuba session deepening 2-3 artifacts beats trying to cover everything at once.
- **Correct early.** If Reef gets a fact wrong, correct it immediately. Wrong facts compound.
- **Add your own docs.** Drop architecture docs, meeting notes, or design specs into `sources/context/`. Scuba and deep will use them.
- **Open in Obsidian.** Artifacts use `[[wikilink]]` syntax. Open the reef directory as a vault, enable Graph View.
- **One reef per team.** Services that talk to each other belong together. The sweet spot is 3-15 repos.
