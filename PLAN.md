# Reef — Build Plan

## What Reef Is

Reef is a Claude Code plugin that builds structured knowledge repositories from codebases. You point it at source code, and through a combination of automated discovery and Socratic questioning, it produces a wiki of interlinked markdown artifacts — systems, schemas, APIs, processes, decisions, glossaries, contracts, and risks.

Every claim in a Reef wiki traces to source code, a document, or an explicit "known unknown." The output is plain markdown with YAML frontmatter — readable in Obsidian, VS Code, GitHub, or any text editor. No vendor lock-in. No database. Local-first.

**Core insight:** Auto-discovery alone produces shallow, README-level output. The real value comes from human-guided exploration — "AI found the answers. I asked the questions." Reef supports both: fast surface scans for instant value, and deep Socratic sessions for institutional-grade knowledge.

## Who It's For

**Primary:** Platform team PM managing 5+ services. Recurring need to understand how systems connect, highest pain from undocumented cross-system boundaries, multi-source discovery is the killer feature.

**Secondary:** Tech leads inheriting unfamiliar codebases, staff engineers onboarding to new orgs, any IC who needs to answer "how does this actually work?" across multiple repos.

These users don't need to be taught what a schema is — they need help extracting and organizing what they already half-know.

## Core Value Proposition

1. **Structured, not freeform.** 8 artifact types with enforced schemas. Every artifact has typed relationships, source citations, freshness tracking, and explicit gaps. Agents and humans can both consume the output.
2. **Progressive depth.** Snorkel gives you 3-6 draft artifacts in 5 minutes with zero questions. Scuba deepens them through conversation. Deep dives trace execution paths line by line.
3. **Cross-system contracts.** When you document 2+ systems, Reef identifies boundaries and proposes contract artifacts — surfacing things you knew implicitly but never wrote down.
4. **Maintainable, not just created.** Source snapshots at write time, mechanical health checks, change classification, and a question bank that tells you whether the wiki is actually answering your real questions.
5. **Obsidian-native.** `[[wikilinks]]` in prose, typed relationships in frontmatter, tags and aliases for filtering. Open the wiki in Obsidian and get a connected knowledge graph immediately.

---

## The Multi-Repo Problem

Reef's core value is multi-service discovery — cross-system contracts are the "aha" moment. But Claude Code opens in one directory at a time.

**Three usage patterns:**

| Pattern | Setup | Best for |
|---------|-------|----------|
| **Monorepo / parent dir** | Open Claude Code at a parent directory containing multiple service repos | Teams with monorepo or co-located repos |
| **Single-repo, merge later** | Create a reef per repo, then run `/reef-merge` to combine | Distributed teams, repos on different machines |
| **Single-repo with external paths** | reef-init accepts absolute paths to other repos as additional sources | Quick setup when all repos are local |

reef-init explicitly handles wiki location and source scoping:
- **Where does the reef live?** Default: cwd. Alternative: external path.
- **What sources does it cover?** Default: cwd only. Can add absolute paths to external repos.
- For single-repo reefs, Claude notes that cross-system contracts will be limited and suggests `/reef-merge` later.

---

## Plugin Structure

```
reef-plugin/
├── .claude-plugin/
│   └── plugin.json                      # Plugin manifest (SessionStart hook for pyyaml)
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
│       └── SKILL.md                     # Merge single-repo reefs (v1.1)
├── scripts/
│   └── reef.py                          # Deterministic CLI for all mechanical operations
└── references/
    ├── artifact-contract.md             # Enforceable artifact schema and rules
    ├── methodology.md                   # Personality, depth modes, quality rubric, UX language
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

---

## Scripts Layer — `scripts/reef.py`

All deterministic operations live in a single Python script. Skills invoke it via Bash, read its JSON output, and act on results. The script does the *finding*; the LLM does the *interpreting and presenting*.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py <command> [options]
```

