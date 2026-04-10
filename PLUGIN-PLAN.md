# Reef — Claude Code Plugin Plan

## Context

Reef pivoted from an Electron desktop app to a Claude Code plugin on 2026-04-10 (Day 2). The Electron app proved that BYOK API costs are prohibitive ($5 for 4 artifacts from one repo using Opus). As a Claude Code plugin, Max subscribers get unlimited usage at $0 marginal cost.

The critical insight from dogfooding + comparing snorkel output vs hand-crafted artifacts: **auto-discovery alone produces shallow, README-level output.** The real value comes from Jessi's Socratic methodology — "AI found the answers. I asked the questions." The plugin must support both modes.

This plan incorporates all decisions from STRESS-TEST.md (34 questions, Sections A-H).

### What transfers from Day 1-2

- The 4-layer system prompt (`src/main/system-prompt.ts`) — Identity, Artifact Contract, Discovery Methodology, Dynamic Context
- The artifact contract — 8 types (System, Schema, API, Process, Decision, Glossary, Contract, Risk; Pattern deferred to v2)
- 8 artifact templates (from `templates/artifacts/`)
- The 33-question discovery template (`templates/discovery/understanding.md`)
- The 3 depth modes: snorkel (auto), scuba (conversational), deep (exhaustive)
- The wiki output structure (3-zone: artifacts/ + sources/ + .reef/)
- Onco-PE state management decisions (source snapshots, artifact-state, log.md, freshness triggers, change classification)
- All existing csg-knowledge-repo skills as reference patterns

### Who It's For

**Primary persona:** Platform team PM managing 5+ services. Recurring need to understand how systems connect, highest pain from undocumented boundaries, multi-source discovery is the killer feature.

**Secondary:** Tech leads inheriting unfamiliar codebases, staff engineers onboarding to new orgs, any IC who needs to answer "how does this actually work?" across multiple repos.

**Why this matters for the plugin:** The README, the questions reef-init asks, and the depth of registry file prompts are all shaped by this persona. These users don't need to be taught what a schema is — they need help extracting and organizing what they already half-know.

### What's different from the Electron app

- No custom tools — Claude Code's native Read, Write, Glob, Grep, Bash replace the 4 custom tools
- No IPC, no Electron, no React renderer
- Must be **generic** — works with any codebase, not just CSG
- Must be a shareable **plugin** with self-contained reference files
- No custom UI — terminal-only (Reef Desktop deferred to v2)

### Key decisions inherited from STRESS-TEST.md

| Decision | Source | Summary |
|----------|--------|---------|
| 8 artifact types | A4, B1 | System, Schema, API, Process, Decision, Glossary, Contract, Risk. Pattern deferred. |
| 7 relationship types | A3, B3 | parent, depends_on, refines, constrains, supersedes, feeds, integrates_with |
| 3-zone wiki structure | A4 | artifacts/ (canonical) + sources/ (evidence+registries) + .reef/ (operational state) |
| Onco-PE state management | A3 | Source snapshots at write time, artifact-state/, source-artifact-map, log.md, sessions/ |
| Freshness tracking | A3, B4 | freshness_note (human), freshness_triggers (machine), git diffs for code, content hashes for non-git |
| Change classification | A3 | new/updated/renamed/deleted/unchanged vocabulary for health check reports |
| Validation on accept | A3, F2 | Blocking (schema errors) + Warning (reference errors). 8-point validation checklist. |
| Health check (lint) | A2, C3 | 7 mechanical checks + 3 LLM-assisted checks. Ships in MVP. |
| Key Facts = claims-lite | A3, B2 | Each fact links to source, individually lintable, without C1/C2 machine IDs |
| Obsidian compatibility | B2 | Dual strategy: frontmatter relates_to for agents + body [[wikilinks]] for Obsidian graph |
| Curious Researcher personality | G3 | Subtle, no emojis, no exclamation marks. Adapts to depth mode. |
| Guided priorities, not phases | C2 | SYS- first, then fill in based on what's found. Any type at any time. Contracts always-on. |
| Question Bank | G2 | `.reef/questions.json` — user's real questions as north star, progress metric, freshness signal |
| 4-phase lifecycle | A3 | Bootstrap (human-heavy) → Expand (mixed) → Maintain (automated) → Lint (fully automated) |
| Registry files | A4 | `sources/registries/` for org charts, repo maps, service URLs — what code can't tell you |
| Local-first | D3 | Wiki + state on user's machine. Git for sharing. Privacy is a prerequisite, not a feature. |
| Compact source summaries | D1 | System prompt gets ~200 tokens per source, not full file trees. Claude navigates via tools. |

---

## The Multi-Repo Problem

Reef's core value is multi-service discovery — cross-system contracts are the "aha" moment. But Claude Code opens in one directory at a time.

**Three usage patterns:**

| Pattern | Setup | Best for |
|---------|-------|----------|
| **Monorepo / parent dir** | User opens Claude Code at a parent directory containing multiple service repos | Teams with monorepo or co-located repos |
| **Single-repo, merge later** | User creates a reef per repo, then runs `/reef-merge` to combine into a multi-system reef | Distributed teams, repos on different machines |
| **Single-repo with external paths** | reef-init accepts absolute paths to other repos as additional sources | Quick setup when all repos are local |

reef-init must explicitly handle wiki location and source scoping:
- **Where does the reef live?** Could be cwd, a subdirectory, or an external path. Default: `.reef/` in cwd.
- **What sources does it cover?** Could be cwd alone, or cwd + external repo paths. Default: cwd only.
- For single-repo reefs, Claude should note that cross-system contracts will be limited and suggest `/reef-merge` later.

