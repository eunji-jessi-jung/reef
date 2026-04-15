---
description: "Re-index sources and update stale artifacts"
---

# /reef:update

Pull latest source code, re-extract specs, detect what changed, and produce an update report for human review. This is the "keep your reef alive" skill. `/reef:health` reports staleness; `/reef:update` fixes it.

**Default mode is human-reviewed.** Changes are presented as a curated report. You decide what to apply. Use `--auto` to apply everything without prompting.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 0. Check for an unfinished update report

Before doing anything else, check if `.reef/update-report.json` exists.

**If it exists and has items with `"status": "pending"`:**

Count applied, pending, and skipped items. Then check staleness: compare the report's `source_index_at` against the current modification times of source files on disk (spot-check 5-10 files from the source index). If any have changed since the report was generated, the report is stale.

**Report is fresh (sources unchanged):**

```
Found an unfinished update report from {date}.
  Applied: N items | Pending: M items | Skipped: K items

Options:
  1. Resume — review remaining M items
  2. Regenerate — re-scan sources and build a fresh report
```

**Report is stale (sources changed since generation):**

```
Found an unfinished update report from {date}.
  Applied: N items | Pending: M items | Skipped: K items

Warning: sources have changed since this report was generated.
The report may be incomplete or outdated.

Options:
  1. Regenerate — build a fresh report from current sources (recommended)
  2. Resume anyway — apply remaining items (may miss new changes)
  3. Discard — delete the old report and start fresh
```

On **Resume**: skip to Step 7 (present report and review loop) with the existing report.
On **Regenerate** or **Discard**: delete `update-report.json` and proceed from Step 1.

**If no report exists or report has no pending items:** proceed from Step 1.

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

Read `.reef/project.json` for services and source paths.

### 2. Pipeline stage gate

Read `.reef/scuba-manifest.json`.

**No manifest file:** Hard block.
```
This reef hasn't been through scuba yet. Run /reef:scuba first.
```

**Manifest exists, `planned` is empty:** Scuba is complete. Proceed to Step 3.

**Manifest exists, `planned` is non-empty:** Scuba is incomplete. Check manifest freshness by comparing `generated_at` against source file modification times on disk.

If manifest is fresh (sources unchanged since generation):
```
Scuba has {N} items remaining in the manifest.

Options:
  1. Finish scuba first (recommended) — resume /reef:scuba with {N} remaining items
  2. Proceed with update anyway (not recommended — incomplete foundation)
```

If manifest is stale (sources changed since generation):
```
Scuba has {N} items remaining, but sources have changed since the
manifest was generated on {date}. The manifest may plan artifacts
for code that no longer exists, or miss new code.

Options:
  1. Finish scuba first (recommended) — resume /reef:scuba with {N} remaining items
  2. Regenerate scuba manifest from current code, then finish scuba
  3. Proceed with update anyway (not recommended)
```

On option 1: tell user to run `/reef:scuba`. Stop.
On option 2: tell user to run `/reef:scuba --fresh`. Stop.
On proceed anyway: print warning and continue. The user is the domain expert and may have valid reasons (e.g., remaining items were intentionally deferred).

### 3. Pull source code

For each source in `project.json`, check if it is a git repository (look for `.git` directory at the source path).

For git repos, fetch from remote to check status:
```bash
git -C <source-path> fetch 2>&1
git -C <source-path> rev-list HEAD..@{u} --count 2>/dev/null
```

Present a summary:
```
Source repositories:
  service-a    /path/to/service-a    (3 commits behind origin/main)
  service-b    /path/to/service-b    (up to date)
  shared-lib   /path/to/shared-lib   (not a git repo)
  service-c    /path/to/service-c    (remote status unknown — network may be unavailable)

Pull latest for git repos? (yes / no / select repos)
```

**On yes:** run `git -C <path> pull` for each selected repo. Report results:
```
Pulled:
  service-a — 3 commits pulled
  service-b — already up to date
```

