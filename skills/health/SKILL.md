---
description: "Validate artifacts and report freshness"
---

# /reef:health

Read-only validation and freshness report. This skill does NOT modify artifacts. To fix issues, run `/reef:update`.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher. Use reef metaphor for status ("Your reef is aging", "3 artifacts growing stale"). Plain language for actions ("Run /reef:update to refresh"). No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Find the `.reef/` directory in cwd or parents. Read `project.json` from the reef root.

### 2. Run script checks

Run both commands:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff --reef <reef-root>
```

These cover the seven mechanical checks:

1. **Orphan detection** — artifacts with no incoming `relates_to` (except `SYS-` roots, which are natural entry points).
2. **Dangling references** — `relates_to` targets that do not resolve to an existing artifact file.
3. **Source file existence** — `sources` refs that no longer exist on disk.
4. **Frontmatter schema** — required fields present, valid enum values, `id` matches filename.
5. **Key Facts without source links** — Key Facts missing the `→` citation syntax.
6. **Wikilink/frontmatter sync** — `## Related` wikilinks do not match `relates_to` entries.
7. **Freshness** — source files changed on disk since the artifact's last write time.

### 3. Format the report

Render the health report as a text table using Unicode box-drawing characters. The report has three sections: domain coverage (headline), artifact health, and source detail (secondary).

**Section 1 — Artifact Topology (headline)**

Show a heatmap matrix of artifact density by service and type. This gives the user an instant visual of where the reef is deep vs thin.

Use shaded block characters to represent density:

- (empty) = 0 artifacts
- `░` = 1-2
- `▒` = 3-4
- `▓` = 5-6
- `█` = 7+

```
Reef Health — {project name}                         {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Artifact Topology
────────────────────────────────────────────────────────────────
           SYS  SCH  API  PROC  CON  PAT  DEC  RISK  GLOSS
{service}   ░    ▒    ▓    █     ░    ▒    ▒    ░     ░
...

░ 1-2  ▒ 3-4  ▓ 5-6  █ 7+  (empty) 0

Total: {N} artifacts across {M} services
```

Counts come from artifact frontmatter `type` and `domain` fields. Include a `shared`/`cross-service` row if artifacts exist with those domains.

**Section 2 — Artifact Health**

```
Artifact Health
────────────────────────────────────────────────────────────────
Type         Total   Verified  Unchecked  Stale
SYS              4          4          0      0
SCH             10          6          4      0
API             14          7          7      0
PROC            34          7         27      0
...

Depth: {avg} Key Facts/artifact · {N}% with worked examples
Quality: {N} lint issues · {N} warnings (exclude source_existence from count — report index staleness separately)
```

If any stale artifacts exist, add a freshness summary line after the table:

```
Freshness: {stale}/{total} stale — run /reef:update to refresh.
```

If no stale artifacts exist, add:

```
Freshness: all artifacts current.
```

**Column definitions:**

- **Verified** — sources checked during last `/reef:update`. Content confirmed current.
- **Unchecked** — not examined in the last update cycle. The artifact's sources did not change, so it was correctly skipped. Likely still accurate, but not re-verified.
- **Stale** — sources have changed on disk since last verification. Needs `/reef:update`.

**Freshness classification logic:** Compare each artifact's `last_verified` date against its source files' modification times on disk (from `reef.py diff` output):
- If the artifact's sources appear in the diff as changed → **stale**.
- If the artifact's sources do NOT appear in the diff AND `last_verified` is from the most recent update cycle → **verified**.
- If the artifact's sources do NOT appear in the diff AND `last_verified` is from a previous cycle → **unchecked**.

The "most recent update cycle" is determined by the latest `update-report` timestamp in `.reef/update-history/`, or the most recent `last_verified` date across all artifacts if no update history exists.

- **Depth** — average Key Facts per artifact across the reef, and percentage of SCH-/PROC- artifacts that contain worked examples (join queries, enum tables, step-by-step flows).
- **Quality** — lint error and warning totals.

**Section 3 — Source Detail (secondary, collapsed by default)**

After the main report, offer: "Want to see source file coverage details?" If the user accepts:

```
Source File Detail
────────────────────────────────────────────────────────────────
Source               Total Files   Referenced   Coverage
{source}             {N}           {N}          {bar}
```

- **Total Files** — all files in the source repo.
- **Referenced** — files cited in at least one artifact's `sources`.
- **Coverage bar** — `████░░░░` (8 chars, proportional to referenced/total).

This section is informational context, not the coverage metric. A low referenced-to-total ratio is expected — reef focuses on domain-critical files, not tests, migrations, configs, or generated code.

Populate each row from the lint and diff output. If a source or type has zero artifacts, still show the row with zeroes.

### 3.5. Actionable guidance

After the report, add a "What next" section based on what the report found. Only include lines that apply — skip any that don't.

```
What next
────────────────────────────────────────────────────────────────
```

| Condition | Guidance |
|-----------|----------|
| Any stale artifacts | `{N} stale artifacts need refreshing. Run /reef:update.` |
| Unanswered questions in `.reef/questions.json` | `{N} open questions in the question bank. Run /reef:deep to investigate.` |
| source_existence lint errors dominate (>80% of errors) | These mean the source index is out of sync, not that artifacts are broken. Report as: `Source index is stale. Run /reef:update to re-index.` Do NOT report the raw error count — it inflates the severity. |
| Other lint errors (non-source_existence) | `{N} lint issues. Most common: {top category}. Run /reef:lint --fix to auto-fix, or review manually.` |
| Everything is clean | `Your reef is healthy. No action needed.` |

### 3.6. Surface orphaned artifacts

Scan all artifact files for `status: orphaned` in frontmatter. If any exist, add a section to the report:

```
Orphaned Artifacts — {N} marked
────────────────────────────────────────────────
  SCH-ORDERS-LEGACY-CART        orphaned {date}   model class removed
  API-PLATFORM-ANALYTICS-V1    orphaned {date}   route prefix removed
  PROC-PIPELINE-NIGHTLY-SYNC   orphaned {date}   source file deleted

These were marked by /reef:update when their source code was removed.
Delete them? Enter numbers (e.g. "1, 2"), "all", or "none".
```

- **On delete:** Remove the artifact file, clean up `relates_to` references in other artifacts, run `rebuild-index` and `rebuild-map`. Log the deletion.
- **On keep:** Leave as-is. They will appear again on the next health check.

If no orphaned artifacts exist, skip this section entirely.

### 4. Offer deeper checks (do not auto-run)

After presenting the report, offer the LLM opt-in checks. Ask the user:

> "Want me to run deeper checks? I can look for contradictions, stale claims, and suspiciously empty known_unknowns."

If the user accepts, run these:

- **Empty known_unknowns** — flag artifacts where `known_unknowns` is empty. Genuinely no gaps, or under-explored?
- **Contradiction detection** — compare Key Facts across artifacts. Flag conflicting claims about the same entity or behavior.
- **Stale claims** — re-read source files referenced by aging/stale artifacts. Check whether Key Facts still hold against current source content.

Report findings grouped by severity: contradictions first, then stale claims, then empty known_unknowns.

After presenting results, remind the user: "Artifacts are wikilinked — open the reef directory as an Obsidian vault to explore the knowledge graph. Have docs that might fill gaps? Drop them in `sources/context/`."

## Important

This skill is read-only except for orphaned artifact cleanup (Step 3.6), which requires user confirmation. Do not modify artifact content, index files, or map files. If the user asks to fix stale content, direct them to `/reef:update` or `/reef:artifact`.
