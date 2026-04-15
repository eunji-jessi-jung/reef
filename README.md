# Reef

Most codebase knowledge lives in someone's head, or gets re-derived from scratch every time someone asks a question. Reef takes a different approach: it builds a persistent, structured wiki from your source code — one that compounds over time instead of being rediscovered on every query.

Reef is a Claude Code plugin. It reads source code, asks the right questions, and produces interlinked markdown artifacts with YAML frontmatter, source citations, and honest gap tracking. The AI does the reading and the bookkeeping. You bring the domain knowledge and decide what matters. Output is Obsidian-native, local-first, plain markdown.

## Built For

Reef is designed for **codebases that have services, data, and interfaces**. If your code has APIs (REST, gRPC, GraphQL), persistent data (any database or ORM), and components that talk to each other — Reef will produce rich, interlinked artifacts.

It works well for: microservices, monoliths with modules, full-stack apps, data pipelines, infrastructure-as-code, DevOps toolchains, and anything in between.

It is not the right tool for: native mobile apps with no backend, game engines, embedded firmware, or ML training notebooks. These don't have the data schemas, API surfaces, or service boundaries that Reef is built to document.

## Guide

For a full step-by-step walkthrough of the workflow (init → scuba → deep → update), see **[docs/guide.md](docs/guide.md)**.

## Quick Start

```
/plugin marketplace add eunji-jessi-jung/reef
/plugin install reef@eunji-jessi-jung-reef
```

Then, in any project directory:

```
/reef:init        # Set up the reef, then auto-runs snorkel + source in parallel:
                  #   snorkel — auto-discover 3-6 draft artifacts
                  #   source  — extract full API specs and ERDs
/reef:scuba       # Deepen drafts through guided Socratic questioning
```

## Skills

| Skill | Description |
|-------|-------------|
| `/reef:init` | Bootstrap a new reef — scope, scaffold, index, seed questions |
| `/reef:snorkel` | Auto-discovery surface pass, 3-6 draft artifacts, no questions asked |
| `/reef:source` | Extract full API specs and ERDs with tiered protocol + recipe caching |
| `/reef:scuba` | Socratic deepening through guided question-and-answer |
| `/reef:deep` | Exhaustive line-by-line tracing of critical areas |
| `/reef:artifact` | Explore a topic, capture knowledge, or update an artifact |
| `/reef:update` | Pull sources, detect changes, generate update report for review |
| `/reef:lint` | Lint artifacts for format and structural errors, with auto-fix |
| `/reef:health` | Read-only validation and freshness report |
| `/reef:test` | Test whether the reef answers your real questions |

## When to Use Each Depth

**Snorkel** — First contact with a codebase. No questions, no input. Produces draft artifacts with honest `known_unknowns`. Also useful when adding a new source to an existing reef.

**Source** — After snorkel, before scuba. Extracts complete API specs and entity-relationship diagrams from your source repos. Tries copying existing specs first, then runtime extraction, then code reading as fallback. Caches successful recipes so repeat runs are fast.

**Scuba** — You have drafts, full API/ERD specs, and domain knowledge. The AI reads code and asks you things code alone can't answer: why decisions were made, who owns what, what breaks in practice. This is where most real knowledge gets captured.

**Deep** — Critical systems where shallow reading misses real behavior. Line-by-line tracing, 5+ Key Facts per artifact with precise citations. Reserve for areas where getting it wrong has consequences.

## I Built a Reef — Now What?

A reef is a living knowledge base. Once scuba completes (even partially), you can:

- **Feed it to dev agents** — point Claude Code, Cursor, or Copilot at the reef directory as context so they understand your domain, not just your syntax
- **Onboard teammates** — open in Obsidian, explore the knowledge graph, ramp up without scheduling walkthrough meetings
- **Export as docs** — artifacts are structured markdown with frontmatter; copy into Confluence, Notion, or a static site
- **Audit and review** — `/reef:health` for coverage gaps, `/reef:test` to check if the reef answers your real questions
- **Keep it alive** — `/reef:update` after code changes; each update costs a fraction of the initial build

See [docs/guide.md](docs/guide.md) for the full workflow.

## Domain Boundaries

One reef covers one ecosystem — services that talk to each other. The sweet spot is **3-15 repos** that form a coherent domain. This is where Reef delivers the most value: complex enough that no one person holds the full picture, small enough that Reef can trace every cross-system connection.

- **1-2 repos:** Reef works, but the code might be its own best documentation. Consider whether you need it.
- **3-15 repos:** The goldilocks zone. Cross-service contracts, shared entities, and auth boundaries are where the real knowledge lives — and where it gets lost most often.
- **15+ repos:** Split into multiple reefs by team or domain. Each reef should cover services that directly interact. Services that don't talk to each other belong in separate reefs.

In a large org (hundreds of repos), the right unit is one reef per team or domain — not one reef for the whole org. A platform team's reef and a product team's reef are separate, each covering their own ecosystem.

## The Question Bank

Seed questions during `/reef:init`. These are the north star. `/reef:test` evaluates whether the reef actually answers them. A reef that answers 8 of 10 questions is useful. A reef with beautiful artifacts that answers 2 of 10 is decorative.

## Keeping It Alive

Knowledge bases die when the maintenance burden outgrows the value. Reef shifts that burden to the machine. `/reef:update` re-indexes sources, detects changes, and walks you through updating affected artifacts. `/reef:health` reports the state without modifying anything. Artifacts don't flip from good to bad — they age gradually. Run these after significant code changes.

## Nine Artifact Types

| Type | Prefix | Question it answers |
|------|--------|-------------------|
| System | SYS- | What does this service do? |
| Schema | SCH- | What does this data mean? |
| API | API- | What can I call? |
| Process | PROC- | What happens when...? |
| Decision | DEC- | Why was it built this way? |
| Glossary | GLOSSARY- | What does this term mean? |
| Contract | CON- | What do these systems agree on? |
| Risk | RISK- | What could go wrong? |
| Pattern | PAT- | What problem does this solve repeatedly? |

## Obsidian

Artifacts are wikilinked with `[[artifact-id]]` syntax — open the reef directory as an Obsidian vault to see the full graph of how everything connects. Enable Graph View and Dataview plugins for the best experience. The reef is plain markdown, so any markdown tool works.

## Adding Your Own Docs

Have architecture docs, design specs, or runbooks that aren't in the codebase? Drop them into `sources/raw/` in your reef directory. Scuba will pick them up when deepening artifacts — they're especially useful for answering questions that code alone can't.

## See It in Action

**[supabase-reef](https://github.com/eunji-jessi-jung/supabase-reef)** — a complete reef covering 5 Supabase repos (Go, Elixir, TypeScript, React) built by a PM with zero Supabase knowledge. Includes a [benchmark report](https://github.com/eunji-jessi-jung/supabase-reef/blob/main/reef-benchmark-report.md) testing whether the reef actually helps AI agents (28 runs, 2 models, 7 tasks, with honest caveats).

## Author

**Eunji Jung** — Product Manager building tools for AI-assisted software engineering.

- [LinkedIn](https://www.linkedin.com/in/eunji-jessi-jung/)
- Questions or feedback? [Open an issue](https://github.com/eunji-jessi-jung/reef/issues)