| Command | What it does | Called by |
|---------|-------------|-----------|
| `init <path>` | Scaffold 3-zone directory structure, create project.json | `/reef-init` |
| `index` | Walk all sources, hash files (SHA-256), build `.reef/source-index.json` | `/reef-init`, `/reef-snorkel`, `/reef-update` |
| `snapshot <artifact-id>` | Capture source state (hashes + timestamps) → `.reef/artifact-state/{id}.json` | `/reef-artifact`, `/reef-snorkel`, `/reef-scuba`, `/reef-deep` |
| `diff` | Compare current hashes vs snapshots, classify changes | `/reef-update`, `/reef-health` |
| `lint` | Run 7 mechanical checks (orphans, dangling refs, schema, freshness, etc.) | `/reef-health` |
| `rebuild-map` | Parse artifact frontmatter, rebuild `source-artifact-map.json` | `/reef-artifact`, `/reef-update` |
| `rebuild-index` | Regenerate `index.md` from artifact frontmatter | `/reef-artifact`, `/reef-update` |
| `log <message>` | Append timestamped entry to `log.md` | All skills |

**Output:** Structured JSON to stdout. Example:

```json
// reef.py diff
{
  "sources": {
    "cdm": { "new": 1, "updated": 3, "renamed": 0, "deleted": 0, "unchanged": 338 }
  },
  "affected_artifacts": ["SYS-CDM", "SCH-CDM-STUDY"],
  "details": [
    { "file": "src/models/study.py", "classification": "updated", "old_hash": "a1b2...", "new_hash": "d4e5..." }
  ]
}
```

**Dependencies:** Python stdlib + `pyyaml` (auto-installed via `SessionStart` hook).

---

## Wiki Output Structure (3-Zone)

What `/reef-init` creates on disk:

```
<project>/
├── index.md                          # Auto-generated catalog
├── log.md                            # Append-only evolution log
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
    │   └── {artifact-id}.json
    ├── source-artifact-map.json      #   reverse index (source file → which artifacts)
    ├── questions.json                #   question bank
    ├── sessions/                     #   lightweight session logs
    └── .gitignore                    #   excludes sessions/, keeps everything else
```