---

## Plugin Structure

```
reef-plugin/
├── .claude-plugin/
│   └── plugin.json                      # Plugin manifest
├── README.md                            # Installation + usage + philosophy
├── skills/
│   ├── reef-init/
│   │   └── SKILL.md                     # Bootstrap wiki structure
│   ├── reef-snorkel/
│   │   └── SKILL.md                     # Auto-discovery surface pass
│   ├── reef-scuba/
│   │   └── SKILL.md                     # Socratic deepening
│   ├── reef-deep/
│   │   └── SKILL.md                     # Exhaustive deep dive
│   ├── reef-artifact/
│   │   └── SKILL.md                     # Create/update one artifact
│   ├── reef-update/
│   │   └── SKILL.md                     # Bulk update (re-index + refresh stale artifacts)
│   ├── reef-health/
│   │   └── SKILL.md                     # Validation + freshness check + text-rendered report
│   ├── reef-test/
│   │   └── SKILL.md                     # Test your reef (question bank)
│   └── reef-merge/
│       └── SKILL.md                     # Merge single-repo reefs into multi-system reef
├── scripts/
│   └── reef.py                          # Deterministic CLI for all mechanical operations
└── references/
    ├── artifact-contract.md             # Generic contract (adapted from CSG)
    ├── methodology.md                   # Personality + methodology + quality rubric
    ├── understanding-template.md        # 33-question discovery template
    └── templates/
        ├── system.md
        ├── schema.md
        ├── api.md
        ├── process.md
        ├── decision.md
        ├── glossary.md
        ├── contract.md
        └── risk.md
```

**Where it lives:** `~/Projects/seaof-ai/reef-plugin/` during development. Eventually its own Git repo for distribution.

---

## Scripts Layer — `scripts/reef.py`

A single Python script handles all deterministic operations. No LLM needed for any of these — they're mechanical, fast, and reliable. Skills invoke the script via Bash, read its JSON output, and act on results.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py <command> [options]
```

### Subcommands

| Command | What it does | Called by |
|---------|-------------|-----------|
| `init <path>` | Scaffold 3-zone directory structure, create project.json | `/reef-init` |
| `index` | Walk all sources in project.json, hash files (SHA-256), build `.reef/source-index.json` | `/reef-init`, `/reef-snorkel`, `/reef-update` |
| `snapshot <artifact-id>` | Capture source state (hashes + timestamps) for a specific artifact → `.reef/artifact-state/{id}.json` | `/reef-artifact`, `/reef-snorkel`, `/reef-scuba`, `/reef-deep` |
| `diff` | Compare current file hashes vs artifact-state snapshots, classify changes (new/updated/renamed/deleted/unchanged) | `/reef-update`, `/reef-health` |
| `lint` | Run 7 mechanical checks (orphans, dangling refs, source existence, schema, key facts, wikilink sync, freshness) | `/reef-health` |
| `rebuild-map` | Parse all artifact frontmatter, rebuild `source-artifact-map.json` | `/reef-artifact`, `/reef-update` |
| `rebuild-index` | Regenerate `index.md` from artifact frontmatter | `/reef-artifact`, `/reef-update` |
| `log <message>` | Append timestamped entry to `log.md` | All skills |

### Output format

Every command outputs structured JSON to stdout. Skills read this and present results to the user or feed them into LLM reasoning.

```json
// reef.py diff
{
  "sources": {
    "cdm": { "new": 1, "updated": 3, "renamed": 0, "deleted": 0, "unchanged": 338 },
    "ctl": { "new": 0, "updated": 0, "renamed": 0, "deleted": 0, "unchanged": 218 }
  },
  "affected_artifacts": ["SYS-CDM", "SCH-CDM-STUDY", "PROC-CDM-CASE-LIFECYCLE"],
  "details": [
    { "file": "src/models/study.py", "classification": "updated", "old_hash": "a1b2c3...", "new_hash": "d4e5f6..." }
  ]
}
```

```json
// reef.py lint
{
  "errors": [
    { "check": "schema", "artifact": "SCH-CDM-STUDY", "issue": "missing required field: freshness_note" }
  ],
  "warnings": [
    { "check": "dangling_ref", "artifact": "SYS-CDM", "issue": "relates_to target [[SYS-NONEXISTENT]] not found" }
  ],
  "info": [
    { "check": "freshness", "artifact": "PROC-CDM-CASE-LIFECYCLE", "issue": "source cdm:src/services/case.py changed since last write" }
  ],
  "summary": { "errors": 1, "warnings": 1, "info": 1, "artifacts_checked": 12 }
}
```

### Why a single script, not many

One file with subcommands means: one dependency to manage, one thing to install, one path to resolve. The script imports only Python stdlib (`os`, `hashlib`, `json`, `yaml`, `pathlib`, `glob`). The only external dependency is `pyyaml` for frontmatter parsing — installed via `SessionStart` hook.

### Dependency installation

`plugin.json` includes a `SessionStart` hook:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c 'import yaml' 2>/dev/null || python3 -m pip install --quiet pyyaml"
          }
        ]
      }
    ]
  }
}
```

### How skills use it