**If a pull fails, check the error:**
- **Auth failure** (stderr contains "Authentication failed", "could not read Username", "fatal: could not read Password", or HTTP 403/401): **Stop pulling.** Tell the user:
  ```
  Git pull failed for {repo} — looks like an authentication issue.
  You may be logged into the wrong GitHub account.

  You can fix this now (run `! gh auth login` to re-authenticate)
  or skip pulling and continue with whatever code is on disk.
  ```
  Wait for the user to respond before continuing. Do not silently proceed.
- **Other failure** (uncommitted changes, merge conflicts): warn and continue with the stale copy. Do not attempt to resolve conflicts.

**On no/skip:** proceed with whatever code is on disk. Note: "Proceeding with current local code. Artifacts will be updated against what is on disk."

**No git repos found:** skip this step silently. "None of your sources are git repositories. Skipping source pull."

### 4. Re-extract API specs and ERDs

**BLOCKING STEP — do not proceed to Step 5 until this step is fully complete.**

Run the source extraction skill to refresh API specs and ERDs from current code. This uses cached recipes from `.reef/source-recipes.json`, so it replays the exact commands that worked during the initial extraction.

**Before extracting, determine which repos to skip:**

1. **0 commits pulled → skip.** If Step 3 reported 0 commits pulled for a repo (or the repo was not pulled), the code hasn't changed. The existing spec is still current. Do not re-extract.
2. **Frontend-only repos → skip.** Repos that contain no API framework and no ORM/ODM (no backend server, no database models) have nothing to extract. Check the cached recipes — if a repo has no `extraction_command` and no `schema_command` in `source-recipes.json`, it's frontend-only or infrastructure-only. Also skip repos whose names clearly indicate frontend (`-frontend`, `-admin-ui`, `-web`).

Report what was skipped and why:
```
Skipping re-extraction for:
  auth-service — 0 commits pulled, code unchanged
  storefront-frontend — frontend repo, no API/ERD to extract
  admin-dashboard — frontend repo, no API/ERD to extract
```

**For remaining repos,** read `${CLAUDE_PLUGIN_ROOT}/skills/source/SKILL.md` and follow its instructions. Key differences from a first run:

- **Tier 1 (cached recipe replay) will handle most repos.** The recipe cache stores the command, env vars, PYTHONPATH, and stub list. Replay produces a fresh spec from today's code.
- **If a cached recipe fails** (new dependency, changed env var), it falls through to Tier 2 (fresh runtime extraction) automatically.
- **This step is fully automated** — no user input needed unless a tool is missing.
- **Extraction runs sequentially per app.** Monorepos with multiple apps (e.g., a backend with orders/payments/inventory/fulfillment) extract each app one at a time since they share runtime. If a repo's extraction fails, skip it and warn — do not retry. Move on to the next repo.
- **Time budget: 4 minutes per app.** If a single app's extraction exceeds 4 minutes, move on to the next app or repo. Report what was skipped. Most single-app repos finish in under 2 minutes.

After source extraction completes, report what was refreshed:
```
Source re-extraction complete. 8 API specs and 5 ERDs refreshed from current code.
```

If re-extraction fails for a service, warn and continue. That service's artifacts will be flagged as potentially stale in the report.

**Only after this step is fully done — all repos attempted, results reported — proceed to Step 5.**

### 5. Re-index sources and detect changes

