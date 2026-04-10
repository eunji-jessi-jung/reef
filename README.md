# Reef

Most codebase knowledge lives in someone's head, or gets re-derived from scratch every time someone asks a question. Reef takes a different approach: it builds a persistent, structured wiki from your source code — one that compounds over time instead of being rediscovered on every query.

Reef is a Claude Code plugin. It reads source code, asks the right questions, and produces interlinked markdown artifacts with YAML frontmatter, source citations, and honest gap tracking. The AI does the reading and the bookkeeping. You bring the domain knowledge and decide what matters. Output is Obsidian-native, local-first, plain markdown.

## Quick Start

```
/plugin marketplace add eunji-jessi-jung/reef
/plugin install reef@eunji-jessi-jung-reef
```

Then, in any project directory:

```
/reef:init        # Set up the reef, point it at your source code, seed questions
/reef:snorkel     # Auto-discover 3-6 draft artifacts in ~5 minutes
/reef:scuba       # Deepen drafts through guided Socratic questioning
```

## Skills

| Skill | Description |
|-------|-------------|
| `/reef:init` | Bootstrap a new reef — scope, scaffold, index, seed questions |
| `/reef:snorkel` | Auto-discovery surface pass, 3-6 draft artifacts, no questions asked |
| `/reef:scuba` | Socratic deepening through guided question-and-answer |
| `/reef:deep` | Exhaustive line-by-line tracing of critical areas |
| `/reef:artifact` | Create or update a single artifact with full contract enforcement |
| `/reef:update` | Re-index sources, detect changes, update affected artifacts |
| `/reef:health` | Read-only validation and freshness report |
| `/reef:test` | Test whether the reef answers your real questions |
| `/reef:obsidian` | Open the reef in Obsidian for graph visualization |

## When to Use Each Depth

**Snorkel** — First contact with a codebase. No questions, no input. Produces draft artifacts with honest `known_unknowns`. Also useful when adding a new source to an existing reef.

**Scuba** — You have drafts and domain knowledge. The AI reads code and asks you things code alone can't answer: why decisions were made, who owns what, what breaks in practice. This is where most real knowledge gets captured.

**Deep** — Critical systems where shallow reading misses real behavior. Line-by-line tracing, 5+ Key Facts per artifact with precise citations. Reserve for areas where getting it wrong has consequences.

## Domain Boundaries

One reef covers one ecosystem — services that talk to each other. Services that don't interact belong in separate reefs. When in doubt, start with one reef per team or domain.

## The Question Bank

Seed questions during `/reef:init`. These are the north star. `/reef:test` evaluates whether the reef actually answers them. A reef that answers 8 of 10 questions is useful. A reef with beautiful artifacts that answers 2 of 10 is decorative.

## Keeping It Alive

Knowledge bases die when the maintenance burden outgrows the value. Reef shifts that burden to the machine. `/reef:update` re-indexes sources, detects changes, and walks you through updating affected artifacts. `/reef:health` reports the state without modifying anything. Artifacts don't flip from good to bad — they age gradually. Run these after significant code changes.

## Eight Artifact Types

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

## Obsidian

Run `/reef:obsidian` to open the reef as an Obsidian vault. Artifacts are wikilinked — the graph view shows how everything connects. Enable Graph View and Dataview plugins for the best experience. The reef is plain markdown, so any markdown tool works.