Example — how `/reef-health` combines script output with LLM reasoning:

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint` → get JSON with all 7 mechanical check results
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py diff` → get change classification
3. LLM reads the JSON, formats the text-rendered report (Unicode blocks, tables)
4. If user opts in to LLM checks: Claude reads flagged artifacts and does checks 8-10 (empty unknowns, contradictions, stale claims)
5. LLM presents combined report with actionable recommendations

The script does the *finding*. The LLM does the *interpreting and presenting*.

---

## Wiki Output Structure (3-Zone)

From STRESS-TEST A4 — what `/reef-init` creates on disk:

```
<project>/
├── index.md                          # Auto-generated catalog
├── log.md                            # Append-only wiki evolution log (Onco-PE)
├── artifacts/                        # Zone 1: canonical knowledge
│   ├── systems/
│   ├── schemas/
│   ├── apis/
│   ├── processes/
│   ├── decisions/
│   ├── glossary/
│   ├── contracts/
│   └── risks/
├── sources/                          # Zone 2: evidence + registries
│   ├── registries/                   #   repos.yaml, org-chart.yaml, etc.
│   └── raw/                          #   API specs, schema dumps, exported docs
└── .reef/                            # Zone 3: operational state (hidden)
    ├── project.json                  #   name, sources, created date
    ├── source-index.json             #   file index with lastModified + contentHash
    ├── artifact-state/               #   per-artifact source snapshots at write time
    │   └── {artifact-id}.json        #     sources read, hashes, freshness status
    ├── source-artifact-map.json      #   reverse index (source file → which artifacts)
    ├── questions.json                #   question bank for "Test Your Reef"
    ├── sessions/                     #   lightweight session logs
    │   └── {timestamp}.json          #     sources scanned, artifacts created/flagged
    └── .gitignore                    #   excludes sessions/, keeps everything else
```

---

## Skill Breakdown

### `/reef-init` — Bootstrap

Creates the 3-zone wiki structure. Handles scoping and wiki location.

1. Check if `.reef/` already exists → report or offer reset
2. **Scope the reef:**
   - Ask: project name, what system(s) to document
   - Ask: where should the reef live? Default: `.reef/` + `artifacts/` + `sources/` in cwd. Alternative: external path.
   - Ask: what source directories to analyze? Default: cwd. Can add absolute paths to external repos.
   - If single-repo: note that cross-system contracts will be limited. "You can create reefs for other services and merge them later with `/reef-merge`."
3. Run `reef.py init <path>` → scaffold 3-zone directory structure, create project.json
4. Run `reef.py index` → walk all sources, hash files, build `.reef/source-index.json`
5. Ask about organizational context: "Do you have info about team ownership, service URLs, or repo mapping? I can help create registry files." → create `sources/registries/` entries using these structures:

   ```yaml
   # sources/registries/repos.yaml
   repos:
     - name: service-name
       full_name: Human-Readable Service Name
       domain: domain-label
       team: owning-team
       description: One-line description
   ```

   ```yaml
   # sources/registries/org-chart.yaml
   teams:
     - name: team-name
       lead: TBD
       systems: [service-a, service-b]
       domain: domain-label
   ```

   ```yaml
   # sources/registries/raci.yaml (optional)
   decisions:
     - topic: "Schema changes for service-x"
       responsible: team-name
       accountable: team-lead
       consulted: [other-team]
       informed: [stakeholders]
   ```

6. Ask about documentation sources: "Do you have architecture docs, SRS, wiki exports, or design docs that describe these systems? They dramatically improve terminology accuracy." → note doc paths in `project.json` for scuba/deep to reference
7. Optionally: "What questions do you need this wiki to answer?" → seed `.reef/questions.json`
8. Run `reef.py log "Project created: {name}, {n} sources, {n} files"` → append to log.md
9. Suggest next step: `/reef-snorkel` for auto-discovery or `/reef-scuba` for guided exploration

### `/reef-snorkel` — Auto-Discovery Surface Pass

Rapidly generates 3-6 surface-level draft artifacts. No questions asked. (STRESS-TEST C1: Snorkeling mode)

1. Run `reef.py index` → refresh source-index.json. Read `.reef/project.json` for sources. Read `references/artifact-contract.md`. Glob existing artifacts.
2. For each source: structural scan (2-level dir tree, README, routers/handlers, models/schemas, config, tests)
3. Generate artifacts in priority order: SYS- first, then SCH-, API-, GLOSSARY- as discovered
4. Each artifact:
   - Valid frontmatter with all required fields
   - Key Facts with source refs (repo-relative paths) — individually verifiable
   - Honest `known_unknowns` (STRESS-TEST: "honest gaps beat confident lies")
   - `status: "draft"`
   - `freshness_note` — when to re-verify
   - `freshness_triggers` — machine-checkable source file paths
   - `## Related` section with `[[wikilinks]]` matching frontmatter `relates_to` (Obsidian dual strategy)
5. **Validation on accept** (STRESS-TEST A3, F2):
   - Blocking: frontmatter schema, required fields, id/filename match, valid enums, Key Facts present
   - Warning: relates_to targets exist, sources refs resolve, body sections present
6. **Source snapshot at write time** (Onco-PE): run `reef.py snapshot <artifact-id>` → capture content hash + last modified of every source file Claude read
7. Run `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log "Created {id}"`
8. After 3-6 artifacts, **stop**. Summarize what was found. Invite depth.

**Personality:** Curious Researcher. Present-participle narration ("Reading src/models/...", "Found 4 independent applications..."). No emojis. No exclamation marks.

**Key constraint from dogfooding:** One artifact at a time. Don't batch-dump.

