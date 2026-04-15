# CLAUDE.md Generation Template

This template defines how reef generates and maintains a `CLAUDE.md` file at the reef root. The file makes the reef discoverable and usable by AI agents working on the codebase.

## When to generate/update

| Skill | Action |
|-------|--------|
| `init` | Create initial CLAUDE.md with project scope and source list |
| `snorkel` | Update with artifact summary and key cross-service contracts |
| `scuba` | Update with deeper artifact coverage, decision rationale, known risks |
| `update` | Refresh artifact counts and any new contracts/risks discovered |
| `deep` | Append deep-dive findings if they change the system picture |

## Template

The generated CLAUDE.md should follow this structure. Replace `{placeholders}` with actual reef data.

```markdown
# {project_name} — Knowledge Reef

This directory contains a structured knowledge base for {project_description}.

## What this is

A Reef — a set of interlinked markdown artifacts extracted from source code and enriched with domain knowledge. Each artifact cites specific source files and lines. Artifacts track what is known, what is partially known, and what is explicitly unknown.

## Services

{For each service in project.json:}
- **{service_name}** ({full_name}) — {description}. Sources: {repo list}

## How to use this reef

**Before making cross-service changes**, read the relevant contract artifacts:
{List CON- artifacts with one-line descriptions, e.g.:}
- `artifacts/contracts/con-auth-storage.md` — How storage validates auth tokens
- `artifacts/contracts/con-studio-auth.md` — How the dashboard authenticates users

**Before modifying a service**, read its system artifact:
{List SYS- artifacts, e.g.:}
- `artifacts/systems/sys-auth.md` — Auth service boundaries, dependencies, runtime components

**Before changing data models**, check the schema artifacts:
- `artifacts/schemas/` — Entity definitions with field-level documentation

**Before changing business logic**, check process and decision artifacts:
- `artifacts/processes/` — Entity lifecycles, state machines, workflows
- `artifacts/decisions/` — Why things are built the way they are

## Key risks and known unknowns

{List RISK- artifacts and top known_unknowns across all artifacts, e.g.:}
- `artifacts/risks/risk-auth-known-gaps.md` — Token refresh edge cases, provider-specific quirks
- Several artifacts flag uncertainty about {common theme} — see known_unknowns in individual artifacts

## Artifact counts

{Heatmap or simple table of artifact counts by service x type}

## Freshness

This reef was last updated on {date}. Run `/reef:update` to sync with code changes, or `/reef:health` for a status check.
```

## Rules

- **Keep it scannable.** An agent should get the picture in 10 seconds. No prose paragraphs.
- **Link to artifacts, don't duplicate content.** CLAUDE.md is an index and guide, not a knowledge dump.
- **Update, don't append.** Each skill overwrites the relevant sections, not appends endlessly.
- **Only include artifacts that exist.** Don't reference empty categories.
- **CON- artifacts are the highest-value section.** Cross-service contracts are what agents miss most when working from code alone. Always list them prominently.