Run these commands sequentially:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff --reef <reef-root>
```

The diff command compares current source hashes against artifact snapshots. It outputs:
- Per-source change counts (new, updated, deleted, unchanged)
- List of affected artifacts (artifacts whose source files changed)
- Details of each changed file with its classification

#### 5a. Read changed files and build semantic understanding

Do not stop at file counts. For **every** file flagged by the diff — **new, updated, AND deleted** — build a semantic understanding of what actually changed:

**New files:** Read the full file. Determine what it adds:
- A new model/entity → candidate for a new SCH- artifact
- A new route handler or controller → may expand an existing API- artifact or warrant a new one
- A new utility/middleware/integration → may affect existing SYS- or PROC- artifacts
- A new test file → may reveal behavioral documentation for existing artifacts
- **Key question: does this file belong to an existing artifact's scope, or is it something entirely new?** Check the source-artifact map. If no existing artifact references files in the same module/directory, this is likely uncovered territory.

**Updated files:** Read the changed sections. Determine what shifted:
- New models, fields, or relationships added
- API endpoints added, removed, or signature-changed
- Business logic changes (new validation rules, changed state transitions, new integrations)
- Configuration changes (new env vars, changed defaults, new feature flags)
- Patterns that appeared or disappeared (new error handling, new retry logic, new auth checks)

**Deleted files:** Check what they used to provide:
- Was this file a source for any artifact? (Check source-artifact map.) If so, that artifact needs updating — some of its Key Facts may now be invalid.
- Did this file contain models, routes, or config that other artifacts reference? Flag those artifacts for review even if the deleted file wasn't in their `sources` list directly.
- Was this the *only* source for a behavior documented in an artifact? That behavior may no longer exist.

This semantic reading is what makes the update report valuable — it tells the user "the order service now supports async fulfillment" instead of "3 files changed in orders/."

#### 5b. Discover new questions

As you read changed source files, watch for things that raise questions the reef cannot answer from code alone:

- **New integrations:** "Service A now calls a new endpoint on Service B — what is the contract? Is this a planned integration?"
- **Changed business logic:** "The overlap constraint was loosened from strict to partial — was this intentional? What are the new rules?"
- **New configuration:** "A new feature flag `ENABLE_ASYNC_FULFILLMENT` appeared — is this actively being rolled out?"
- **Removed code:** "The legacy sync path was deleted — has all traffic been migrated?"
- **Ambiguous patterns:** "Two services now both define a `ProcessingStatus` enum with different values — is this intentional divergence?"

Add discovered questions to `.reef/questions.json` with:
```json
{
  "id": "Q-{next-number}",
  "question": "...",
  "status": "unanswered",
  "phase": "update",
  "source": "detected during update on {date}",
  "related_artifacts": ["artifact-ids-if-known"]
}
```

These questions will appear in the update report under a dedicated section so the user can answer them, defer them, or dismiss them. They also enrich future scuba and deep sessions.

### 6. Detect new context and structural changes

#### 6a. New context files

Scan `sources/context/` and `sources/raw/` for files that are not yet referenced by any artifact's `sources` field. These are newly added non-code context — requirements docs, design decisions, SOPs, meeting notes, roadmaps.

If new context files are found:
1. Read each file (supports .md, .txt, .pdf, .csv — skip binary files other than PDF).
2. Match content against existing artifacts' `known_unknowns`. If a context doc answers or partially answers a known_unknown, flag that artifact for update.
3. Match against artifact topics more broadly — a PRD about the order fulfillment system is relevant to PROC- and SCH- artifacts covering that feature.

If no new context files found, skip silently.

#### 6b. New things (entities, APIs, services, source repos)

**This step is critical. Do not skip it.** Run the detection script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py detect-new --reef <reef-root>
```

This scans all source repos for files added since the last update, classifies them (model, API, or other), extracts class names from model files, and checks whether each class is already mentioned in any artifact.

**Read the JSON output.** Key fields:

- `new_files_total` — total new source files found
- `new_model_files` — new files in `models/` or `entities/` directories
- `new_api_files` — new files in `endpoints/`, `routes/`, `controllers/` directories
- `uncovered_entities` — model classes NOT mentioned in any artifact. Each has `class`, `file`, `nearest_artifact` (the closest artifact by service, or null), and `cross_app` (boolean).
- `cross_app_classes` — class names that appear in multiple repos/apps. These are cross-cutting concerns.

**For each uncovered entity:**

1. If `cross_app` is true → always create a `new_entity` item, even if `nearest_artifact` is set. Cross-app models (same class in multiple repos) are cross-cutting concerns that warrant their own artifact, not enrichment into one app's schema.
2. If `cross_app` is false and `nearest_artifact` is set → create an `enrichment` item on that artifact. Read the new model file to get field details for the summary: "New ReturnRequest model (status enum, refund_amount, requested_at). Not yet documented in SCH-ORDERS-CORE."
3. If `cross_app` is false and `nearest_artifact` is null → create a `new_entity` item. This entity doesn't fit any existing artifact.