**Cross-system contracts always-on** (STRESS-TEST C2): when Claude reads code that calls another system (webhooks, API clients, shared DB access), it flags the boundary immediately — doesn't wait.

### `/reef-scuba` — Socratic Deepening

Interactive, question-driven knowledge extraction. This is where the real value lives. (STRESS-TEST C1: Scuba-diving mode)

1. Load context (project.json, existing artifacts, contract, question bank)
2. Determine entry point:
   - (a) User names a system or topic — start there
   - (b) User has snorkel drafts — offer to deepen one
   - (c) User wants full question list — generate from understanding template
3. If generating questions: read `references/understanding-template.md`, adapt the 33 baseline questions based on structural scan, save to `.reef/{system}-understanding.md`
4. **Guided priorities, not rigid phases** (STRESS-TEST C2): establish system boundaries first (SYS-), then fill in based on what's found. Any artifact type at any time. If a PROC- is proposed before its parent SYS- exists, warn (not block).
5. Work through questions one at a time:
   - Read source code to find the answer
   - Structure as: Fact / Why it matters / Source / Confidence / Open question
   - Create or update the target artifact (full validation + source snapshot)
6. After each artifact: **"What did I get wrong? What am I missing?"**
7. Proactively suggest questions the code alone won't answer:
   - Team ownership, organizational context → registry files
   - Decision rationale → DEC- artifacts
   - Operational reality vs design intent (STRESS-TEST Q3 from presentation)
   - Cross-system boundaries → CON- artifacts
8. **Suggest documentation sources when uncertain:** If Claude notices terminology ambiguity or shallow context, suggest the user provide architecture docs, SRS, or wiki exports. When docs exist, read them before code — docs provide the lens for interpreting code. After doc ingestion, offer to correct existing artifacts.
9. If question bank exists (`.reef/questions.json`), prioritize exploration toward unanswered questions (STRESS-TEST G2)

**Core principle (from presentation):** "AI reads code. It can't know which gaps are dangerous or which ambiguities cause real problems downstream. That part is yours."

### `/reef-deep` — Exhaustive Deep Dive

Maximum depth on a specific area. (STRESS-TEST C1: Deep-diving mode)

1. User directs Claude to a specific system, subsystem, or topic
2. Claude reads entire directories, traces execution paths, maps every function that materially affects runtime
3. Dense Key Facts with precise line citations (e.g., `src/services/case.py:L45-89`)
4. 5+ facts per artifact minimum
5. The user provides domain framing that reshapes how Claude interprets the code (STRESS-TEST C1: the PROC-RDP-CS-TASK-PLAYBOOK example — "treat every function that materially affects runtime behavior as an execution unit")

This mode is for critical systems where shallow reading misses the real behavior.

### `/reef-artifact` — Create/Update Single Artifact

Workhorse skill for creating or updating one artifact with full contract enforcement.

1. Read `references/artifact-contract.md` (always)
2. Create mode: determine type → generate ID → reference template from `references/templates/`
3. Update mode: read existing artifact → identify changes → preserve unaffected fields → bump `last_verified`
4. Gather evidence: read source code, check relates_to edges, trace every claim
5. Write following contract exactly:
   - All frontmatter fields (deterministic ordering per STRESS-TEST B2)
   - Required body sections per type
   - Key Facts with source citations
   - `## Related` with `[[wikilinks]]` matching `relates_to`
   - `freshness_note` and `freshness_triggers`
6. **Validation on accept** (blocking + warning)
7. Run `reef.py snapshot <artifact-id>` → capture source state at write time
8. Run `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log "Created/Updated {id}"`

### `/reef-health` — Validation & Freshness (Lint)

The lint operation (STRESS-TEST A2, C3). Ships in MVP — not deferred.

**Step 1:** Run `reef.py lint` + `reef.py diff` → get JSON results for all 7 mechanical checks:
1. Orphan detection — artifacts with no incoming relates_to (except SYS- roots)
2. Dangling references — relates_to targets that don't resolve to existing artifact IDs
3. Source file existence — sources[].ref files still exist on disk
4. Frontmatter schema — required fields, valid enums, id/filename match, dates parseable
5. Key Facts without source links
6. Wikilink/frontmatter sync — `## Related` matches `relates_to`
7. Freshness — artifacts whose source files changed since write time (via `.reef/artifact-state/` snapshots)

**Step 2:** LLM reads the JSON output and formats the text-rendered report.

**LLM-assisted checks (opt-in, more expensive):**
8. Empty `known_unknowns` — ask Claude to review if genuinely no gaps
9. Contradiction detection — Claude reads artifact pairs sharing relates_to targets, checks for conflicting Key Facts
10. Stale claims — Claude re-reads source files referenced by Key Facts, checks if claims still hold

**Change classification vocabulary** (STRESS-TEST A3):
| Classification | Meaning | Action |
|---|---|---|
| `new` | file appeared | flag artifacts in same module |
| `updated` | content hash changed | flag artifacts referencing this file |
| `renamed` | path changed, content similar | update source refs |
| `deleted` | file removed | warn — artifacts may be invalid |
| `unchanged` | no movement | skip |

**Text-rendered report:**

Health output uses Unicode block characters for a visual summary in the terminal:

