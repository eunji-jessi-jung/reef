# Update Report Schema

The update report is a persistent JSON file at `.reef/update-report.json` that tracks what changed, what needs review, and what has been applied. It enables cross-session resumption.

Completed reports are archived to `.reef/update-history/update-report-{ISO-date}.json`.

## Top-level structure

```json
{
  "generated_at": "ISO timestamp",
  "source_index_at": "ISO timestamp from source-index.json",
  "sources_pulled": {
    "service-a": { "pulled": true, "commits_pulled": 3 },
    "service-b": { "pulled": false, "reason": "user skipped" }
  },
  "source_changes": {
    "service-a": {
      "new": 1, "updated": 3, "deleted": 0, "renamed": 0,
      "semantic_summary": "Added async fulfillment pipeline (new Celery tasks, new FulfillmentRecord model). Order API now accepts batch submissions. Legacy sync processing path removed."
    },
    "service-b": {
      "new": 0, "updated": 0, "deleted": 0, "renamed": 0,
      "semantic_summary": "No changes."
    }
  },
  "new_questions": [
    {
      "id": "Q-042",
      "question": "The async fulfillment pipeline uses a new FULFILLMENT_QUEUE env var — what broker is this targeting in production?",
      "related_artifacts": ["SYS-ORDERS", "PROC-ORDERS-FULFILLMENT"]
    }
  ],
  "items": [],
  "context_impact": [],
  "stats": {
    "total_items": 0,
    "substantive": 0,
    "trivial": 0,
    "by_category": {}
  }
}
```

## Report item structure

Each affected artifact gets one item:

```json
{
  "id": "update-001",
  "artifact_id": "SYS-INGEST",
  "category": "refresh",
  "impact": "substantive",
  "summary": "3 source files changed; 2 Key Facts outdated, 1 new fact discovered",
  "details": {
    "changed_sources": ["service-a:src/ingest/handler.py"],
    "stale_facts": ["Ingest uses synchronous processing"],
    "new_facts": ["Ingest now uses async batch processing via Celery"],
    "resolved_unknowns": []
  },
  "status": "pending"
}
```

## Item categories

| Category | Meaning |
|---|---|
| `refresh` | Existing artifact needs content update due to source changes (existing facts updated, not new entities) |
| `enrichment` | New entity, model, endpoint, or concept discovered that belongs inside an existing artifact. More significant than a refresh — new content is being added, not just existing content updated. |
| `new_entity` | New entity/API group/service discovered that does NOT fit any existing artifact — needs a new draft artifact file |
| `orphaned` | Source code removed, artifact may be invalid |
| `renamed` | Source paths changed, artifact refs need updating |
| `context_enrichment` | New context doc enriches existing artifact |

## Impact classification

| Impact | Criteria |
|---|---|
| `trivial` | Only `freshness_note` and `last_verified` need bumping; no Key Facts changed. Also: pure renames where content is identical. |
| `substantive` | Key Facts outdated, new facts discovered, known_unknowns resolved, entity added/removed, API surface changed. |

Trivial items are auto-applied during report generation (status: `"auto_applied"`). Substantive items require human review (status: `"pending"` until approved).

## Item statuses

| Status | Meaning |
|---|---|
| `pending` | Awaiting user review |
| `applied` | User approved and changes written |
| `skipped` | User explicitly skipped |
| `auto_applied` | Trivial change, applied automatically |

## Context impact entry

For new context files that match existing artifacts:

```json
{
  "file": "sources/context/requirements/order-fulfillment-srd.pdf",
  "affected_artifacts": ["PROC-PAYMENTS-ORDER-FINALIZATION"],
  "resolves_unknowns": 2,
  "summary": "Resolves 2 known_unknowns about fulfillment SLA requirements"
}
```

## Semantic summary guidelines

The `semantic_summary` field in `source_changes` must describe **what changed in meaning**, not just file counts. Read the changed files and summarize:

- New models, fields, or relationships
- API endpoints added, removed, or changed
- Business logic changes (validation, state transitions, integrations)
- Configuration changes (env vars, defaults, feature flags)
- Patterns that appeared or disappeared

Good: "Added async fulfillment pipeline. Order API now accepts batch submissions. Legacy sync path removed."
Bad: "3 files updated, 1 new file."
