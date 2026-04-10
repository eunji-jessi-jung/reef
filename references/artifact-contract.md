# Artifact Contract

The enforceable rulebook for all Reef artifacts. Every skill that creates, updates, or validates an artifact must conform to this contract.

---

## Artifact Types

| Type | Prefix | Purpose | Required Body Sections |
|------|--------|---------|----------------------|
| System | SYS- | Entry point for a domain or service | Overview, Key Facts, Responsibilities, Core Concepts, Related |
| Schema | SCH- | Interpretation of data models | Overview, Key Facts, Entities, Related |
| API | API- | Interpretation of API surfaces | Overview, Key Facts, Source of Truth, Resource Map, Related |
| Process | PROC- | Workflow, lifecycle, or behavior | Purpose, Key Facts + archetype-dependent body, Related |
| Decision | DEC- | Architectural decision record | Context, Decision, Key Facts, Rationale, Consequences, Related |
| Glossary | GLOSSARY- | Domain term registry | Terms (table with wikilinks), Related |
| Contract | CON- | Cross-system boundary agreement | Parties, Key Facts, Agreement, Current State, Related |
| Risk | RISK- | Known issues with severity tracking | Description, Key Facts, Impact, severity/resolution fields, Related |

---

## Relationship Types

| Type | Meaning |
|------|---------|
| parent | Detail of a higher-level artifact |
| depends_on | Assumes another artifact's content |
| refines | Adds peer-level detail |
| constrains | Governs or limits another |
| supersedes | Replaces a previous artifact |
| feeds | Sends data to another system |
| integrates_with | Bidirectional exchange |

---

## Frontmatter Schema

Required fields, in this exact order:

```yaml
---
id: "{PREFIX}-{slug}"
type: "{type}"
title: "{Human-readable title}"
domain: "{domain-slug}"
status: draft | active | deprecated
last_verified: YYYY-MM-DD          # unquoted ISO date
freshness_note: "{why this is current or stale}"
freshness_triggers:                 # sorted alphabetically
  - "{file_or_path_pattern}"
known_unknowns:
  - "{honest gap or open question}"
tags:
  - "{tag}"
aliases:
  - "{alternate name}"
relates_to:                         # sorted by target
  - type: "{relationship_type}"
    target: "[[{ARTIFACT_ID}]]"
sources:                            # sorted by ref
  - category: implementation | documentation | discussion | external
    type: github | doc | manual
    ref: "{relative_path_or_url}"
    notes: "{optional context}"
notes: "{optional freeform notes}"
---
```

### Field Rules

- `id` must match the filename: lowercase, hyphens only (e.g., `sys-ingest` matches `sys-ingest.md`).
- `status` accepts exactly one of: `draft`, `active`, `deprecated`.
- `last_verified` is an unquoted ISO date (`2026-04-10`, not `"2026-04-10"`).
- `freshness_note` must never be empty. State why the artifact is current or what might make it stale.
- `freshness_triggers` are sorted alphabetically. Each entry is a file path or glob pattern relative to the source root.
- `relates_to` entries are sorted by `target`. Each entry has `type` (one of the 7 relationship types) and `target` (as `[[WIKILINK]]`).
- `sources` entries are sorted by `ref`. Each entry has `category`, `type`, `ref`, and optional `notes`.

### Determinism Rules

To ensure consistent output across runs:

1. `relates_to` — sorted alphabetically by `target`
2. `sources` — sorted alphabetically by `ref`
3. `freshness_triggers` — sorted alphabetically

---

## Key Facts Rules

- Every artifact type except Glossary must include a `## Key Facts` section.
- Each fact is a single, independently verifiable claim.
- Each fact links to its source using `→` syntax.
- Format: `- {Verifiable claim} → {source_ref}`
- Example: `- Ingest service owns order processing → src/services/order.py`
- Key Facts are not summaries. They are atomic assertions a reader can check against the cited source.

---

## Validation on Accept

### Blocking (must pass)

These checks must pass before an artifact is accepted into the vault:

1. YAML is parseable.
2. All required frontmatter fields are present and in the correct order.
3. `id` matches the filename (lowercase, hyphens, prefix matches type).
4. `status` is a valid enum (`draft`, `active`, `deprecated`).
5. `type` is a valid enum (one of the 8 artifact types, lowercase).
6. `freshness_note` is not empty.
7. `## Key Facts` section is present (except for Glossary type).

### Warning (reported but non-blocking)

These are reported for the user to address but do not prevent acceptance:

1. `relates_to` targets exist as files in the vault.
2. `sources` refs resolve to actual files or URLs.
3. All required body sections for the artifact type are present.
4. `## Related` section in the body matches `relates_to` in frontmatter.

---

## Obsidian Dual Strategy

Reef artifacts serve two audiences: agents and humans using Obsidian.

1. **Frontmatter `relates_to`** — structured data for agents and Dataview queries. This is the machine-readable source of truth for relationships.
2. **Body `[[wikilinks]]`** — inline links in Key Facts, prose paragraphs, and the `## Related` section. These power Obsidian's graph view and make navigation natural for human readers.

Both are generated together. The lint pass checks that they stay in sync: every `relates_to` target should appear as a wikilink somewhere in the body, and vice versa.