```
Reef Health — my-project                         2026-04-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources          Files    Seen   Deep   Freshness
─────────────────────────────────────────────────
cdm              342      287    94     ████████░░ aging
ctl              218      180    42     ██████████ fresh
rdp              156       38     0     ██░░░░░░░░ stale

Artifacts        Total    Fresh  Aging  Stale  Errors
─────────────────────────────────────────────────
SYS-             3        2      1      0      0
SCH-             4        3      0      1      1
API-             2        2      0      0      0
PROC-            5        3      2      0      0
CON-             1        0      1      0      1

Issues: 2 errors · 4 warnings · 1 info
Run /reef-update to refresh stale artifacts.
```

Also appended to `log.md` as a timestamped entry.

### `/reef-update` — Bulk Update (Re-index + Refresh)

The "Update Wiki" operation from the Electron app. Re-indexes all sources, detects what changed, and updates affected artifacts in one pass.

1. Run `reef.py index` → re-index all sources, rebuild `.reef/source-index.json` with current file hashes
2. Run `reef.py diff` → compare against `.reef/artifact-state/` snapshots, classify changes (new/updated/renamed/deleted/unchanged)
3. LLM reads JSON output and presents change summary to user:
   ```
   Source changes since last update:
     cdm: 3 updated, 1 new, 0 deleted
     ctl: 0 updated, 0 new, 0 deleted
     rdp: 8 updated, 2 new, 1 deleted

   Affected artifacts: SYS-CDM, SCH-CDM-STUDY, PROC-CDM-CASE-LIFECYCLE, PROC-RDP-...
   ```
4. For each affected artifact, Claude re-reads the changed source files and proposes updates
5. User accepts/skips each update (same validation-on-accept as `/reef-artifact`)
6. Run `reef.py snapshot <artifact-id>` for each updated artifact
7. Run `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log "Updated {n} artifacts"`

**Key difference from `/reef-health`:** Health *reports* problems. Update *fixes* them. Health is read-only. Update writes artifacts.

### `/reef-merge` — Combine Reefs (v1.1)

Merges single-repo reefs into a multi-system reef. Solves the core limitation of Claude Code opening in one directory.

1. User provides paths to 2+ existing reef directories (each with `.reef/` and `artifacts/`)
2. Read each reef's `project.json` and artifact index
3. Copy artifacts into a new combined reef, preserving IDs and source refs
4. **Conflict detection:** if two reefs have artifacts with the same ID, flag for user resolution
5. **Cross-system discovery:** after merge, Claude scans for cross-system boundaries that were invisible in single-repo reefs → propose CON- artifacts
6. Update all `relates_to` edges to reflect the combined graph
7. Rebuild `index.md`, `source-artifact-map.json`, `log.md`

This is the path from "I documented each service separately" to "now I can see how they connect."

**Deferred to v1.1** — requires the single-repo flow to be solid first. But the wiki structure (IDs, source refs, frontmatter) is designed to make merging possible from day one.

### `/reef-source` — Extract Raw Specs from Code (v1.1)

Generates raw evidence files that SCH- and API- artifacts can reference.

1. **OpenAPI extraction:** Scan for FastAPI/Flask/Express route definitions → generate `sources/raw/{service}/openapi.json`
2. **ERD/schema extraction:** Scan for SQLAlchemy/Django/Prisma models → generate `sources/raw/{service}/schema.md` (entity list with fields, types, relationships)
3. **Ingest user-provided docs:** User points to PRDs, SRDs, architecture docs, wiki exports → copy to `sources/docs/` with metadata

These are raw evidence files, not artifacts. SCH- and API- artifacts *interpret* them — adding business rules, usage patterns, deprecation status, cross-system dependencies.

**Deferred to v1.1** — snorkel/scuba can work without raw specs. But when specs exist, artifact quality improves significantly.

### `/reef-test` — Test Your Reef (Question Bank)

From STRESS-TEST G2 — the most meaningful progress metric.

1. Read `.reef/questions.json` (seeded during init or added anytime)
2. For each question, Claude answers grounded in existing artifacts (not source code)
3. Rate each answer: fully answered (cites specific artifacts) / partially answered / not answerable
4. Surface gaps: "DAIP is shallow — 3 Key Facts, needs deeper exploration"
5. Report: "7/12 questions answered fully. 3 need deeper exploration. 2 unanswerable with current artifacts."
6. **Gap-to-action loop** (STRESS-TEST G2): for unanswered questions, offer "Want me to deep-dive into [area] to fill this gap?" → transitions naturally into scuba/deep mode

Users can add questions anytime. The question bank serves as:
- **North star** — the reef exists to answer them
- **Discovery guide** — unanswered questions tell Claude where to focus in scuba
- **Ongoing health check** — run "Test" anytime; if a previously-answered question drops, that's freshness signal

**Text-rendered report:**

```
Test Your Reef — my-project                      2026-04-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: ████████████░░░░░░░░ 7/12 questions answered

 ✓  How does CDM handle case state transitions?      → PROC-CDM-CASE-LIFECYCLE
 ✓  What data flows from CDM to RDP?                 → CON-CDM-RDP-FEED, SYS-RDP
 ✓  Who owns the annotation review workflow?          → SYS-CTL, PROC-CTL-REVIEW
 ~  How does auth work across services?               → partial: SYS-DAIP (shallow)
 ~  What happens when image dedup finds a match?      → partial: known_unknown in SYS-CDM
 ~  How are Prefect flows scheduled?                  → partial: SYS-RDP (no PROC- yet)
 ✗  What's the disaster recovery plan?
 ✗  How do schema migrations get coordinated?

Gaps to explore:
  DAIP is shallow — 3 Key Facts, needs /reef-scuba
  RDP has no PROC- artifacts — run /reef-deep on rdp:src/flows/
```