**For new API files:** Check if the routes are already covered by an existing API- artifact. If not, create an `enrichment` or `new_entity` item.

**Also check:**
1. **New source repos.** Compare `project.json` sources against `source-index.json`. New repos need SYS-, SCH-, and API- artifacts. Recommend `/reef:snorkel`.
2. **New services.** Repos/directories on disk with no SYS- artifact.

#### 6c. Removed things (entities, APIs, services, source files)

1. **Removed source files — partial loss.** For each deleted source file, check which artifacts reference it. If an artifact loses *some* of its sources (but not all), it is not orphaned — but some of its Key Facts may now be invalid. Flag it as a `refresh` item with `"details.reason": "source file deleted"` so the user knows to verify the remaining facts.
2. **Removed source files — total loss.** If ALL of an artifact's source files are deleted, the artifact is orphaned.
3. **Removed entities.** For each SCH- artifact, verify the model/table still exists in source code. If the model file is deleted or the class/table is removed, the artifact is orphaned.
4. **Removed API groups.** For each API- artifact, verify the route group still exists in refreshed specs. If the tag/prefix is gone, the artifact is orphaned.
5. **Removed services.** If a service's source path no longer exists on disk, all its artifacts are candidates for orphaning.

### 7. Generate update report

Compile all findings from Steps 5-6 into a persistent update report at `.reef/update-report.json`.

**Read `${CLAUDE_PLUGIN_ROOT}/references/update-report-schema.md`** for the full JSON structure, item categories, impact classification, context impact format, and semantic summary guidelines. All rules in that reference apply.

**Key rules (do not skip):**

- **Auto-apply trivial changes immediately.** During report generation, apply all trivial items (freshness bumps, pure renames) without prompting. Set their status to `"auto_applied"`. For each: update `freshness_note` and `last_verified`, lint on write, run snapshot.
- **Substantive items stay `"pending"`** for human review.
- **`semantic_summary` is mandatory** for each service in `source_changes`. Describe what changed in meaning, not file counts.
- **New questions** discovered in Step 5b go in the report's `new_questions` array.

Write the report to `.reef/update-report.json`.

### 8. Present report and review loop

Present the report as curated, human-readable text. Do NOT dump the raw JSON.

**Report format:**

```
Update Report — {project name}                    {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources pulled: service-a (3 commits), service-b (skipped)

What changed:
  service-a — Added async fulfillment pipeline (new Celery tasks,
    new FulfillmentRecord model). Order API now accepts batch
    submissions. Legacy sync processing path removed.
  service-b — No changes.

New content discovered ({N} items):

  1. [enrichment] SCH-ORDERS-CORE
     New ReturnRequest model (status enum, refund calculation fields).
     New order_summary_mv materialized view. Will add to existing artifact.

  2. [new] SCH-ORDERS-FULFILLMENT
     New FulfillmentRecord model in orders/models/fulfillment.py.
     Will generate draft artifact.

Refreshes ({N} items):

  3. [refresh] SYS-INGEST
     3 source files changed. 2 Key Facts outdated (sync → async processing).

Orphaned ({N} items):

  4. [orphaned] SCH-ORDERS-LEGACY-CART
     Model class LegacyCart no longer in source. Mark orphaned or delete?

Context enrichment:
  order-fulfillment-srd.pdf → resolves 2 known_unknowns in PROC-PAYMENTS-ORDER-FINALIZATION

New questions surfaced:
  Q-042: The async fulfillment pipeline uses a new FULFILLMENT_QUEUE
    env var — what broker is this targeting in production?
  (Answer now, or defer — these will appear in future deep/scuba sessions)

Auto-applied ({M} items):
  SCH-INGEST-ORDER — freshness_note refreshed (no content changes)
  ... (list each auto-applied item in one line)
```