**Three zones:**
- **artifacts/** — canonical knowledge. The product's output. Human-reviewed, structured, interlinked.
- **sources/** — raw evidence, organizational registries, user-provided docs. Things code alone can't tell you.
- **.reef/** — operational state. Never edited by hand. Powers freshness, lint, and updates.

---

## The Artifact Contract

Reef's core IP — the structured schema that makes the output valuable.

### 8 Artifact Types

| Type | Prefix | Purpose | Required Sections |
|------|--------|---------|-------------------|
| System | `SYS-` | Entry point for a domain/service | Overview, Key Facts, Responsibilities, Core Concepts, Related |
| Schema | `SCH-` | *Interpretation* of data models (not the raw ERD) | Overview, Key Facts, Entities, Related |
| API | `API-` | *Interpretation* of API surfaces (not the raw spec) | Overview, Key Facts, Source of Truth, Resource Map, Related |
| Process | `PROC-` | Workflow/lifecycle/behavior | Purpose, Key Facts + archetype-dependent body, Related |
| Decision | `DEC-` | Architectural decision record | Context, Decision, Key Facts, Rationale, Consequences, Related |
| Glossary | `GLOSSARY-` | Domain term registry | Terms table (with `[[wikilinks]]`), Related |
| Contract | `CON-` | Cross-system boundary agreement | Parties, Key Facts, Agreement, Current State, Related |
| Risk | `RISK-` | Known issues with severity tracking | Description, Key Facts, Impact, severity/resolution fields, Related |

**SCH- and API- clarification:** These capture interpretation and context — business rules, usage patterns, deprecation status, cross-system dependencies. The raw spec lives in `sources/raw/` and the artifact points to it.

### 7 Relationship Types

| Type | Meaning | Example |
|------|---------|---------|
| `parent` | Detail of a higher-level artifact | PROC-CDM-CASE → SYS-CDM |
| `depends_on` | Assumes another artifact's content | SCH-CDM-STUDY → SCH-CDM-IMAGE |
| `refines` | Adds peer-level detail | API-CDM-REST → SYS-CDM |
| `constrains` | Governs/limits another | DEC-AUTH-PATTERN → API-CDM-AUTH |
| `supersedes` | Replaces a previous artifact | DEC-NEW-AUTH → DEC-OLD-AUTH |
| `feeds` | Sends data to another system | SYS-CDM → SYS-RDP |
| `integrates_with` | Bidirectional exchange | SYS-CDM ↔ SYS-CTL |

### Frontmatter Schema

```yaml
---
id: "SYS-CDM"
type: "system"
title: "CSG Data Manager"
domain: "cdm"                         # free-form string
status: "draft"                       # draft | active | deprecated
last_verified: 2026-04-09            # unquoted ISO date
freshness_note: "review when case model or auth changes"
freshness_triggers:
  - "src/models/study.py"
  - "src/services/case.py"
known_unknowns:
  - "Image deduplication logic unclear"
tags:
  - cdm
  - system
aliases:
  - "CDM"
relates_to:
  - type: "feeds"
    target: "[[SYS-RDP]]"
sources:
  - category: "implementation"
    type: "github"
    ref: "src/models/study.py"
notes: ""
---
```

**Field ordering:** id, type, title, domain, status, last_verified, freshness_note, freshness_triggers, known_unknowns, tags, aliases, relates_to, sources, notes.

**Determinism rules:** `relates_to` sorted by target, `sources` sorted by ref, `freshness_triggers` sorted alphabetically.

**Obsidian dual strategy:** Frontmatter `relates_to` for agents/Dataview. Body `[[wikilinks]]` in Key Facts, prose, and `## Related` section for Obsidian graph view. Both generated; validation checks sync.

### Key Facts

Every artifact (except Glossary) includes individually verifiable assertions linked to sources:

```markdown
## Key Facts
- CDM owns breast and chest radiology case management → `src/services/case.py`
- Case status transitions enforced at the service layer → `src/services/case.py:L45-89`
- CDM does NOT own annotation workflows (that's CTL) → verified with CTL team
```

Each fact can be independently verified during lint. When a source file changes, only facts referencing it need re-verification.

### Validation on Accept

Before writing to disk:

**Blocking:** YAML parseable, required fields present, id matches filename, valid enums, freshness_note not empty, Key Facts present.

**Warning:** relates_to targets exist, source refs resolve, body sections present, `## Related` matches frontmatter.

---

## Skill Breakdown

### `/reef-init` — Bootstrap

1. Check if `.reef/` already exists → report or offer reset
2. **Scope the reef:** project name, wiki location (default: cwd), source directories (default: cwd, can add external repo paths). Single-repo note: suggest `/reef-merge` later.
3. Run `reef.py init <path>` → scaffold 3-zone structure
4. Run `reef.py index` → walk sources, hash files, build source-index.json
5. Ask about organizational context → create registry files:

   ```yaml
   # sources/registries/repos.yaml
   repos:
     - name: service-name
       full_name: Human-Readable Name
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

6. Ask about documentation sources (architecture docs, SRS, wiki exports) → note in project.json
7. Optionally seed `.reef/questions.json` — "What questions do you need this wiki to answer?"
8. Run `reef.py log` → append creation entry
9. Suggest next step: `/reef-snorkel` or `/reef-scuba`

### `/reef-snorkel` — Auto-Discovery Surface Pass

Rapidly generates 3-6 draft artifacts. No questions asked.

1. Run `reef.py index` to refresh. Read project.json, artifact contract, existing artifacts.
2. Structural scan per source: 2-level dir tree, README, routers/handlers, models/schemas, config, tests
3. Generate in priority order: SYS- first, then SCH-, API-, GLOSSARY- as discovered
4. Each artifact: valid frontmatter, Key Facts with source refs, honest known_unknowns, `status: "draft"`, freshness fields, `## Related` with wikilinks
5. Validation on accept (blocking + warning)
6. Run `reef.py snapshot` → source state at write time
7. Run `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log`
8. After 3-6 artifacts, **stop**. Summarize. Invite depth.

**Personality:** Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

**One at a time.** Don't batch-dump. The user should see each artifact appear.

**Cross-system contracts always-on:** when Claude reads code calling another system, flag the boundary immediately.

### `/reef-scuba` — Socratic Deepening

Interactive, question-driven knowledge extraction. Where the real value lives.

1. Load context: project.json, existing artifacts, contract, question bank
2. Entry point: (a) user names a topic, (b) offer to deepen a snorkel draft, (c) generate questions from understanding template
3. If generating questions: adapt 33 baseline questions to what the structural scan reveals
4. **Guided priorities, not rigid phases:** SYS- boundaries first, then fill in. Any type at any time. Warn (not block) if PROC- proposed before parent SYS-.
5. Work through questions one at a time: Fact / Why it matters / Source / Confidence / Open question
6. After each artifact: **"What did I get wrong? What am I missing?"**
7. Proactively suggest questions code can't answer: team ownership, decision rationale, operational reality vs design intent, cross-system boundaries
8. **Suggest documentation sources when uncertain.** Docs provide the lens for interpreting code.
9. Prioritize toward unanswered questions in the question bank

**Core principle:** "AI reads code. It can't know which gaps are dangerous or which ambiguities cause real problems downstream. That part is yours."

### `/reef-deep` — Exhaustive Deep Dive

Maximum depth on a specific area.

1. User directs Claude to a specific system, subsystem, or topic
2. Read entire directories, trace execution paths, map every function that materially affects runtime
3. Dense Key Facts with precise line citations (e.g., `src/services/case.py:L45-89`)
4. 5+ facts per artifact minimum
5. User provides domain framing that reshapes how Claude interprets the code

For critical systems where shallow reading misses the real behavior.

### `/reef-artifact` — Create/Update Single Artifact

Workhorse skill with full contract enforcement.

1. Read artifact contract (always)
2. Create: determine type → generate ID → reference template. Update: read existing → identify changes → preserve unaffected → bump last_verified
3. Gather evidence: read source, check edges, trace claims
4. Write per contract: all frontmatter fields, required body sections, Key Facts, `## Related`, freshness fields
5. Validation on accept
6. Run `reef.py snapshot` + `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log`

### `/reef-update` — Bulk Update

Re-indexes all sources, detects what changed, updates affected artifacts in one pass.

1. Run `reef.py index` → rebuild source-index.json
2. Run `reef.py diff` → classify changes (new/updated/renamed/deleted/unchanged)
3. Present change summary:
   ```
   Source changes since last update:
     cdm: 3 updated, 1 new, 0 deleted
     ctl: 0 changes
   Affected artifacts: SYS-CDM, SCH-CDM-STUDY, PROC-CDM-CASE-LIFECYCLE
   ```
4. For each affected artifact, re-read changed sources and propose updates
5. User accepts/skips each (same validation as `/reef-artifact`)
6. Run `reef.py snapshot` for each + `reef.py rebuild-index` + `reef.py rebuild-map` + `reef.py log`

**Key difference from `/reef-health`:** Health *reports*. Update *fixes*. Health is read-only. Update writes.

### `/reef-health` — Validation & Freshness

**Step 1 — Script:** Run `reef.py lint` + `reef.py diff` for 7 mechanical checks:
1. Orphan detection (no incoming relates_to, except SYS- roots)
2. Dangling references (relates_to targets don't resolve)
3. Source file existence (refs still on disk)
4. Frontmatter schema (required fields, valid enums, id/filename match)
5. Key Facts without source links
6. Wikilink/frontmatter sync (`## Related` matches `relates_to`)
7. Freshness (source files changed since write time)

**Step 2 — LLM:** Format the text-rendered report.

**Step 3 — LLM opt-in checks:**
8. Empty known_unknowns (genuinely no gaps?)
9. Contradiction detection (conflicting Key Facts across artifacts)
10. Stale claims (re-read sources, check if claims still hold)

**Change classification:**

| Classification | Meaning | Action |
|---|---|---|
| `new` | file appeared | flag artifacts in same module |
| `updated` | content hash changed | flag artifacts referencing this file |
| `renamed` | path changed, content similar | update source refs |
| `deleted` | file removed | warn — artifacts may be invalid |
| `unchanged` | no movement | skip |

**Text-rendered report:**

```
Reef Health — my-project                         2026-04-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sources          Files    Seen   Deep   Freshness
─────────────────────────────���───────────────────
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

### `/reef-test` — Test Your Reef

The most meaningful progress metric.

1. Read `.reef/questions.json` (seeded during init or added anytime)
2. Claude answers each question grounded in existing artifacts (not source code)
3. Rate: fully answered / partially answered / not answerable
4. Surface gaps with specific recommendations
5. **Gap-to-action loop:** for unanswered questions, offer to deep-dive → transitions into scuba/deep

The question bank serves as north star (the reef exists to answer them), discovery guide (unanswered questions steer scuba), and ongoing health check (if a previously-answered question drops, that's a freshness signal).

**Text-rendered report:**

```
Test Your Reef — my-project                      2026-04-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: ████████████░░░░░░░░ 7/12 questions answered

 ✓  How does CDM handle case state transitions?      → PROC-CDM-CASE-LIFECYCLE
 ✓  What data flows from CDM to RDP?                 → CON-CDM-RDP-FEED, SYS-RDP
 ~  How does auth work across services?               → partial: SYS-DAIP (shallow)
 ✗  What's the disaster recovery plan?
 ✗  How do schema migrations get coordinated?

Gaps to explore:
  DAIP is shallow — 3 Key Facts, needs /reef-scuba
  RDP has no PROC- artifacts — run /reef-deep on rdp:src/flows/
```

### `/reef-merge` — Combine Reefs (v1.1)

Merges single-repo reefs into a multi-system reef.

1. User provides paths to 2+ existing reef directories
2. Read each reef's project.json and artifacts
3. Copy artifacts into combined reef, preserving IDs and source refs
4. Conflict detection: same-ID artifacts flagged for resolution
5. Cross-system discovery: scan merged artifacts for boundaries → propose CON- artifacts
6. Rebuild index, source-artifact-map, log

**Deferred to v1.1** — the wiki structure (IDs, source refs, frontmatter) is designed to make merging possible from day one.

### `/reef-source` — Extract Raw Specs from Code (v1.1)

1. OpenAPI extraction: scan for FastAPI/Flask/Express routes → `sources/raw/{service}/openapi.json`
2. ERD/schema extraction: scan for SQLAlchemy/Django/Prisma models → `sources/raw/{service}/schema.md`
3. Ingest user-provided docs: PRDs, SRDs, architecture docs → `sources/docs/`

Raw evidence files, not artifacts. SCH- and API- artifacts *interpret* them.

---

## Reference Files

### `references/artifact-contract.md`
The enforceable rulebook. 8 types, 7 relationships, frontmatter schema, field ordering, determinism rules, body section requirements, validation checklist, Obsidian dual strategy.

### `references/methodology.md`
- **Curious Researcher personality:** genuine curiosity, present-participle narration, adapts to depth mode. No emojis, no exclamation marks.
- **3 depth modes:** snorkel (auto, no questions), scuba (conversational, Socratic), deep (exhaustive, line-by-line)
- **Core principle:** "AI found the answers. I asked the questions."
- **3 foundational questions:** How keep it from going stale? How know it's true? How find what it needs?
- **Anti-patterns:** never invent facts, never use absolute paths, honest gaps beat confident lies
- **4-phase lifecycle:** Bootstrap (human-heavy) → Expand (mixed) → Maintain (automated) → Lint (fully automated)
- **9-question quality stress test** (from presentation)
- **Key Facts as claims-lite:** each fact linked to source, individually lintable
- **SCH-/API- clarification:** interpret the raw spec, don't restate it
- **UX language guidelines:**

  | Context | Use | Example |
  |---------|-----|---------|
  | Status / health | Reef metaphor | "Your reef is aging" / "3 artifacts growing stale" |
  | Call to action | Plain language | "Run `/reef-health`" / "Deepen with `/reef-scuba`" |
  | Progress narration | Present participle | "Reading src/models/..." / "Found 4 independent applications..." |
  | Error / gap | Honest, not alarming | "I couldn't verify this claim — adding to known unknowns" |

  The user should never have to decode the metaphor to understand what to do.

### `references/understanding-template.md`
33 questions across 7 phases (A-G). Generalized for any codebase. Adaptive: add questions for multi-app/complex auth, remove for simple systems.

### `references/templates/*.md`
8 templates (System, Schema, API, Process, Decision, Glossary, Contract, Risk). Each includes required frontmatter with placeholders, required body sections, `## Related` template, and notes on what this type captures.

---

## Implementation Phases

### Phase 1: Scaffold + Script + References (~3 hours)

1. Create `reef-plugin/.claude-plugin/plugin.json` (with `SessionStart` hook for pyyaml)
2. Write `scripts/reef.py` — all 8 subcommands
3. Write `references/artifact-contract.md`
4. Write all 8 `references/templates/*.md`
5. Write `references/understanding-template.md`
6. Write `references/methodology.md`
7. Write `skills/reef-init/SKILL.md`

**Verify:** Run `reef.py init` + `reef.py index` directly. Then `/reef-init` in a test directory.

### Phase 2: Snorkel (~2 hours)

8. Write `skills/reef-snorkel/SKILL.md`
9. Test against a real codebase
10. Validate: frontmatter parses, source refs real, Key Facts cited, known_unknowns honest, snapshots captured

### Phase 3: Artifact + Health + Update (~3 hours)

11. Write `skills/reef-artifact/SKILL.md`
12. Write `skills/reef-health/SKILL.md` — mechanical checks + LLM opt-in + text report
13. Write `skills/reef-update/SKILL.md` — re-index, detect changes, propose updates
14. Test: create artifact → health check → corrupt → re-check. Modify source → update → verify.

### Phase 4: Scuba + Deep (~3 hours)

15. Write `skills/reef-scuba/SKILL.md`
16. Write `skills/reef-deep/SKILL.md`
17. Test full scuba session: generate questions → work through 3-4 → compare to hand-crafted quality

### Phase 5: Test + Polish (~1 hour)

18. Write `skills/reef-test/SKILL.md`
19. Write `README.md` (installation, usage, philosophy, privacy note)
20. End-to-end test: init → snorkel → scuba → update → health → test

### Phase 6: v1.1 Skills (post-MVP)

21. Write `skills/reef-merge/SKILL.md`
22. Write `skills/reef-source/SKILL.md`
23. Test merge with 2 separate reefs → verify CON- artifacts at boundaries

---

## Verification

1. **Init smoke test:** all 3 zones, project.json, log.md, registries prompt
2. **Snorkel against real code:** 3-6 artifacts, valid frontmatter, real sources, Key Facts, snapshots
3. **Quality comparison:** snorkel output vs hand-crafted — honest draft with clear known_unknowns
4. **Scuba round-trip:** deepen a draft → approaches hand-crafted quality
5. **Health catches issues:** corrupt artifacts → all 7 mechanical problems flagged
6. **Test your reef:** seed questions → verify grounding and gap detection
7. **Update detects changes:** modify source → verify affected artifacts flagged and updated
8. **Cross-project portability:** full flow on unfamiliar codebase → nothing assumes specific structure
9. **Obsidian compatibility:** open in Obsidian → graph view, Dataview queries work
10. **Text reports render:** health and test produce readable Unicode graphics in terminal

---

## Success Criteria

1. **First artifacts in 5 minutes, zero questions.** Surface pass produces 3-6 structurally correct drafts. After 30 minutes of scuba, 8-12+ artifacts with organizational depth.
2. **Useful without Reef, beautiful in Obsidian.** Plain markdown. Connected graph. Dataview-queryable frontmatter.
3. **Collaborative discovery, not document generation.** Three depth modes feel distinct. Curious researcher personality makes it engaging. User feels like they're teaching, not prompting.
4. **Cross-system contracts are the "aha."** After 2+ systems, Claude proposes boundary artifacts that surface implicit knowledge.
5. **Validation catches errors.** Schema errors blocked. Dangling refs warned. Source snapshots captured.
6. **Maintainable.** Health check finds problems. Update fixes them. Question bank tracks whether the wiki answers real questions.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SKILL.md context limits | Medium | High | Keep skills focused. Heavy material in `references/` read on demand. |
| Too many skills overwhelm users | Medium | Medium | README: clear 3-step flow (init → snorkel → scuba). Others are "when you need them." |
| Quality varies by model (Sonnet vs Opus) | Medium | Medium | Test on both. Snorkel/health work on Sonnet; scuba/deep benefit from Opus. |
| Claude doesn't follow contract consistently | Medium | High | Always read full contract before writing. Validation catches deviations. |
| Plugin discovery/installation friction | High | Medium | Clear README. Eventually marketplace. |
| Users don't return after snorkel | Medium | High | Snorkel flags gaps and invites depth. Question bank gives a reason to come back. |
| Large monorepos overwhelm snorkel | Medium | Medium | Compact summaries. Claude navigates via tools. Init asks user to scope directories. |

---

## Roadmap

### v1.0 — Plugin MVP
8 skills (init, snorkel, scuba, deep, artifact, update, health, test). 8 artifact types, 7 relationships, 3-zone wiki. Scripts layer for mechanical operations. Text-rendered reports. Obsidian-compatible.

### v1.1 — Multi-Repo + Raw Specs
`/reef-merge` for combining reefs. `/reef-source` for OpenAPI/ERD extraction and doc ingestion. Git-based freshness diffing. Dependency tracking via source-artifact-map.

### v1.2 — Richer Discovery
Pattern artifact type. Process archetype detection. Proactive doc source integration. Obsidian plugin.

### v2.0 — Reef Desktop
Visual layer reading wiki output. Ocean depth design system (seven-blue palette + coral, ✱ logo). Coverage indicators, session summaries, artifact ribbon.

### v2.1 — Output + Collaboration
Export to Confluence/Notion/GitBook/HTML. Share via git. Domain-specific type extensions.

### v3.0 — Agent Autonomy
Scheduled updates. CI/CD integration. Multi-agent (one per system, coordinator for contracts). **Work zone** for drafting PRDs/SRDs grounded in structured knowledge. **Spec → code loop:** code → knowledge → specs → code.

---

## Privacy

Reef skills read source code and pass contents to Claude for analysis.
- **Max subscribers:** processed under Anthropic's Claude subscription policy.
- **No data leaves your machine** except through Claude Code's normal operation.
- **Wiki output is local-first.** Artifacts, state, and logs stay on your filesystem.
- The plugin stores no credentials and makes no network requests.

---

## Key Decisions

**Why a Claude Code plugin?** Zero marginal cost for Max subscribers. No custom tools needed — Claude Code's native Read, Write, Glob, Grep, Bash cover everything. No installation beyond the plugin. The methodology is the product, not the runtime.

**Why scripts + LLM, not LLM alone?** File hashing, change detection, schema validation, index rebuilding — these are deterministic. Scripts are faster, cheaper, and more reliable. The LLM focuses on what requires intelligence: interpreting code, generating artifacts, answering questions.

**Why 8 MVP skills?** Each has distinct behavior. Snorkel suppresses questions; scuba is built on them; deep traces paths; update fixes staleness; health reports without changing. Separate skills keep context size manageable.

**Why source snapshots?** Cannot be backfilled. Enables the entire freshness/lint/update story. Cheap (~20 lines per artifact).

**Why Obsidian dual strategy?** Frontmatter for agents/Dataview. Body wikilinks for graph view (which only reads body links). Both generated; validation checks sync.

**Why local-first?** Privacy is a prerequisite, not a feature. Sharing via git. No server, no account, no lock-in.