---

## Adapting the Artifact Contract for Generic Use

| Field | CSG Version | Reef Version | Rationale (STRESS-TEST) |
|-------|-------------|-------------|------------------------|
| `domain` | `cdm\|ctl\|rdp\|daip\|shared` | Free-form string | A4: can't productize org-specific enums |
| `owning_domain` | `csg\|platform` | Removed | A4: too org-specific |
| `scope` | Predefined breast/chest/etc | Free-form string | A4: too org-specific |
| `source_of_truth_status` | `canonical\|derived\|external` | Removed | A4: would be "derived" on 95% of artifacts |
| `verification_needed` | boolean | Removed | A4: freshness system replaces with something more granular |
| `owner` | Required | Optional | A4: users won't know what to put |
| `sources[].ref` | `label:path` format | Repo-relative paths from cwd | D2: Claude Code cwd is context |
| `freshness_note` | Not in original CSG contract | Added (MVP) | A3: human-readable re-verify guidance |
| `freshness_triggers` | Not in original CSG contract | Added (MVP) | A3: machine-checkable source file paths |
| `tags` | Not in original CSG contract | Added | B2: Obsidian tag pane + graph filtering |
| `aliases` | Not in original CSG contract | Added | B2: Obsidian quick switcher |

**Preserved unchanged:** All 8 types, all formatting rules, all body section requirements, 7 relates_to edge types, frontmatter quoting rules, determinism rules (sorted arrays, stable field ordering).

**Frontmatter field ordering** (STRESS-TEST B2): id, type, title, domain, status, last_verified, freshness_note, freshness_triggers, known_unknowns, tags, aliases, relates_to, sources, notes.

---

## Supporting Reference Files

### `references/artifact-contract.md`
Adapted from `docs/artifact-contract.md` in csg-knowledge-repo. All CSG-specific enums generalized. Adds freshness_note, freshness_triggers, tags, aliases. Includes the Obsidian dual-strategy (frontmatter for agents, body wikilinks for graph). Includes the validation-on-accept checklist (8 blocking + warning checks).

### `references/methodology.md`
New file containing:
- Curious Researcher personality definition (from `IDENTITY` in system-prompt.ts)
- The 3 depth modes and their behavioral differences (from STRESS-TEST C1)
- Core principle: "AI found the answers. I asked the questions."
- The 3 foundational questions (from presentation): How keep from going stale? How know it's true? How find what it needs?
- Anti-patterns: never invent, never use absolute paths, honest gaps beat confident lies
- The 4-phase lifecycle: Bootstrap → Expand → Maintain → Lint (STRESS-TEST A3)
- The 9-question quality stress test (from presentation slides 20-29)
- Key Facts as claims-lite: each fact linked to source, individually lintable (STRESS-TEST A3)
- Why SCH- and API- artifacts are interpretations, not spec restatements (STRESS-TEST B1)
- **UX Language Guidelines:** Reef metaphor for status, plain language for CTAs. The metaphor adds warmth and personality to status reporting, never friction to actions.

  | Context | Use | Example |
  |---------|-----|---------|
  | Status / health | Reef metaphor | "Your reef is aging" / "3 artifacts growing stale" |
  | Call to action | Plain language | "Run `/reef-health`" / "Deepen with `/reef-scuba`" |
  | Progress narration | Present participle | "Reading src/models/..." / "Found 4 independent applications..." |
  | Error / gap | Honest, not alarming | "I couldn't verify this claim — adding to known unknowns" |

  Principle: The user should never have to decode the metaphor to understand what to do.

### `references/understanding-template.md`
Adapted from `templates/discovery/understanding.md`. Same 33 questions across 7 phases (A-G). CSG references removed. Generalized for any codebase. Includes adaptive guidance: when to add questions (multi-app, multiple DBs, complex auth) and when to remove (simple systems).

### `references/templates/*.md`
8 templates adapted from `templates/artifacts/` (all except Pattern, which is deferred). CSG-specific defaults removed. Each includes:
- Required frontmatter fields with placeholders
- Required body sections for the type
- `## Related` section template
- Notes on what this artifact type is for (from STRESS-TEST B1)

---

## Implementation Phases

### Phase 1: Scaffold + Script + References (~3 hours)

Create the plugin directory structure, the mechanical script, and all reference files.

1. Create `reef-plugin/.claude-plugin/plugin.json` (with `SessionStart` hook for pyyaml)
2. Write `scripts/reef.py` — all 8 subcommands (init, index, snapshot, diff, lint, rebuild-map, rebuild-index, log)
3. Write `references/artifact-contract.md` (adapt from CSG, apply all STRESS-TEST decisions)
4. Write all 8 `references/templates/*.md` (adapt from CSG)
5. Write `references/understanding-template.md` (adapt from CSG discovery template)
6. Write `references/methodology.md` (extract from system-prompt.ts + STRESS-TEST + presentation)
7. Write `skills/reef-init/SKILL.md`

**Verify:** Run `reef.py init` + `reef.py index` directly. Then run `/reef-init` in a test directory. Check all 3 zones created, project.json well-formed, source-index.json populated, log.md initialized.

### Phase 2: Snorkel (~2 hours)

The first-impression skill. Demonstrates what Reef does.