**Large changesets:** If more than 15 substantive items, show the top 15 by impact. Add: "{N} more items. Say 'show all' to see the full list."

**After the report, immediately offer to apply:**

```
Ready to update artifacts based on these changes.
  "apply all"     — update all substantive items
  "apply 1, 3"    — update specific items by number
  "skip 2"        — skip specific items
  "details 1"     — show full proposed changes for an item before deciding
  "done"          — save report, finish for now (resume later with /reef:update)
```

The user can respond in natural language. Parse their intent:
- "apply all" / "go ahead" / "update everything" → apply all pending substantive items
- "apply 1, 3" / "do the first and third" → apply specific items
- "skip 2" / "leave the new entity for now" → mark items as skipped
- "details 1" / "show me more about SYS-INGEST" → show full proposed diff (old Key Facts vs. new, exact source lines that changed, what would be added/removed)
- "done" / "that's enough for now" → save report state and exit

**Handling new questions in the review loop:**

If the report surfaced new questions, the user can answer them inline during review. When the user provides an answer:
1. Update the question's status to `"answered"` in `.reef/questions.json`.
2. Record the answer in the question entry.
3. If the answer is relevant to a pending report item, enrich that item's update with the new context. For example, if the user answers "FULFILLMENT_QUEUE targets RabbitMQ in prod" and SYS-ORDERS is pending, that fact gets woven into the SYS-ORDERS update.

If the user defers a question ("I'll answer that later"), leave it as `"unanswered"`. It will surface again in future deep or scuba sessions.
If the user dismisses a question ("not relevant"), set status to `"dismissed"`.

**`--auto` mode:** If the user invoked update with `--auto`, skip the review loop entirely. Apply all substantive items automatically. This is the escape hatch for power users, not the default.

### 9. Apply approved changes

For each approved item, process one at a time:

#### For `refresh` items:

1. Read the current artifact file.
2. Re-read the changed source files it references.
3. Compare current Key Facts against source content.
4. Determine specific updates:
   - Changed Key Facts (old value → new value).
   - New information found in sources.
   - Claims that no longer hold (source content removed or contradicted).
   - Updated `freshness_note` and `last_verified`.
5. **Glossary cross-check.** Compare the artifact's terms against GLOSSARY- artifacts. If any Key Fact or description uses a domain term inconsistently with the glossary, fix it. If the source code reveals the glossary definition is outdated, update the glossary too.
6. Write the updated artifact.

#### For `new_entity` items:

Generate a draft artifact using the same templates and conventions as snorkel. Read the relevant source files, apply the artifact contract, and write the artifact.

#### For `orphaned` items:

Present the user with a choice:

```
SCH-ORDERS-LEGACY-CART — model class LegacyCart no longer found in orders/models/

  1. Mark as orphaned (keeps the artifact with status: orphaned)
  2. Delete (removes the file and cleans up relates_to references)
```

On mark orphaned: set `status: orphaned` in frontmatter, update `freshness_note` explaining what was removed and when.
On delete: remove the artifact file, clean up `relates_to` references in other artifacts that pointed to it.

#### For `context_enrichment` items:

1. Read the context doc.
2. Read the affected artifact.
3. Cite the context doc in the artifact's `sources` field.
4. Resolve any `known_unknowns` the doc answers — move them to Key Facts with a citation.
5. Add new Key Facts if the doc reveals information not captured anywhere.

#### For `renamed` items:

Update `sources` refs in affected artifacts to reflect the new paths.

#### After writing each artifact:

**Lint immediately:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```
Parse the JSON output, filter to errors for this artifact's ID. If errors are found, fix them now.

**Then run:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
```

**Update the report:** Set the item's status to `"applied"` with a timestamp.

After each item is applied, briefly confirm to the user:
```
Applied: SYS-INGEST — 2 Key Facts updated, 1 added.
```

Then continue with the next item or return to the review loop if the user selected specific items.

### 10. Post-update

