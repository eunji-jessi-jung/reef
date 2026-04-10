# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Reef is a Claude Code plugin that builds structured knowledge wikis from codebases. Users point it at source code, and through automated discovery + Socratic questioning, it produces interlinked markdown artifacts (systems, schemas, APIs, processes, decisions, glossaries, contracts, risks) with YAML frontmatter. Output is Obsidian-native, local-first, plain markdown.

This repo is currently in the **planning/pre-implementation stage**. `PLAN.md` is the authoritative build plan.

## Architecture Overview

Reef is a Claude Code plugin with three layers:

- **Skills** (`skills/*/SKILL.md`): 9 slash commands that orchestrate user-facing workflows. Each skill is a separate SKILL.md read by Claude Code at invocation time.
- **Scripts** (`scripts/reef.py`): Single Python script handling all deterministic operations (indexing, hashing, diffing, linting, snapshots). Skills call it via Bash and parse JSON stdout. Dependencies: Python stdlib + pyyaml (auto-installed via SessionStart hook).
- **References** (`references/`): Artifact contract, methodology, understanding template, and 8 artifact templates. Read by skills on demand to stay within context limits.

### Key Skills

| Skill | Purpose |
|-------|---------|
| `/reef-init` | Bootstrap wiki directory structure (3-zone: artifacts/, sources/, .reef/) |
| `/reef-snorkel` | Auto-discovery: 3-6 draft artifacts, no questions, ~5 min |
| `/reef-scuba` | Socratic deepening: question-driven knowledge extraction |
| `/reef-deep` | Exhaustive line-by-line tracing of specific areas |
| `/reef-artifact` | Create/update single artifact with full contract enforcement |
| `/reef-update` | Re-index sources, detect changes, update affected artifacts |
| `/reef-health` | Read-only validation + freshness report (text-rendered) |
| `/reef-test` | Answer questions from question bank using only wiki content |
| `/reef-obsidian` | Open reef in Obsidian |

### Artifact System

8 types (SYS-, SCH-, API-, PROC-, DEC-, GLOSSARY-, CON-, RISK-) with 7 relationship types. Every artifact has YAML frontmatter with enforced field ordering, Key Facts linked to sources, known_unknowns, and freshness tracking via source snapshots. The artifact contract in `references/artifact-contract.md` is the enforceable rulebook.

### Design Principles

- **Scripts do finding, LLM does interpreting.** Deterministic ops (hashing, diffing, linting) go in reef.py. Intelligence (code interpretation, artifact generation) stays in skills.
- **One reef = one domain.** Cross-domain ecosystems should be separate reefs, mergeable later via `/reef-merge`.
- **Source snapshots at write time.** Cannot be backfilled. Powers the entire freshness/lint/update story.
- **Obsidian dual strategy.** Frontmatter `relates_to` for agents/Dataview. Body `[[wikilinks]]` for Obsidian graph view. Both generated; validation checks sync.
- **Curious Researcher voice.** Present-participle narration. No emojis. No exclamation marks.

## Implementation Phases

See `PLAN.md` for the full phased plan. Build order: scaffold + script + references (Phase 1) -> snorkel (Phase 2) -> artifact + health + update (Phase 3) -> scuba + deep (Phase 4) -> test + polish + docs (Phase 5) -> docs site on Mintlify at reef.seaof.ai (Phase 6) -> v1.1 merge/source skills (Phase 7).

## Plugin Manifest

The plugin registers via `.claude-plugin/plugin.json` with a `SessionStart` hook that installs pyyaml. No other dependencies or network requests.