7. Write `skills/reef-snorkel/SKILL.md` — containing:
   - Identity/personality block (Curious Researcher, from system-prompt.ts Layer 1)
   - Artifact contract summary (key rules — skill references the full file)
   - Snorkel-specific methodology (from system-prompt.ts Layer 3)
   - Compact source summary generation (STRESS-TEST D1: ~200 tokens per source, not full tree)
   - Validation-on-accept instructions
   - Source snapshot instructions
8. Test against csg-case-curator-backend
9. Validate: frontmatter parses, source refs real, Key Facts have citations, known_unknowns honest, source snapshots captured

### Phase 3: Artifact + Health + Update (~3 hours)

The workhorse skill, the lint operation, and the bulk update — all MVP.

10. Write `skills/reef-artifact/SKILL.md` (model on existing `/artifact` skill)
11. Write `skills/reef-health/SKILL.md` — mechanical checks (1-7), LLM checks (8-10) as opt-in, text-rendered report
12. Write `skills/reef-update/SKILL.md` — re-index, detect changes, propose updates, text-rendered change summary
13. Test: create an artifact, run health check, corrupt an artifact, re-run health check. Test update after modifying a source file.

### Phase 4: Scuba + Deep (~3 hours)

The methodologically complex skills — where the real value lives.

14. Write `skills/reef-scuba/SKILL.md` — containing:
    - Conversational personality mode
    - Question generation from understanding template
    - Guided priorities (not rigid phases)
    - "What did I get wrong?" loop
    - Registry file creation prompts
    - Doc source suggestion when terminology is ambiguous
    - Question bank integration
15. Write `skills/reef-deep/SKILL.md` — exhaustive mode
16. Test a full scuba session: generate questions → work through 3-4 → compare output to SYS-CDM quality

### Phase 5: Test + Polish (~1 hour)

17. Write `skills/reef-test/SKILL.md` (question bank validation, text-rendered progress report)
18. Write `README.md` with installation, usage, philosophy, privacy note
19. End-to-end test: init → snorkel → scuba → update → health → test

### Phase 6: v1.1 Skills (post-MVP)

20. Write `skills/reef-merge/SKILL.md` — combine single-repo reefs
21. Write `skills/reef-source/SKILL.md` — extract OpenAPI/ERD from code, ingest user docs
22. Test merge with 2 separate reefs → verify CON- artifacts proposed at boundaries

---

## Verification