After the review loop ends (user said "done", or all items are applied/skipped), run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Update: enriched E, refreshed N, added M, orphaned K, skipped S" --reef <reef-root>
```

Replace N, M, K, S with actual counts from the report.

**Refresh CLAUDE.md** at the reef root. Update artifact counts, CON- list, SYS- list, RISK- list, and freshness date. Use the template in `${CLAUDE_PLUGIN_ROOT}/references/claude-md-template.md`.

**Archive or keep the report:**

If all items are applied or skipped (no pending items remain):
- Create `.reef/update-history/` directory if it does not exist.
- Move `update-report.json` to `.reef/update-history/update-report-{ISO-date}.json`.

If pending items remain:
- Keep `update-report.json` in place for resumption.
- Tell the user: "Report saved with {N} items remaining. Run `/reef:update` to resume."

**Present summary:**

```
Update complete.

Enriched: 2 artifacts (new content added)
  SCH-ORDERS-CORE — ReturnRequest model, order_summary_mv added
  API-ORDERS-REST — 3 new return endpoints documented

Refreshed: 3 artifacts (existing content updated)
  SYS-INGEST — 2 Key Facts updated
  SCH-INGEST-ORDER — freshness_note refreshed (auto-applied)
  PROC-INGEST-ORDER-LIFECYCLE — 1 Key Fact removed (source deleted)

New: 1 artifact created
  SCH-ORDERS-FULFILLMENT — new entity discovered

Orphaned: 1 artifact marked
  SCH-ORDERS-LEGACY-CART — model class removed from source

Skipped: 1 item
  API-PAYMENTS-WEBHOOKS — deferred to next update

Unchanged: 12 artifacts (sources not affected)
```

**Recommend next steps based on what the update surfaced:**

- If new questions were surfaced or unanswered questions remain → suggest `/reef:deep` to investigate them (or `/reef:scuba` if scuba manifest has remaining items)
- If new entities were created as draft artifacts → suggest `/reef:deep` to deepen them with worked examples and domain context
- If the update surfaced topics the user might want to explore → suggest `/reef:artifact` to dig into a specific area or capture new knowledge
- If the update was purely refreshes with no new questions → no suggestion needed, the reef is current

```
Suggested next steps:
  /reef:deep — {N} new questions surfaced during this update. Deep-dive can
    investigate these against the source code.
  /reef:artifact — Explore a topic, capture something you learned, or refine
    a specific artifact.
  /reef:scuba — {M} items remaining in scuba manifest.
```

Only show suggestions that apply. If all apply, show all. If none applies, omit this section. **Do not suggest skills that are not listed here** — these are the only valid next steps after update.

### 11. No changes detected

If the diff command reports no source changes AND structural detection finds nothing new or removed AND no new context files exist:

```
All sources unchanged since last update. API specs and ERDs have been
refreshed from current code. Your reef is fresh.
```

Source re-extraction (Step 4) always runs regardless — code may have changed even if the indexed file set hasn't. The diff in Step 5 only determines whether artifacts need content updates.

### 12. Handling renames

If the user asks to rename a service, follow the procedure in `${CLAUDE_PLUGIN_ROOT}/references/rename-cascade.md`. This covers: identifying all affected files, presenting the full impact for confirmation, applying atomically, and running post-rename commands.

## Key Rules

- **Human review is the default.** The report is a conversation, not a batch job.
- **Trivial changes are auto-applied.** Freshness bumps do not need human approval.
- **Substantive changes require review.** Key Fact changes, new entities, orphaned artifacts.
- **Reports are persistent.** The user can stop and resume across sessions.
- **Completed reports are archived.** Moved to `.reef/update-history/` for historical record.
- **Source pull is offered, not forced.** The user decides.
- **Gate check is a soft gate.** Incomplete scuba gets options, not a wall.
- **Lint-on-write after every artifact change.** No exceptions.
- **Do not summarize — explain actual changes.** "2 Key Facts outdated (sync → async)" not "some things changed."
- **Never invent facts.** If uncertain about a change, add to `known_unknowns`.
