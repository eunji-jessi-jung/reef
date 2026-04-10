---
description: "Validate artifacts and report freshness"
---

# /reef:health

Read-only validation and freshness report. This skill does NOT modify artifacts. To fix issues, run `/reef:update`.

## Setup

Read these references before doing anything else:

- `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`

## Voice

Curious Researcher. Use reef metaphor for status ("Your reef is aging", "3 artifacts growing stale"). Plain language for actions ("Run /reef:update to refresh"). No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Find the `.reef/` directory in cwd or parents. Read `project.json` from the reef root.

### 2. Run script checks

Run both commands:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py lint --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py diff --reef <reef-root>
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

Render the health report as a text table using Unicode box-drawing characters. Follow this layout exactly:

```
Reef Health — {project name}                         {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources          Files    Seen   Deep   Freshness
────────────────────────────────────────────────
{source}         {N}      {N}    {N}    {bar} {status}

Artifacts        Total    Fresh  Aging  Stale  Errors
────────────────────────────────────────────────
{TYPE-}          {N}      {N}    {N}    {N}    {N}

Issues: {N} errors · {N} warnings · {N} info
Run /reef:update to refresh stale artifacts.
```

**Column definitions:**

- **Files** — total files in that source.
- **Seen** — files referenced by at least one artifact.
- **Deep** — files referenced by artifacts with 5 or more Key Facts.
- **Freshness bar** — visual indicator using filled and empty blocks: `████░░░░` (8 characters wide, proportional to coverage).
- **Freshness status** — one of:
  - `fresh` — no source changes since last verification.
  - `aging` — some source changes detected.
  - `stale` — many source changes or `last_verified` is old.
- **Fresh/Aging/Stale** for artifacts — count of artifacts in each freshness state.
- **Errors** — count of blocking validation failures for that artifact type.

Populate each row from the lint and diff output. If a source or type has zero artifacts, still show the row with zeroes.

### 4. Offer deeper checks (do not auto-run)

After presenting the report, offer the LLM opt-in checks. Ask the user:

> "Want me to run deeper checks? I can look for contradictions, stale claims, and suspiciously empty known_unknowns."

If the user accepts, run these:

- **Empty known_unknowns** — flag artifacts where `known_unknowns` is empty. Genuinely no gaps, or under-explored?
- **Contradiction detection** — compare Key Facts across artifacts. Flag conflicting claims about the same entity or behavior.
- **Stale claims** — re-read source files referenced by aging/stale artifacts. Check whether Key Facts still hold against current source content.

Report findings grouped by severity: contradictions first, then stale claims, then empty known_unknowns.

## Important

This skill is strictly read-only. Do not modify any artifact files, index files, or map files. If the user asks to fix something, direct them to `/reef:update` or `/reef:artifact`.
