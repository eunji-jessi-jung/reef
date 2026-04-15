---
description: "Lint artifacts for format and structural errors, with auto-fix"
---

# /reef:lint

Validate reef artifacts against the artifact contract. Reports errors, warnings, and info. Can auto-fix common issues.

## Setup

Read this reference before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`

## Voice

Direct and mechanical. Report findings plainly. No metaphors. No emojis.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop: "No reef found. Run `/reef:init` first."

### 2. Run lint

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Parse the JSON output. Extract `errors`, `warnings`, and `summary`.

### 3. Report

If zero errors and zero warnings:

```
Lint passed — {N} artifacts checked, no issues found.
```

Otherwise, render a structured report:

```
Reef Lint — {N} artifacts checked
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Errors: {N}
  {ARTIFACT-ID}  {check}  {message}
  ...

Warnings: {N}
  {ARTIFACT-ID}  {check}  {message}
  ...
```

Group by artifact when multiple issues affect the same file. Show errors first, then warnings.

### 4. Auto-fix (if `--fix` argument or user requests it)

If the user passes `--fix` or says "fix" / "auto-fix" / "fix them", apply these fixes:

| Check | Auto-fix |
|-------|----------|
| `id_case` | Uppercase the `id` field in frontmatter |
| `filename_case` | Rename file to lowercase |
| `title_case` | Title-case the `title` field |
| `schema` (missing field) | Add field with sensible default: `tags: []`, `relates_to: []`, `sources: []`, `known_unknowns: []`, `freshness_note: "TBD"`, `freshness_triggers: []`, `aliases: []`, `notes: ""` |
| `wikilink_sync` (frontmatter has, Related missing) | Add missing `[[wikilink]]` to `## Related` section |
| `wikilink_sync` (Related has, frontmatter missing) | Add missing entry to `relates_to` with `type: "relates_to"` |
| `dangling_reference` | Remove the dangling `relates_to` entry (warn user) |
| `orphan` | Info only — cannot auto-fix (requires another artifact to link to this one) |
| `source_existence` | Info only — cannot auto-fix (source may have been renamed/deleted) |
| `freshness` | Info only — cannot auto-fix (requires `/reef:update`) |
| `key_facts_sources` | Info only — cannot auto-fix (requires code reading to add citations) |

For each fix:
1. Read the artifact file.
2. Apply the fix.
3. Write the file back.
4. Report: "Fixed: {ARTIFACT-ID} — {description}"

After all fixes, re-run lint to verify:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Report final status: "Re-lint: {N} errors, {M} warnings remaining" or "Re-lint: all clear."

### 5. Single-artifact mode

If the user specifies an artifact ID or filename (e.g., `/reef:lint proc-payments-auth`), lint only that artifact:

1. Find the artifact file in `artifacts/`.
2. Parse its frontmatter.
3. Run the same checks as `reef.py lint` but only for that artifact (frontmatter schema, ID/filename match, relates_to validity, source existence, Key Facts citations, wikilink sync).
4. Report results.
5. If `--fix` requested, apply fixes to that artifact only.

This mode is used by the post-write hook — it runs lint on a single artifact immediately after it is written, so errors are caught at write-time rather than batched at the end of a pipeline stage.

## Post-write hook integration

Other skills (snorkel, scuba, artifact, update) should call `/reef:lint` in single-artifact mode after writing each artifact. The pattern:

```
After writing {artifact-file}:
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
  Parse output, filter to errors for {artifact-id} only.
  If errors found for this artifact, fix them immediately before moving on.
```

This catches format errors at write-time. Skills should NOT wait until the end of a pipeline stage to lint — lint each artifact as it is written.

## Key Rules

- This skill is safe to run at any time — it reads artifacts and optionally fixes them.
- Auto-fix never deletes artifact content — it only fixes structural/format issues.
- Auto-fix never changes Key Facts, Overview, or any content section — only frontmatter and `## Related`.
- If a fix would be ambiguous (e.g., which `type` to use for a `relates_to` entry), skip it and report as manual-fix-needed.
