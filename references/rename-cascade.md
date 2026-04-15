# Rename Cascade Procedure

When a user asks to rename a service (e.g., "we renamed Orders to Fulfillment"), the change cascades across the entire reef. This procedure ensures nothing is left pointing to the old name.

## 1. Identify all affected files

Search for the old name in:

- Artifact filenames (e.g., `SYS-ORDERS.md` → `SYS-FULFILLMENT.md`)
- Artifact `id` fields in frontmatter
- `relates_to` entries in other artifacts
- `[[wikilinks]]` in body text
- `.reef/project.json` services array
- `.reef/questions.json`
- `sources/apis/` and `sources/schemas/` directory names

## 2. Present the full list of changes

Show the user the complete impact before making any edits:

```
Renaming "orders" → "fulfillment" affects:
  - 3 artifact files to rename (SYS-ORDERS, SCH-ORDERS-CORE, API-ORDERS-REST)
  - 3 artifact IDs to update in frontmatter
  - 7 relates_to references across other artifacts
  - 4 wikilinks in body text
  - 1 service entry in project.json
  - 2 source directories (apis/orders/, schemas/orders/)
```

Wait for user confirmation before proceeding.

## 3. Apply all changes atomically

On confirmation:

1. Rename artifact files
2. Update `id` fields in renamed artifacts' frontmatter
3. Update `relates_to` entries in all artifacts that referenced the old IDs
4. Update `[[wikilinks]]` in body text across all artifacts
5. Update service name in `.reef/project.json`
6. Update references in `.reef/questions.json`
7. Rename source directories under `sources/apis/` and `sources/schemas/`

## 4. Post-rename

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Renamed service: {old} → {new}" --reef <reef-root>
```

Run `snapshot` on every modified artifact.