1. **Init smoke test:** `/reef-init` in fresh directory — all 3 zones, project.json, log.md, registries prompt
2. **Snorkel against real code:** 3-6 artifacts, valid frontmatter, real sources, Key Facts with citations, source snapshots in `.reef/artifact-state/`
3. **Quality comparison:** Snorkel output vs hand-crafted SYS-CDM — honest draft with clear known_unknowns (not a README paraphrase)
4. **Scuba round-trip:** Deepen a snorkel draft → approaches SYS-CDM quality (owns/doesn't own, domain behavior, dependencies table)
5. **Health catches issues:** Corrupt artifacts → health flags all 7 mechanical problems + warns on references
6. **Test your reef:** Seed 5 real questions → run `/reef-test` → verify artifact grounding and gap detection
7. **Update detects changes:** Modify a source file → run `/reef-update` → verify it flags affected artifacts and proposes updates
8. **Cross-project portability:** Full flow on non-CSG codebase → nothing assumes CSG structure
9. **Obsidian compatibility:** Open wiki in Obsidian → graph view shows nodes + edges → Dataview queries work on frontmatter
10. **Text reports render correctly:** `/reef-health` and `/reef-test` produce readable Unicode block graphics in the terminal

---

## Key Architectural Decisions

**Why 8 MVP skills + 2 v1.1 skills?** Each skill has a distinct behavior and personality. Snorkel suppresses questions; scuba is built on questions; deep traces execution paths; update detects and fixes staleness; health reports without changing. Keeping them separate also keeps each SKILL.md at reasonable context size.

**Why no MCP server?** Claude Code's native tools cover everything. No runtime dependencies, no installation friction.

**Why bundle the contract?** The artifact contract is Reef's core IP — the validated 8-type taxonomy, frontmatter schema, and quality standards. Bundling ensures every user gets the proven rules. (STRESS-TEST H1: methodology is the moat, product bundles it.)

**Why repo-relative paths?** In Claude Code, cwd is the context. `src/models/study.py` is what tools naturally produce and consume.

**Why source snapshots at write time?** (STRESS-TEST A3, Onco-PE) Cannot be backfilled. Enables the entire freshness/lint story. Cheap (~20 lines of state per artifact).

**Why Obsidian dual strategy?** (STRESS-TEST B2) Frontmatter `relates_to` for agents/Dataview. Body `[[wikilinks]]` for Obsidian graph view (which only reads body links). Both generated, validation checks sync.

---

## Success Criteria

The plugin MVP is successful if:

1. **First artifacts appear within 5 minutes of `/reef-snorkel` — with zero questions asked.**
   - Surface pass auto-generates 3-6 artifacts (SYS-, SCH-, API-, GLOSSARY-) from a single source.
   - Artifacts have valid frontmatter, Key Facts with source refs, honest known_unknowns, and freshness notes.
   - After 30 minutes of `/reef-scuba`, the wiki has 8-12+ artifacts with organizational depth.

2. **The wiki is useful without Reef — and beautiful in Obsidian.**
   - Output is plain markdown. Readable in Obsidian, VS Code, GitHub, or any editor.
   - index.md serves as a navigable entry point with `[[wikilinks]]`.
   - `[[wikilinks]]` in Key Facts, prose, and `## Related` create a connected graph in Obsidian.
   - `tags` and `aliases` enable Obsidian filtering and quick switcher.
   - Frontmatter `relates_to` with typed relationships enables Dataview queries.

3. **The experience feels like collaborative discovery, not document generation.**
   - Three depth modes work as expected: snorkel produces batch artifacts, scuba feels conversational, deep produces exhaustive references.
   - Claude's curious researcher personality makes the session engaging, not transactional.
   - The user feels like they're teaching Claude about their systems.
   - Artifacts improve when the user corrects Claude.
   - Progressive disclosure — conversation, not questionnaire.

4. **Cross-system contracts are the "aha" moment.**
   - After documenting 2+ systems, Claude identifies boundaries and proposes CON- artifacts.
   - These artifacts surface things the user knew implicitly but never documented.

5. **Validation catches errors before they hit disk.**
   - Frontmatter schema errors are blocked.
   - Dangling references are warned.
   - Source snapshots are captured for every accepted artifact.

6. **The wiki can be maintained, not just created.**
   - `/reef-health` identifies stale artifacts, orphans, and broken refs.
   - log.md provides a readable timeline of the wiki's evolution.
   - `/reef-test` against the question bank shows whether the wiki is actually answering the user's real questions.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SKILL.md context size limits — skills can't inject unlimited methodology | Medium | High | Keep each SKILL.md focused. Heavy reference material goes in `references/` files that skills read on demand. |
| 7 skills overwhelm new users (too many entry points) | Medium | Medium | README provides a clear 3-step flow: init → snorkel → scuba. Other skills are "when you need them." |
| Skill execution quality varies with model (Sonnet vs Opus) | Medium | Medium | Test all skills on both Sonnet and Opus. Snorkel and health should work well on Sonnet; scuba and deep may benefit from Opus. Document in README. |
| Claude doesn't follow artifact contract consistently | Medium | High | `/reef-artifact` always reads the full contract before writing. Validation-on-accept catches deviations. |
| Plugin discovery/installation friction | High | Medium | Clear README with one-line install. Eventually plugin marketplace. |
| Claude Code version compatibility | Low | Medium | Use only stable Claude Code features (skills, plugins, native tools). No experimental APIs. |
| Source snapshots add complexity for minimal perceived value | Low | Medium | Snapshots are invisible to users — they power health check behind the scenes. Worth the ~20 lines of state per artifact. |
| Users don't return for scuba after snorkel | Medium | High | Snorkel output explicitly flags gaps and invites depth. Question bank gives users a reason to come back. |
| Large monorepos overwhelm snorkel (too many files) | Medium | Medium | Compact summaries (~200 tokens/source). Claude navigates via tools, doesn't memorize entire trees. Reef-init asks user to scope to specific directories. |

---

## Roadmap

### v1.0 — Plugin MVP (current plan)
- 8 skills: init, snorkel, scuba, deep, artifact, update, health, test
- 8 artifact types, 7 relationships, 3-zone wiki
- Full methodology in reference files
- Text-rendered health and progress reports
- Obsidian-compatible out of the box

### v1.1 — Multi-Repo + Raw Specs
- `/reef-merge` — combine single-repo reefs into multi-system reef, discover cross-system contracts
- `/reef-source` — extract OpenAPI/ERD from code, ingest user-provided PRDs/SRDs/specs into `sources/docs/`
- Freshness diffing against git history (detect changed source files since last artifact write)
- Dependency tracking via source-artifact-map (when artifact X changes, flag artifacts that depend on it)

### v1.2 — Richer Discovery
- Pattern artifact type (emerges from cross-system synthesis)
- Process archetype detection (lifecycle vs. workflow vs. boundary)
- Better doc source integration (suggest docs proactively, read before code)
- Obsidian plugin for deeper integration beyond native graph compatibility

### v2.0 — Reef Desktop
- Electron visual layer that reads wiki output from the plugin
- Ocean depth design system (seven-blue palette + coral, typography, ✱ logo as health indicator)
- Coverage indicator (dual-layer bars showing breadth vs depth per source)
- Session summary cards, artifact ribbon, health bitmap

### v2.1 — Output Layer + Collaboration
- Export to Confluence / Notion / GitBook / HTML (tool-agnostic)
- "Share via Git" action (init repo + push wiki to remote)
- Domain-specific type extensions (Onco-PE style)

### v3.0 — Agent Autonomy + Downstream Specs
- Scheduled wiki updates (cron-based re-indexing and artifact refresh)
- CI/CD integration (update wiki on PR merge)
- Multi-agent: one agent per system, coordinator agent for contracts
- **Work zone:** Planning workspace where agents use the wiki to draft PRDs, SRDs, impact analyses — grounded in structured knowledge, not hallucination
- **Spec → code loop:** Publish SRDs as markdown to GitHub. Agents read wiki + SRD + codebase to implement with full context. The closed loop: code → knowledge → specs → code

### Not in scope (separate workstreams)
- seaof.ai branding / website
- Plugin marketplace distribution — after testing with early users
- LLM-assisted lint checks 8-10 — ship as opt-in in v1.0, refine based on usage

---

## Privacy Note (for README)

Reef skills read source code files and pass their contents to Claude for analysis. In Claude Code:
- **Max subscribers:** Code is processed under Anthropic's usage policy for the Claude subscription.
- **No data leaves your machine** except through Claude Code's normal operation.
- **Wiki output is local-first:** All artifacts, state, and logs stay on your filesystem.
- The plugin itself stores no credentials and makes no network requests.
