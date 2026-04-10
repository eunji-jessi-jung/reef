# Reef — Plan Stress Test

A structured questionnaire to pressure-test whether Reef's plan holds up against competing approaches, absorbs their best ideas, and has a defensible value proposition.

Compare against:
- **Karpathy LLM Wiki** — the pattern (ingest/query/lint, index.md + log.md, schema-driven)
- **Onco-PE Knowledge Base** — a production implementation (claim-based pages, evidence tables, deterministic state, full-build/incremental sync)
- **CSG Knowledge Repo** — Jessi's own implementation (9-type artifact contract, 5-zone architecture, discovery flow, freshness tracking)
- **NotebookLM / RAG tools** — the mainstream approach (upload docs, query at runtime, no persistent synthesis)

---

## A. Core Value & Differentiation

### A1. Why does Reef exist when someone can just use Claude Code with a CLAUDE.md?

Jessi built the CSG knowledge repo using exactly this approach — Claude Code + a well-crafted CLAUDE.md + skill files. What does a dedicated app add that the CLI doesn't? Is the answer "accessibility for non-developers" strong enough to justify a product?

**What's at stake:** If the CLI approach is 90% as good, Reef is a UI wrapper, not a product.

**Answer:** CLI + CLAUDE.md can produce the same output, but the user must also design the methodology, the schema, the discovery flow, and the file structure — simultaneously while doing the actual knowledge work. That's what Jessi did, and the path was full of trials, errors, and self-doubt (see docs/archive for the surviving history — more was deleted). Reef encodes all of that hard-won knowledge into the product. The user only does the valuable part: asking questions and validating answers. The structure, the artifact contract, the phased discovery, the multi-source indexing — that's Reef's job. Additionally, UI provides spatial awareness (seeing all sources, accumulated artifacts, and progress) that a linear CLI cannot. This isn't a UI wrapper — it's the difference between handing someone a blank terminal and handing them a guided process that already knows the best path.

---

### A2. What does Reef do that Karpathy's LLM Wiki pattern doesn't?

Karpathy's pattern is intentionally abstract and tool-agnostic. Anyone can implement it with Claude Code, Codex, or any agent. Reef's plan claims structured artifacts and human-in-the-loop as differentiators — but Karpathy explicitly mentions staying involved during ingestion and co-evolving the schema.

**Specific challenges:**
- Karpathy has **ingest/query/lint** as three operations. Reef only has discovery + update. Where is Reef's equivalent of **lint** (health-check for contradictions, orphans, stale claims)?
- Karpathy's pattern files **good query answers back into the wiki**. Reef's chat answers disappear into conversation history. Is this a gap?
- Karpathy suggests **Obsidian graph view** for navigation. Reef outputs markdown but has no graph visualization. Does this matter?

**Answer:** Reef is more than one implementation of Karpathy's pattern — it's a specialized product for a specific problem space (overseeing complex multi-system environments with real-world organizational complexity) that Karpathy's abstract pattern and general tools like NotebookLM don't effectively address.

**On the three specific gaps:**

1. **Lint is a genuine gap — and Reef can do it better.** Reef's rigorous artifact contract (typed artifacts, required frontmatter, `relates_to` targets, `sources` references) makes mechanical validation possible: orphans, dangling references, stale source links, missing `known_unknowns`. Karpathy has to lint against a user-defined schema. Reef's schema is built in. Reef also tracks all sources explicitly, so freshness checks are a natural extension. Approach: adopt Karpathy's lint concept, implement as a "Health Check" feature, leveraging the artifact contract for richer validation than an abstract pattern can offer.

2. **Good chat answers should be kept.** The CSG discovery files (2,810 lines across 4 systems) were continuously referenced during artifact creation and used as stress tests for completeness. Reef already persists conversations in `.reef/conversation.json`. The missing piece: a "save as artifact" action on any Claude message, letting users promote good answers into the wiki without a formal artifact proposal. Lightweight to build, closes the gap.

3. **Don't build visualization — integrate with Obsidian.** Reef already outputs markdown with YAML frontmatter and `relates_to` links. If formatted as standard markdown links or wikilinks, Obsidian's graph view works for free. An Obsidian plugin is a v2 idea. For MVP: ensure output is Obsidian-friendly. Zero engineering cost, full visualization benefit.

**On positioning:** Karpathy's pattern is universal (books, docs, any knowledge). Reef is intentionally narrower: complex production systems with organizational context (org charts, RACI, cross-system contracts, 12+ repos). This specificity is a strength for traction. Broaden the horizon later from a position of strength — don't split focus on day one.

**Answer:**

---

### A3. What does Reef absorb from the Onco-PE implementation?

The Onco-PE knowledge base has several ideas Reef's plan doesn't mention:

| Onco-PE Feature | In Reef? | Should it be? |
|-----------------|----------|---------------|
| **Claim-based pages** (C1, C2... with evidence refs and status per claim) | Adapted | Key Facts section (claims-lite) |
| **Append-only claim IDs** (surviving claims never renumbered) | Principle adopted | Stable artifact IDs + stable Key Facts |
| **Evidence table** (evidence_ref, source_url, updated_at_source, content_hash) | Adapted | Source snapshots in `.reef/artifact-state/` |
| **Change triggers** (when to re-evaluate a page) | Yes | `freshness_note` field + `freshness_triggers` |
| **Determinism rules** (sorted collections, stable paths) | Yes | Sorted frontmatter arrays, stable field ordering |
| **Source-to-KB mapping** (which source → which KB page + claims) | Yes | Reverse index in `.reef/source-artifact-map.json` |
| **Run records** (full-build and incremental sync logs) | Adapted | `log.md` (human-readable) + session logs in `.reef/sessions/` |
| **Domain-specific type extensions** (OAI, OAIOLS, INTG each have custom types) | v2 | Power-user feature for later |
| **Validation on write** (12-check synthesized-KB checklist) | Yes | Validate frontmatter + refs on artifact accept |
| **Richer relation types** (deploys_to, feeds, integrates_with...) | Yes | Expanded enum for system architecture clarity |
| **Change classification vocabulary** (new/updated/renamed/deleted...) | Yes | Powers the lint/health-check feature |
| **log.md** (append-only wiki evolution log) | Yes | Curated timeline, not raw chat history |
| **freshness_note** per artifact | Yes | Human judgment on when to re-verify |

**The question:** Is Reef's simpler approach (prose artifacts with frontmatter) better for the target user, or is it leaving value on the table by not adopting claim-level granularity?

**Answer:** Onco-PE and Reef start from fundamentally different source material and lifecycle models.

**Onco-PE reads documents about systems.** Its 2,676 sources are almost entirely Confluence pages — architecture docs, workflow specs, deployment guides that humans wrote *about* the code. GitHub is tracked at the repo level ("this repo exists") but individual source files are not read. When Onco-PE says "OneAI uses Prefect for workflow orchestration" (claim C3, status: `unverified`), the only way to verify that is to read the code — but the pipeline doesn't do that.

**Reef reads the systems themselves.** It opens `src/services/case.py`, reads FastAPI routes, parses database models, and grounds every claim in actual code. When Reef says "case status transitions are enforced at the service layer," the source ref points to the exact file. This is primary-source knowledge, not secondary.

**Reef's lifecycle model is not "hand-built forever."** The CSG repo proves that human-driven discovery is essential for the initial library (depth, context, organizational knowledge), but maintaining 181 artifacts manually as 4 codebases evolve is unsustainable. Reef's paradigm:

1. **Bootstrap (human-heavy):** Guided discovery, Q&A, human validates each artifact. Irreplaceable — no pipeline can ask "why did the team choose this auth pattern?"
2. **Expand (mixed):** Claude scans unexplored files, proposes new artifacts in batches. Human reviews, doesn't guide every step.
3. **Maintain (mostly automated):** Source changes detected via git diffs + content hashes. Affected artifacts flagged. Claude proposes updates. Human reviews diffs, not full artifacts.
4. **Lint & Health Check (fully automated):** Orphans, dangling refs, stale facts, contradictions — all checked without human trigger. Reports generated. Human decides what to act on.

Human involvement moves from "required for every step" to "required for judgment calls, optional for mechanical updates." The human's time is spent where it's most valuable.

**Where Reef can leapfrog both Onco-PE and current approaches:**

The ideal is reading **both** code (ground truth) **and** documentation (organizational context), then **reconciling** the two: "the code does X, but the Confluence doc says Y — which is current?" This is a PM's biggest pain, and neither Onco-PE nor any current tool addresses it explicitly.

Onco-PE has genuine engineering rigor in state management and verification that Reef should absorb. After deep review, we're adopting substantially more than initially planned — not the pipeline machinery, but the **state management discipline** and **verification infrastructure** that makes a knowledge base maintainable across all four lifecycle phases.

### What Reef adopts from Onco-PE (all MVP):

**1. Source snapshots at artifact-write time**
When an artifact is accepted, Reef captures the state (content hash + last modified) of every source file Claude read during its creation, stored in `.reef/artifact-state/{id}.json`. This is cheap and enables the entire lint/freshness story. If you don't capture it at write time, you lose the baseline forever. The enhanced `.reef/` state layer:
```
.reef/
├── project.json              → (existing) sources, model, timestamps
├── source-index.json         → (enhanced) add lastModified + contentHash per file
├── conversation.json         → (existing) chat history
├── artifact-state/           → NEW: per-artifact operational state
│   └── {artifact-id}.json    →   source refs at write time, hashes, freshness status
├── source-artifact-map.json  → NEW: reverse index (source file → which artifacts)
├── sessions/                 → NEW: lightweight session logs
│   └── {timestamp}.json      →   sources scanned, artifacts created/flagged
└── log.md                    → NEW: append-only wiki evolution log
```

**2. `log.md` — append-only wiki evolution log**
Adapted from Onco-PE's KB log. A curated, human-readable timeline of the wiki's evolution — not raw chat history (that's `conversation.json`), not machine state (that's `sessions/`). Example:
```markdown
## 2026-04-09
- Added sources: cdm (342 files), ctl (218 files)
- Created SYS-CDM, SYS-CTL, SCH-CDM-STUDY-MODEL
- Flagged known unknown: CDM auth pattern unclear

## 2026-04-15
- Health check: 2 artifacts stale (auth refactor in cdm:src/middleware/)
- Updated SYS-CDM, regenerated PROC-CDM-AUTH
```

**3. `freshness_note` frontmatter field**
Every artifact gets a human-readable note about when to re-verify. Different from `known_unknowns` (what we don't know) and `freshness_triggers` (machine-checkable conditions). Example: `freshness_note: "review when CDM's case model or status transitions change"`.

**4. `freshness_triggers` field**
Machine-checkable conditions for re-evaluation. Adapted from Onco-PE's Change Triggers section. Example: `freshness_triggers: ["cdm:src/models/study.py", "cdm:src/services/case.py"]` — when these files change, flag the artifact.

**5. Validation on artifact accept**
Before writing to disk, validate:
- YAML frontmatter present and parseable
- All required fields present for the artifact type
- `id` matches intended filename
- `relates_to` targets reference existing artifacts (warn, don't block)
- `sources` refs are real files in indexed sources (warn, don't block)
- Required body sections present for the artifact type
- `freshness_note` is not empty
- Key Facts section present with at least one fact

Block on schema errors (malformed frontmatter, missing required fields). Warn on reference errors (dangling relates_to, missing source files) — the user decides whether to accept anyway.

**6. Richer relation types**
Expand from 3 types (`parent`, `depends_on`, `refines`) to a richer set that captures system architecture semantics:

| Relation | Meaning | Example |
|---|---|---|
| `parent` | belongs to | PROC-CDM-CASE → SYS-CDM |
| `depends_on` | requires | SYS-CDM → SYS-DAIP (for auth) |
| `refines` | adds detail to | SCH-CDM-STUDY → SYS-CDM |
| `constrains` | governs/limits | DEC-AUTH-PATTERN → API-CDM-AUTH |
| `supersedes` | replaces | DEC-NEW-AUTH → DEC-OLD-AUTH |
| `feeds` | sends data to | SYS-CDM → SYS-RDP |
| `integrates_with` | bidirectional exchange | SYS-CDM ↔ SYS-CTL |

`feeds` and `integrates_with` are particularly valuable for the target user (PM/TPM) understanding data flow and system boundaries.

**7. Key Facts section in artifacts (claims-lite)**
Not Onco-PE's machine-ID'd claim tables, but a human-readable section where each assertion links to its source:
```markdown
## Key Facts
- CDM owns breast and chest radiology case management → `cdm:src/services/case.py`
- CDM does NOT own annotation workflows (that's CTL) → verified with CTL team
- Case status transitions are enforced at the service layer → `cdm:src/services/case.py:L45-89`
- Image deduplication uses perceptual hashing → `cdm:src/utils/dedup.py`
```
Each fact is independently verifiable. When linting, Reef can check each fact's source for changes rather than re-verifying the entire artifact. This is the principle of claims without the pipeline machinery.

**8. Change classification vocabulary**
When Reef runs a health check, it classifies each source file change:

| Classification | Meaning | Action |
|---|---|---|
| `new` | file appeared since last check | flag artifacts in same directory/module |
| `updated` | content hash changed | flag artifacts that reference this file |
| `renamed` | path changed, content similar | update source refs in affected artifacts |
| `deleted` | file removed | warn — artifacts referencing it may be invalid |
| `unchanged` | no movement | skip |

This vocabulary powers meaningful health-check reports: "3 files updated (affects SYS-CDM, PROC-CDM-CASE-LIFECYCLE), 1 file deleted (CON-CDM-CTL-ANNOTATION may be invalid)" instead of just "something changed."

**9. Determinism rules**
- Sorted `relates_to` arrays (alphabetically by target)
- Sorted `sources` arrays (alphabetically by ref)
- Stable frontmatter field ordering (id, type, title, domain, status, last_verified, freshness_note, freshness_triggers, known_unknowns, relates_to, sources, notes)
- Sorted Key Facts (by source label, then path)

Makes diffs clean and prevents spurious changes when artifacts are regenerated.

### What Reef does NOT adopt:

- **Claim-based page format** (C1/C2 with machine IDs) — Key Facts section achieves the same goal in a human-readable way
- **Append-only claim IDs** — stable artifact IDs are sufficient; within-artifact tracking handled by Key Facts
- **Domain-specific type extensions** — 7 types is right for 8-30 artifacts. Extensions are a v2 power-user feature
- **Document-only sourcing** — Onco-PE's fundamental limitation is that it reads Confluence pages *about* code, not code itself. Reef reads both. This is not a feature to adopt but a gap to avoid.

### Reef's strengths over Onco-PE:

- **Primary-source grounding:** Reef reads actual code, not documentation about code. Every Key Fact can trace to a file and line number, not a Confluence page that may be outdated.
- **Code + docs reconciliation:** Reef can read both code (ground truth) and documentation (organizational context) and flag conflicts between them — something no current tool does explicitly.
- **Richer source classification:** The `sources` field with `category` and `type` is richer than Onco-PE's flat canonical identifiers (`conf:OAI:12345`).
- **Git-native freshness:** Git diffs tell you *what* changed, not just *that* it changed. More informative than content hashes for code sources. Content hashes adopted selectively for non-git sources (Confluence, org charts, RACI).
- **Human depth where it matters:** Bootstrap phase produces knowledge that no pipeline can — business context, organizational decisions, cross-system contracts, the *why* behind architectural choices. Then automation takes over for maintenance.
- **Four-phase lifecycle:** Human involvement scales down as the library matures. Bootstrap (human-heavy) → Expand (mixed) → Maintain (mostly automated) → Lint (fully automated). Onco-PE is fully automated from the start, which makes it fast but shallow. Reef gets the depth first, then the speed.

### Key insights absorbed:

1. **State management discipline:** Track the state of sources independently from the state of artifacts, so you can detect drift. Validate rigorously at write time. Capture source snapshots at artifact-write time.
2. **Verification infrastructure:** Log the wiki's evolution as a curated timeline. Give every artifact a human-readable freshness note and machine-checkable freshness triggers. Classify changes with a proper vocabulary so health checks produce actionable reports.
3. **Automation is not optional:** A hand-built library is only viable for the bootstrap phase. Automated expansion, maintenance, and linting are core product features, not nice-to-haves. The product's value proposition includes getting *past* the manual phase into sustainable automated maintenance.
4. **Read primary sources, not just secondary:** Onco-PE's blind spot is that Confluence pages can be wrong. Reef's advantage is reading the code directly. The ultimate move is reconciling code and docs — "the architecture doc says X, the code does Y."

---

### A4. What does Reef absorb from Jessi's own CSG repo?

The CSG knowledge repo is a battle-tested, 181-artifact implementation. Reef simplifies it for productization. Is the simplification correct?

| CSG Feature | In Reef? | Why/why not? |
|-------------|----------|--------------|
| 9 artifact types | 8 (dropped Pattern, kept Risk) | Pattern is a Phase 2/3 artifact requiring cross-system synthesis — emerges late, not natural in early discovery. Risk stays: PMs need a `risks/` folder answering "what should I be worried about?" — visibility is worth the extra type. |
| 5-zone architecture | 3 zones (artifacts + sources + .reef/) | Simplified but not flattened. `artifacts/` = canonical knowledge, `sources/` = raw evidence + registries, `.reef/` = operational state. `docs/` governance → system prompt. `work/` scratch → conversation. `output/` → v2 (tool-agnostic). |
| owner, scope, owning_domain fields | Dropped | Can't productize these — too org-specific. Users won't know what to put. |
| source_of_truth_status field | Dropped | Every Reef artifact is derived from source code — the field would be `"derived"` on 95% of artifacts. Honest gaps are better captured by `known_unknowns` and `freshness_note`, which are actionable. |
| verification_needed flag | Dropped | Redundant. The freshness system (source snapshots + triggers + lint) replaces this with something more granular. |
| Freshness checking (git-based) | Yes (MVP) | Refined approach from A3: git diffs for code, content hashes for non-git sources, source snapshots at write time, change classification vocabulary for health check reports. Substantially better than CSG's current `check-freshness` skill. |
| Output layer (Confluence transformation) | v2, tool-agnostic | When it comes, support Confluence, Notion, GitBook, or beautiful HTML — not locked to one platform. |
| Registry files (repos.yaml, org-chart.yaml) | Yes (MVP) | Critical differentiator — captures knowledge code can't provide. Lives in `sources/registries/`. Claude asks about organizational context and helps create registries. Connects to code + docs reconciliation from A3. |
| 33 baseline discovery questions in 7 phases | All kept, but delivery changes | Questions are Claude's internal checklist in the system prompt, not a form shown to the user. Progressive disclosure: each phase starts with a seed question, follow-ups are reactive based on what Claude found in code. User feels a conversation, not a questionnaire. Progress visible via phase indicator ("Phase 2 of 7: Data Model") but never pressuring. |
| Foundation spec + manifesto docs | System prompt only | Governance rules are code (system prompt), not user-facing files. |

**The question:** When a CSG-style power user tries Reef, will they feel it's missing essential structure? Or will the simplification make it more accessible?

**Answer:** The simplification is mostly correct, with three important refinements:

**1. Three zones, not two.** The original plan collapsed everything into `artifacts/` and `.reef/`. But `sources/` needs to exist as a separate zone for raw evidence and registries:
```
~/reef-wikis/my-project/
├── index.md                      ← auto-generated catalog
├── log.md                        ← append-only wiki evolution log
├── artifacts/                    ← Zone 1: canonical knowledge
│   ├── systems/
│   ├── schemas/
│   ├── apis/
│   ├── processes/
│   ├── decisions/
│   ├── glossary/
│   └── contracts/
├── sources/                      ← Zone 2: evidence + registries
│   ├── registries/               ←   repos.yaml, org-chart.yaml, raci.yaml
│   └── raw/                      ←   API specs, schema dumps, exported docs
└── .reef/                        ← Zone 3: operational state (hidden)
    ├── project.json
    ├── source-index.json
    ├── conversation.json
    ├── artifact-state/
    ├── source-artifact-map.json
    └── sessions/
```

**2. Registry files are a must-have.** These are where Reef captures what code alone can't tell you — team ownership, organizational structure, RACI charts, repo-to-domain mapping. Claude should proactively ask about organizational context during discovery and help the user create these. This connects directly to the "code + docs reconciliation" capability identified in A3.

**3. Discovery questions are kept but delivered differently.** 33 questions baked into the system prompt as Claude's internal guide. The user never sees a checklist. Instead, progressive disclosure: seed questions per phase, reactive follow-ups based on code reading, visible phase progress. The onboarding experience is a conversation, not a form. This is the hardest and most valuable UX challenge — the bootstrap phase must feel inviting, not overwhelming.

**What a CSG power user would notice:** They'd miss Pattern and Risk types (defer Pattern, decide on Risk). They'd miss `owner` and `scope` (acceptable — these are org-specific). They would NOT miss `source_of_truth_status` or `verification_needed` (replaced by better mechanisms). They'd be pleased by the freshness system, registry support, and the fact that 33 questions are still driving discovery under the hood. The simplification removes bureaucracy without removing rigor.

**Decision: Risk artifacts kept as own type.** `RISK-` artifacts with severity/impact/resolution fields live in `artifacts/risks/`. PMs need a clear `risks/` folder answering "what should I be worried about?" Minor observations stay as Key Facts inside other artifacts; systemic risks get their own artifact. 8 types total: System, Schema, API, Process, Decision, Glossary, Contract, Risk. Pattern deferred.

---

### A5. Why not just use NotebookLM or ChatGPT with file uploads?

These tools let you upload documents and ask questions. What's Reef's answer to "I can just drag my files into NotebookLM"?

**Key differences to articulate:**
- NotebookLM re-derives answers every time (RAG). Reef compounds knowledge (persistent artifacts).
- NotebookLM has no structured output. Reef produces typed, interlinked markdown artifacts.
- NotebookLM doesn't support multi-repo code analysis with file reading.
- But: NotebookLM is free, zero-setup, and already exists.

**Answer:** NotebookLM and ChatGPT are query tools. Reef is a knowledge management tool. They solve different problems.

**1. Privacy and trust model.** Enterprise codebases are sensitive. Uploading `src/` to Google's or OpenAI's servers is a non-starter for most engineering orgs — and shouldn't be done. Reef is local-first: code stays on your machine, only the conversation goes to the Claude API. With company API accounts, there are guardrails (zero data retention policies, SOC2 compliance). Engineers are already familiar with local-only tools. This is a hard differentiator, not a soft one.

**2. Compounding vs. re-deriving.** NotebookLM re-derives every answer at query time. There's no persistence, no structure, no accumulation. You ask a question, get an answer, close the tab — the answer is gone. Next time, it re-derives from scratch. Reef produces persistent, typed, interlinked artifacts that compound over time. Each artifact builds on the last. The knowledge base grows. If NotebookLM could solve the problem Reef addresses — building and maintaining a structured understanding of complex multi-system architectures — it would have already been used for that. It hasn't, because it fundamentally can't.

**3. Active investigation vs. passive Q&A.** NotebookLM answers questions about documents you uploaded. Reef *investigates* systems. Claude reads a file, decides it needs to also read 3 related files, follows imports, understands directory structure, asks the user clarifying questions, and proposes structured artifacts based on active exploration. The tool-use loop (read → reason → read more → synthesize → propose) is a fundamentally different interaction model than upload-and-query.

**4. Code-native.** NotebookLM accepts PDFs, docs, and websites. It doesn't understand codebases — directory structure, file relationships, import chains, database models, API routes. Reef reads source code natively, across multiple repos, with labeled sources. It can trace a claim to a specific file and line number.

**What NotebookLM IS good for:** One-time synthesis from document collections (papers, reports, meeting notes). If you need a podcast summary of 10 PDFs, use NotebookLM. If you need a living knowledge base of your production systems that stays current as the code evolves — that's Reef.

---

## B. Artifact Contract & Schema Design

### B1. Is 7 artifact types the right number?

CSG has 9. Onco-PE has 8 core types + 15 domain extensions (23 total). Karpathy has zero (untyped pages).

Reef has 7: System, Schema, API, Process, Decision, Glossary, Contract.

- **Too few?** Missing: Pattern (reusable design solutions), Risk (known issues), Integration-spec (Onco-PE), Guide (general-purpose).
- **Too many?** A PM building their first knowledge base might be confused by 7 types. Would 4 (System, Schema, Process, Glossary) be enough for MVP?
- **Wrong types?** Are API and Contract distinct enough, or do they overlap for the target user?

**Answer:** 8 types is right. Simplification is almost always better.

**Onco-PE's core 8 don't add anything Reef doesn't already cover.** Their extra types (`source-summary`, `architecture-note`, `guide`, `policy`, `deployment-note`, `issue-tracking`) exist because they're categorizing 2,700 existing Confluence pages into bins. Reef creates knowledge through discovery — different types emerge from a different process. Side-by-side: `source-summary` is a pipeline artifact (not relevant); `architecture-note` overlaps with SYS- + DEC-; `guide` is an output format (v2); `policy` is a standing DEC-; `deployment-note` is PROC- or RISK-; `issue-tracking` is RISK-.

**API and Schema stay, with clarified intent:**
- **SCH-** artifacts capture the *interpretation* of data models — not the raw ERD/schema itself. Which entities matter and why, business rules enforced at application layer, logical relationships not visible as foreign keys, used vs. legacy fields. The raw schema lives in `sources/raw/` — the artifact points to it.
- **API-** artifacts capture the *interpretation* of API surfaces — not the raw OpenAPI spec itself. Which endpoints are actually consumed, auth quirks, deprecated-but-live endpoints, API-to-data-model relationships. The raw spec lives in `sources/raw/` — the artifact points to it.

Both types exist to add the human/contextual layer that raw specs can't provide. They are NOT prose restatements of the spec.

**Source freshness for raw specs is a first-class feature:**
1. Reef detects OpenAPI/schema files during indexing (openapi.json, schema.sql, *.prisma, alembic migrations, etc.)
2. Copies them to `sources/raw/` so the wiki is self-contained with a snapshot
3. Hashes them in source-index.json
4. On health check: re-reads from source folder, compares hash. If changed → flags SCH-/API- artifacts, updates the snapshot in `sources/raw/`
5. Separate `sync-sources` action refreshes raw specs without running full lint

**Final type list (8):** System, Schema, API, Process, Decision, Glossary, Contract, Risk. Pattern deferred to v2 (emerges from cross-system synthesis after enough artifacts exist).

---

### B2. Is prose-with-frontmatter the right format, or should Reef use claim-based pages?

**Answer:** Prose with frontmatter, enhanced with three design goals:

1. **Machine-first frontmatter.** Frontmatter is for agents, not humans. It must be parseable by standard YAML libraries (gray-matter, Dataview, any agent).
2. **Contains everything needed to keep the wiki alive.** All fields from the stress test: id, type, title, domain, status, last_verified, freshness_note, freshness_triggers, known_unknowns, relates_to (with types), sources, tags, aliases.
3. **Obsidian-compatible for graph visualization.**

**Critical finding:** Obsidian's graph view only draws edges from `[[wikilinks]]` in the note body — NOT from frontmatter fields. Frontmatter relationships are invisible to the graph. This requires a **dual strategy:**

- **Frontmatter:** structured `relates_to` with types, for agents and Dataview queries
- **Body:** `[[wikilinks]]` in Key Facts, prose, and a `## Related` section, for Obsidian's graph view

**Obsidian-specific frontmatter additions:**
- `tags` — enables tag pane and graph filtering (color all `cdm` nodes blue)
- `aliases` — quick switcher finds "CDM" when file is `SYS-CDM.md`
- `relates_to` targets as `"[[SYS-DAIP]]"` — quoted wikilinks, valid YAML, Obsidian resolves them
- `last_verified` as unquoted ISO date — gets Obsidian's date picker
- Property names lowercase with underscores — Obsidian normalizes to lowercase

**The `## Related` section duplicates frontmatter `relates_to`** — intentionally. Frontmatter is for machines, Related section is for Obsidian's graph and human scanning. Claude generates both; validation checks they stay in sync.

**Full example of an Obsidian-compatible Reef artifact:**
```yaml
---
id: "SYS-CDM"
type: "system"
title: "CSG Data Manager"
domain: "cdm"
status: "draft"
last_verified: 2026-04-09
freshness_note: "review when CDM's case model or auth middleware changes"
freshness_triggers:
  - "cdm:src/models/study.py"
  - "cdm:src/services/case.py"
known_unknowns:
  - "Unclear how image deduplication works across modalities"
tags:
  - cdm
  - system
aliases:
  - "CDM"
  - "CSG Data Manager"
relates_to:
  - type: "depends_on"
    target: "[[SYS-DAIP]]"
  - type: "feeds"
    target: "[[SYS-RDP]]"
  - type: "integrates_with"
    target: "[[SYS-CTL]]"
sources:
  - category: "implementation"
    type: "github"
    ref: "cdm:src/models/study.py"
  - category: "implementation"
    type: "github"
    ref: "cdm:src/services/case.py"
notes: ""
---

## Overview
The CSG Data Manager handles case/study/image curation for breast and chest radiology...

## Key Facts
- CDM owns breast and chest radiology case management → `cdm:src/services/case.py`
- CDM does NOT own annotation workflows (that's [[SYS-CTL]]) → verified with CTL team
- Case status transitions are enforced at the service layer → `cdm:src/services/case.py:L45-89`
- Image deduplication uses perceptual hashing → `cdm:src/utils/dedup.py`

## Responsibilities
...

## Related
- Depends on: [[SYS-DAIP]] (auth and identity)
- Feeds: [[SYS-RDP]] (sends processed cases for pipeline ingestion)
- Integrates with: [[SYS-CTL]] (annotation handoff)
```

Not claim-based pages (too rigid for conversational discovery). Not plain prose (no per-fact verification). The Key Facts section is claims-lite: human-readable, each fact linked to a source, individually lintable — without C1/C2 machine IDs.

---

### B3. Is the relationship model rich enough?

**Answer:** Already resolved in A3/A4. Expanded from 3 to 7 relationship types:

| Type | Meaning | Example |
|---|---|---|
| `parent` | belongs to | PROC-CDM-CASE → SYS-CDM |
| `depends_on` | requires | SYS-CDM → SYS-DAIP |
| `refines` | adds detail | API-CDM-REST → SYS-CDM |
| `constrains` | governs/limits | DEC-AUTH-PATTERN → API-CDM-AUTH |
| `supersedes` | replaces | DEC-NEW-AUTH → DEC-OLD-AUTH |
| `feeds` | sends data to | SYS-CDM → SYS-RDP |
| `integrates_with` | bidirectional exchange | SYS-CDM ↔ SYS-CTL |

`feeds` and `integrates_with` are particularly valuable for PMs understanding data flow and system boundaries. `constrains` and `supersedes` capture decision governance. All relationship types render as `[[wikilinks]]` in the Related section for Obsidian graph compatibility.

---

### B4. Should source references use content hashes?

Reef tracks sources as `source_label:relative/path`. Onco-PE tracks `source_url | updated_at_source | content_hash | transform_warnings`.

Content hashes enable:
- Detecting when a source file changed since the artifact was written
- Knowing which artifacts are stale without re-reading files
- Confidence scoring (artifact based on file that hasn't changed = high confidence)

**Is this worth the complexity for MVP?**

**Answer:** Yes — but the approach depends on the source type. Resolved in A3:

**Git-tracked code sources:** Git diffs are the primary freshness signal. More informative than hashes — you see *what* changed, not just *that* it changed. Reef already indexes source folders that are git repos.

**Raw specs (OpenAPI, ERD, schema dumps):** Content hashes. Reef detects these during indexing, copies them to `sources/raw/` (wiki is self-contained with a snapshot), and hashes them. Health check compares current hash vs. snapshot. Separate `sync-sources` action refreshes specs without running full lint.

**Non-git sources (Confluence, org charts, RACI):** Content hashes fill the gap where git tracking isn't available. For Confluence, `confluence_version` in frontmatter is an existing approach from CSG. For other organizational documents, SHA-256 hash of the file content.

**Source snapshots at artifact-write time (MVP):** When an artifact is accepted, Reef captures the content hash + last modified timestamp of every source file Claude read. Stored in `.reef/artifact-state/{id}.json`. This is cheap (~20 lines of code) and enables the entire freshness/lint story. Cannot be backfilled — must capture at write time.

**Confidence scoring:** An artifact whose source files haven't changed since write time = high confidence. An artifact with 3 stale sources = low confidence. This falls out naturally from the source snapshot mechanism — no extra work needed.

---

## C. Discovery Flow & System Prompt

### C1. Is question-driven discovery actually better than auto-generation?

Karpathy's ingest operation is: drop a source, LLM processes it, updates 10-15 pages automatically. No questions.

Reef's approach: Claude asks questions, user answers, Claude reads files, proposes one artifact at a time.

**Arguments for Reef's approach:**
- User validates each artifact → higher quality
- Discovery surfaces things code alone can't tell you (org context, business rules, historical decisions)
- The conversation IS the value — user learns about their own systems

**Arguments against:**
- Slow. 30 minutes for a basic wiki vs. potentially 5 minutes for auto-generation.
- Friction. Users who "just want docs" have to participate.
- The questions might feel repetitive for someone who knows their system well.

**Should Reef offer both modes?** (Guided discovery for first-time + auto-ingest for subsequent sources)

**Answer:** Yes — both modes, and the user picks the depth. Reef should offer three discovery modes, mapped to a depth metaphor:

**1. Snorkeling (auto-ingest, fast, minimal human input)**
- Claude reads the source index, generates a batch of artifacts automatically.
- User reviews and accepts/skips. No back-and-forth conversation required.
- Best for: adding a new source to an existing wiki, well-structured repos with clear boundaries, "just get me started" users.
- Output quality: broad but shallow. Captures what's visible from file structure and code surface. Misses organizational context, business rules, historical decisions.

**2. Scuba-diving (guided discovery, conversational, human-in-the-loop)**
- Claude asks targeted questions about each system/domain. User answers. Claude reads code to verify and proposes artifacts one at a time.
- Best for: first-time setup of a critical system, repos where the interesting knowledge isn't obvious from code alone, users who want to learn about their own systems.
- Output quality: deep and contextualized. Captures the "why" behind design choices, org-specific terminology, cross-system dependencies that aren't in any single codebase.

**3. Deep-diving (exhaustive, human-directed, maximum depth)**
- User directs Claude to explore specific areas in detail. Claude reads entire directories, traces execution paths, maps every function. User provides domain framing that reshapes how Claude interprets the code.
- Best for: complex subsystems where shallow reading misses the real behavior, regulatory/compliance-sensitive areas, producing artifacts that will be used as canonical references.
- Output quality: the highest possible. Captures algorithms, heuristics, thresholds, edge cases, and handoff contracts.

**Evidence that depth modes matter — PROC-RDP-CS-TASK-PLAYBOOK:**

This 914-line artifact is the strongest proof that auto-generation alone is insufficient. It references ~50 source files across 7 flow families and produces:
- A **Flow-Execution Unit Catalog** (3 detailed tables mapping every flow to its Prefect tasks, flow-local functions, utilities, and primary responsibility).
- A **Stakeholder Review Priority** matrix (P0/P1/P2 tiers by data-correctness impact).
- **Detailed Logic** sections capturing algorithms (white-pixel ratio > 0.5 for scanned report detection, SHA256-based duplicate detection, study_joining hash generation, join-key selection).

An auto-ingest LLM reading `rdp/projects/cs/flows/` would produce a surface-level summary: "ingestion flow processes DICOMs, study_joining combines records." It would miss the critical insight that `flow.py` files are thin orchestration shells — the real execution logic lives in `functions.py` files, shared `tasks/*.py` modules, and `utilities/` helpers scattered across the repo. The playbook exists because a human reframed the question: "don't just list Prefect tasks — treat every function that materially affects runtime behavior as an **execution unit**, regardless of where it's defined." That framing decision is what makes the artifact useful, and no auto-ingest can produce it without human direction.

**How this maps to the 4-phase lifecycle:**
- **Phase 1 (Bootstrap):** Default to Scuba-diving. User is building initial understanding. Snorkeling available as "quick start" option. Deep-diving available for critical systems.
- **Phase 2 (Expand):** Default to Snorkeling. Claude proposes artifacts for unexplored files in batches. User can escalate any artifact to Scuba/Deep if the auto-generated version is insufficient.
- **Phase 3 (Maintain):** Snorkeling-equivalent. Git diffs trigger automatic update proposals. No conversation needed unless Claude flags a conflict.
- **Phase 4 (Lint):** No depth mode — fully automated validation pass.

**The key insight:** The depth modes aren't just UX sugar — they map to genuinely different reading strategies. Snorkeling reads file structure + top-level definitions. Scuba reads file contents + asks clarifying questions. Deep-diving traces execution paths across the entire repo and reinterprets code through a human-provided lens. Each produces fundamentally different artifacts.

---

### C2. Is 7 discovery phases the right structure?

Current phases:
1. System Boundaries → SYS-
2. Data Model → SCH-
3. API Surface → API-
4. Processes → PROC-
5. Decisions → DEC-
6. Glossary → GLOSSARY-
7. Cross-System Contracts → CON-

**Challenges:**
- Phase 2-3 (Data Model, API) require deep code reading. Is Claude good enough at this via file reading, or does it need actual schema/OpenAPI spec parsing?
- Phase 5 (Decisions) depends heavily on user's memory, not code. Should it be earlier in the flow?
- Phase 7 (Contracts) only works with 2+ systems. For a single-system project, this phase is empty. Does that feel broken?
- Karpathy's pattern has no phases — it's organic. Does phased discovery feel too rigid?

**Answer:** The 7 phases are the right *conceptual order* but the wrong *enforcement mechanism*. Here's why:

**The ordering is sound.** You can't write a PROC- (process) artifact without knowing the SYS- (system boundary) it belongs to. You can't write a CON- (contract) without at least two SYS- artifacts. The dependency graph between artifact types is real:

```
SYS- → SCH- / API- → PROC- → DEC- → GLOSSARY- → CON-
         (can be parallel)         (can be parallel)
```

**But rigid phases are wrong for three reasons:**

1. **Discovery isn't linear.** Reading code for SCH- (Phase 2) will surface process behavior (Phase 4) and decisions (Phase 5) simultaneously. Forcing the user to "wait for Phase 4" when the insight is right there kills momentum. The RDP playbook was built by following execution paths — it crossed data model, process, and decision territory in a single pass.

2. **Depth modes (C1) already replace phases.** Snorkeling generates all artifact types in one pass — phases don't apply. Scuba-diving follows the user's curiosity — phases are a suggestion, not a gate. Only Deep-diving might benefit from a focused phase ("let's exhaustively map all processes in CDM"), but even then the user picks the focus, not a phase number.

3. **Phase 7 (Contracts) isn't a phase — it's a trigger.** Contracts should be proposed whenever Claude notices a cross-system boundary during any phase, not held until the end. If Claude is reading CDM code and finds a webhook call to CTL, that's the moment to propose CON-CDM-CTL-*, not after 6 other phases.

**What to do instead:**

- **Guided priorities, not phases.** In Scuba mode, Claude follows a priority order: establish system boundaries first (SYS-), then fill in based on what it finds. But it can propose any artifact type at any time.
- **Artifact type dependencies as soft constraints.** If Claude proposes a PROC- before its parent SYS- exists, show a warning ("this process references SYS-CDM which doesn't exist yet — create it first?"), not a blocker.
- **Contract detection is always-on.** Whenever Claude reads code that calls another system (webhooks, API clients, shared DB access, message queues), it flags the cross-system boundary. This works with 1 or 4+ sources.

**On the specific challenges:**

- **Phase 2-3 (SCH/API) and code reading:** Claude is good enough at reading Python/Go models and OpenAPI specs via file reading. The real question is whether it needs the *whole* spec or just the parts relevant to the current discovery. Answer: use `sources/raw/` for full specs (sync-sources), let Claude read selectively from artifacts that point to them.
- **Phase 5 (Decisions) placement:** Decisions surface organically — move it up? No. Remove the concept of placement entirely. DEC- artifacts get proposed when Claude or the user spots a design choice that isn't obvious from code alone. Could happen at any point.
- **Phase 7 (Contracts) with single source:** Not broken if contracts are always-on detection rather than a phase. With one source, Claude simply doesn't detect cross-system boundaries (or detects them as outbound dependencies — "CDM calls an external webhook at X"). The user never sees an empty "Phase 7."
- **Karpathy's organic approach vs. phases:** Reef's guided priorities give structure without rigidity. In Snorkeling mode, it's fully organic (like Karpathy). In Scuba mode, Claude steers the conversation through priorities but follows the user's lead. Best of both.

---

### C3. Where is Reef's "lint" operation?

Karpathy explicitly calls out **lint** as a core operation: health-check for contradictions between pages, stale claims, orphan pages, missing cross-references, data gaps.

Reef has no equivalent. The "Update Wiki" trigger re-indexes and asks Claude to update, but there's no explicit validation pass.

**Should Reef have a "Health Check" button that:**
- Finds artifacts with no incoming `relates_to` references (orphans)
- Finds broken `relates_to` targets (dangling references)
- Checks if source files referenced in `sources` still exist
- Lists artifacts where `known_unknowns` is empty (suspiciously confident)
- Identifies potential contradictions between artifacts

**Answer:** Yes — this is Phase 4 of the lifecycle model (Lint & Health Check), already decided in A2/A3. The answer here is about *specifics*.

**What the Health Check does (mechanical, no LLM needed):**

1. **Orphan detection** — artifacts with no incoming `relates_to` references from any other artifact (except SYS-, which are roots). Flags: "SCH-CDM-CASE-MODEL has no parent link pointing to it."
2. **Dangling references** — `relates_to` targets that don't resolve to an existing artifact ID. Flags: "PROC-CDM-CASE-LIFECYCLE references SYS-CDM-V2 which doesn't exist."
3. **Source file existence** — checks if files in `sources` frontmatter still exist on disk (for local sources) or in the source index. Flags: "API-CDM-BREAST references cdm:src/api/breast.py which was deleted."
4. **Frontmatter schema validation** — required fields present, valid enums, id matches filename, dates parseable, `relates_to` entries have required `rel` field.
5. **Key Facts without source links** — Key Facts that don't reference a source file. Flags: "fact 3 in SCH-CDM-CASE-MODEL has no source pointer."
6. **Wikilink/frontmatter sync** — body `[[wikilinks]]` in `## Related` section should match `relates_to` entries. Flags mismatches.
7. **Freshness** — artifacts whose `last_verified` date is older than the last-modified date of their source files (via git or content hash comparison from `.reef/artifact-state/`).

**What requires Claude (LLM-assisted lint):**

8. **Empty `known_unknowns`** — flag as "suspiciously confident" and ask Claude to review whether the artifact genuinely has no gaps.
9. **Contradiction detection** — Claude reads pairs of artifacts that share `relates_to` targets and checks for conflicting claims in Key Facts. Example: if PROC-A says "status transitions require API call" and PROC-B says "status can be changed directly in DB," that's a contradiction.
10. **Stale claims** — Claude re-reads the source file referenced by a Key Fact and checks if the claim still holds. This is the most expensive check (requires file reads) and should be opt-in or run on a schedule.

**UX in Reef:**

- **Health Check button** in the status footer — runs checks 1-7 mechanically, shows a report card.
- **Deep Health Check** — runs 8-10 with Claude. More expensive (API calls), user triggers explicitly.
- Report format: categorized findings (errors / warnings / info), each with the artifact ID, the issue, and a suggested fix. User can click to navigate to the artifact.
- Health Check results logged to `.reef/log.md` with timestamp and finding count.

**This is NOT v2 — it ships in MVP.** The mechanical checks (1-7) are trivial to implement (JSON schema validation + file existence checks + graph traversal). The LLM checks (8-10) are Phase 4 of the lifecycle but can ship as a button from day one. Karpathy called lint a core operation for good reason — without it, the wiki degrades silently.

---

### C4. Should good chat answers become artifacts?

Karpathy: "Good answers can be filed back into the wiki as new pages. A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history."

In Reef, only explicitly proposed artifacts (via `write_artifact`) become wiki pages. If a user asks "how does CDM handle image deduplication?" and Claude gives a great answer in chat, that answer is lost when the conversation ends.

**Options:**
1. Do nothing — artifacts are intentional, not accidental. This is fine.
2. Add a "Save as artifact" button on any Claude message — user can promote an answer to a DEC- or PROC- artifact.
3. Claude proactively proposes to save good answers as artifacts.

**Answer:** Artifacts should be creatable from conversation — but rarely from a single message.

**The lived experience (from building CSG knowledge repo):** When creating an artifact based on conversation, it's never based on "just one" answer. It's based on the accumulated context — the back and forth. "What flows exist?" → "What tasks do they run?" → "No, look at the global tasks too" → "Treat each as an execution unit." The artifact emerges from the whole thread, not one response. A single-message "Save" button misses this.

**Why not option 1 (do nothing):** The CSG discovery files prove this is a real need. Those 2,810 lines of discovery notes were continuously referenced during artifact creation and used as completeness checks. In Reef, that knowledge would be trapped in `conversation.json` — technically persisted but practically inaccessible.

**Why not option 3 (Claude proactively proposes):** Too noisy. Users habituate to dismissing prompts. Let them pull, don't push.

**How it works — hybrid approach:**

1. Every Claude message gets a subtle "Save" icon. Clicking it triggers artifact creation.
2. **Claude auto-selects the relevant message range.** It looks backward in conversation to find all messages that contributed to the insight. Shows the user: "I'll base this artifact on messages 12-19 [highlighted in chat]. Want to include or exclude anything?"
3. User adjusts the selection if needed (add earlier context, exclude tangents).
4. Claude synthesizes the selected messages into proper artifact structure (frontmatter, required sections, Key Facts) and proposes it as a normal artifact card.
5. User accepts/skips as usual.

**Why this hybrid works:**
- Default behavior (Claude infers context) is low-effort — one click to start.
- User can adjust — full transparency and control over what feeds the artifact.
- Accounts for the reality that artifacts come from threads, not single messages.

**What types of answers get saved:**
- Comparisons and analyses → DEC- (decision record, since the analysis captures a judgment)
- "How does X work" explanations → PROC- (process artifact)
- "What's the relationship between X and Y" → CON- (contract) or the answer gets folded into an existing artifact's Key Facts
- Terminology clarifications → added to GLOSSARY-

**MVP scope:** The "Save" icon, Claude's context inference with highlighted message range, and the artifact-proposal flow. Don't build a separate "notes" or "scratch" storage — the artifact contract is the only format.

---

## D. Multi-Source & Scale

### D1. How does the system prompt handle 4+ sources with 300 files each?

4 sources × 300 files = 1,200 file entries. Even summarized as directory trees, this is 3,000-5,000 tokens of file tree alone. Plus ~2,600 tokens of static prompt. That's ~8,000 tokens of system prompt before any conversation.

**Questions:**
- At what point does the file tree become too large for the context window?
- Should file trees be dynamically expanded? (Show top-level dirs first, Claude requests deeper listing via a tool)
- Should there be a `list_directory` tool in addition to `read_file`?

**Answer:** The file tree should be **lazy-loaded, not dumped into the system prompt**.

**The math:** 4 sources × 300 files at ~4 tokens per path = ~5,000 tokens. That's manageable for Claude's 200K context, but it's wasteful. Most of those paths are irrelevant to the current conversation. And with larger repos (1,000+ files per source), the tree alone could eat 20K+ tokens — real context pressure.

**Strategy: summary in system prompt, details via tool.**

1. **System prompt gets a compact summary per source** (~200 tokens each):
   ```
   ### [cdm] ~/Projects/cdm (342 files)
   Python/FastAPI backend. Key directories:
   - src/applications/ (breast/, chest/) — API endpoints
   - src/models/ — SQLAlchemy models
   - src/services/ — business logic
   - migrations/ — Alembic DB migrations
   ```
   This gives Claude enough to know *where to look*, not every file.

2. **`list_directory(source, path, depth)` tool** — Claude requests deeper listings when it needs them. Returns file names + sizes + last-modified. Depth parameter controls recursion (default 1, max 3).

3. **`search_files(source, pattern)` tool** — glob search across a source's index. Claude can find files by pattern without browsing the entire tree. Example: `search_files("cdm", "**/*model*.py")`.

4. **`read_file(source, path)` stays as-is** — reads a specific file.

**Why this is better than full tree in prompt:**
- Claude uses the summary to orient, then drills down intentionally. This mirrors how a human navigates a codebase — you don't memorize every filename, you know the directory structure and search for specifics.
- Saves 3,000-15,000 tokens of context per conversation, which matters more as the conversation gets longer.
- Scales to any repo size without prompt engineering.

**What goes in the system prompt (always):**
- Source list with labels, paths, file counts
- Per-source directory summary (top 2 levels, annotated)
- Existing artifacts list (IDs + titles + types)
- Current discovery state (what's been covered, what hasn't)

---

### D2. Does the `source:path` format scale?

When Claude calls `read_file("cdm:src/models/study.py")`, it needs to know the source label and exact path. With 4+ sources and 1,200+ files, will Claude reliably get the labels and paths right?

**Potential issues:**
- Claude might confuse similar filenames across sources
- Claude might hallucinate paths not in the file tree
- Labels might be ambiguous (two sources both named "api")

**Mitigations to consider:**
- Validate paths against the source index before reading
- Return suggestions ("did you mean cdm:src/models/study.py?") on 404
- Auto-deduplicate labels on add

**Answer:** The `source:path` format is correct and will scale, with the mitigations listed above — all three should be implemented.

**Path validation is non-negotiable.** Every `read_file` call checks the source index before hitting disk. If the path doesn't exist: return the error plus the 5 closest matches (fuzzy/Levenshtein). This catches both hallucinated paths and minor typos. Cost: one hash lookup per read — negligible.

**Label deduplication is enforced at add-time.** When a user drops a folder, Reef auto-generates a label from the folder name. If it collides, append a suffix (e.g., `api` → `api-2`) and let the user rename. Labels are short, lowercase, no spaces — enforced by the UI.

**Claude won't struggle with this format.** Claude already handles `source:path` patterns well (it's conceptually identical to monorepo paths like `packages/cdm/src/...`). The lazy-loaded tree from D1 means Claude isn't memorizing 1,200 paths — it's navigating via `list_directory` and `search_files`, then constructing the full `source:path` from results. The tool responses include the full qualified path, so Claude copies rather than constructs.

**One additional mitigation:** When Claude references a source label that doesn't exist, return the list of valid labels. This catches the "wrong label" case cleanly.

---

### D3. Is local-only the right bet?

**For:**
- Privacy. Codebases are sensitive. No cloud = no risk.
- Simplicity. No auth, no server, no accounts.
- Ownership. Users own their wiki files completely.

**Against:**
- Can't share wikis with teammates (without git + manual setup)
- Can't use on iPad, phone, or any device without the desktop app
- Can't run Reef as a CI step or scheduled job

**Is local-first a v1 constraint that enables speed, or a permanent product principle?**

**Answer:** Both — but for different reasons.

**Local-first is a permanent product principle** because of the use case. Reef's users are pointing it at production codebases, internal systems, org charts, and compliance-sensitive documentation. Sending file contents to Anthropic's API is already a trust boundary — adding a Reef cloud server is a second trust boundary that most engineering orgs won't accept. The privacy argument isn't just a feature — it's a prerequisite for the target market.

**Local-first also enables shipping speed** for MVP. No auth, no accounts, no server infrastructure, no multi-tenant data isolation. But this isn't the reason to stay local — it's the reason not to delay shipping by building a server.

**The "Against" arguments are real but solvable without a server:**

- **Sharing with teammates:** The wiki is a folder of markdown files. `git init` + push to a shared repo gives version-controlled collaboration for free. Reef can offer a "Share via Git" action that initializes a repo and pushes. This is better than a cloud sync because it uses the team's existing git infrastructure and access controls.
- **Mobile/iPad access:** If the wiki is in a git repo, it's viewable on GitHub/GitLab. If it's in an Obsidian vault synced via iCloud, it's on every Apple device. Reef doesn't need to solve this — the output format (markdown) already solves it.
- **CI/scheduled jobs:** A headless `reef-cli` that runs the same core logic (source indexer, system prompt, Claude API, artifact writer) without the Electron shell. This is a v2 product extension, not a v1 requirement. The architecture should keep the core logic separate from the UI to enable this path.

**One nuance:** "local-first" means the wiki and project state live on the user's machine. It does NOT mean "offline-first" — Reef requires an internet connection to call the Claude API. Don't confuse the two in marketing.

---

## E. Target User & Go-to-Market

### E1. Will PMs/TPMs actually use a tool that requires an API key?

The target user is "product managers and technical program managers." These people:
- May not have an Anthropic API key
- May not know how to get one
- May be uncomfortable with per-token billing
- May not have budget approval for API costs

**Is BYOK the right model for this audience?** Alternatives:
- Bundle API access with a subscription (Reef handles billing)
- Offer a free tier with limited usage
- Partner with Anthropic for a promotional API credit

**Answer:** BYOK is the right model for MVP, but it limits the addressable market. Here's the honest assessment:

**BYOK is correct for launch because:**
- Reef ships this week. Billing infrastructure is weeks of work (Stripe, usage metering, rate limiting, abuse prevention). Not happening.
- The *first* users aren't random PMs — they're people in Jessi's network, people who already have API keys or are technical enough to get one. The initial audience self-selects.
- BYOK means zero marginal cost for Reef. No subsidy, no burn rate, no "we're losing money on every user."
- Privacy story is stronger: "Your key, your data, your API calls. Reef never sees your code."

**But it will filter out the target persona:**
- A PM who manages 5 services but doesn't write code probably doesn't have an Anthropic API key. Getting one requires: creating an account, adding a payment method, understanding token pricing, and being comfortable with variable billing. That's 4 friction points before they even open Reef.
- The "uncomfortable with per-token billing" concern is real. A 30-minute discovery session with 4 sources might cost $2-8 depending on depth. That's cheap, but unpredictable costs feel expensive.

**Path forward:**
1. **MVP: BYOK only.** Gate-kept to technical users and people in your network. This is fine — the product needs to prove its value before optimizing the funnel.
2. **v1.1: Add estimated cost display.** Before each Claude call, show "~$0.03 for this response" so users aren't surprised. Reduces billing anxiety.
3. **v2: Subscription with bundled API.** Reef proxies Claude API calls, user pays a flat monthly fee (e.g., $29/month for X artifacts/month). This is the unlock for the PM persona. But only build this after product-market fit is proven with BYOK users.

**Don't partner with Anthropic for credits yet.** That conversation happens after you have traction numbers. Ship, get users, then negotiate.

---

### E2. What's the activation flow?

From download to "aha moment" — how many steps?

Current flow: Download DMG → Install → Open → Enter API key → Pick model → Drop folders → Wait for indexing → Start chatting → Wait for Claude → Accept first artifact → Open wiki folder.

That's **10 steps** before the user sees value. NotebookLM is 2 steps (open, upload).

**Can this be shortened?** Ideas:
- Skip model selection (default to Sonnet, change later in settings)
- Auto-start discovery after first source is added (no "Start" button)
- Show the first artifact inline without requiring the user to open the wiki folder

**Answer:** The 10-step count is misleading — several of these steps take zero cognitive effort. But the real activation flow still has friction worth cutting.

**Revised flow (7 steps, 3 cuts):**

1. Download + Install → Open (unavoidable)
2. Enter API key (unavoidable for BYOK — but pre-fill model with Sonnet, **cut model selection screen**)
3. Drop folder(s) onto window (the core gesture — make it delightful)
4. ~~Wait for indexing~~ → **Index in background, show progress in source pill** ("cdm ◔ indexing..." → "cdm ✓ 342 files"). Don't block the user.
5. ~~Start chatting~~ → **Auto-start.** The moment the first source is indexed, Claude sends the first message: "I can see [cdm] has a FastAPI backend with breast and chest applications. Let's start by mapping the system boundary. What is CDM's primary responsibility?" No "Start" button.
6. Chat → Claude proposes first artifact (usually SYS-)
7. Accept first artifact → **shown inline with full preview**, not just "saved to disk." The artifact card expands to show the rendered markdown. User sees the output *inside Reef*.

**That's 7 steps: install, key, drop, chat, accept.** Steps 3-7 are the product loop. Compared to NotebookLM's 2 steps (open, upload), Reef is inherently more steps because it produces something permanent, not an ephemeral chat answer. The value tradeoff: NotebookLM gives instant Q&A, Reef gives a lasting wiki. The extra steps are justified if each one feels productive.

**The real "aha moment" isn't the first artifact — it's the second source.** When a user drops their second repo and Claude says "I notice [ctl] makes annotation webhook calls to [cdm]. Let me map this boundary..." — that's when Reef's multi-source value clicks. Design the flow to get there fast: after the first SYS- artifact, prompt the user to add another source.

---

### E3. What's the "show" moment for LinkedIn/Twitter?

You plan to post on LinkedIn Monday after shipping. What screenshot or video demonstrates the value in 10 seconds?

**Options:**
- Before/after: messy codebase folder → structured wiki with 12 artifacts
- Time-lapse: 30-second clip of the discovery conversation, artifacts appearing
- The index.md: a beautifully structured table of contents that didn't exist before
- A specific artifact: a CON- contract that reveals something the user didn't realize
- The compact UI itself: a small, beautiful tool doing something complex

**Answer:** The time-lapse and the contract artifact — combined.

**The 30-second demo video:**
1. (0-5s) Empty Reef window. User drags 3 folders onto it. Source pills appear: [cdm] [ctl] [daip].
2. (5-15s) Speed-up of the discovery conversation. Artifacts cards appear and get accepted — SYS-CDM, SYS-CTL, SCH-CDM-CASE-MODEL flowing past.
3. (15-22s) Normal speed. Claude says: "I found that CDM sends annotation webhooks to CTL, but there's no retry mechanism. This is a reliability risk." A CON-CDM-CTL-ANNOTATION card and a RISK-CDM-CTL-WEBHOOK-RELIABILITY card appear.
4. (22-28s) User clicks the artifact count. Wiki opens in Obsidian. The graph view shows SYS-CDM as a hub with connections radiating out. Beautiful, organic, alive.
5. (28-30s) Tagline: "Your codebases, mapped."

**Why this works:**
- The drag-and-drop is visually satisfying and immediately understandable.
- The speed-up shows Reef *doing work* — it's not a static screenshot.
- The contract + risk discovery is the "wow" moment — Reef found something the user didn't know about their own systems.
- The Obsidian graph is the visual payoff — a living knowledge graph, not just markdown files.

**For a static screenshot (LinkedIn post):** The Obsidian graph view with 8-12 nodes connected, captioned with the artifact count and source count. "4 repos. 12 artifacts. 30 minutes. Zero documentation existed before." That's a screenshot people share.

---

### E4. Who is the first paying customer?

If Reef becomes a paid product, who pays for it and why?

- **Startup CTO** who just hired 3 engineers and needs onboarding docs → one-time purchase
- **Platform team PM** managing 5+ services with no documentation → recurring (wikis need maintenance)
- **Consulting firm** doing technical due diligence on acquisition targets → per-project
- **Solo founder** trying to document their own spaghetti codebase → impulse purchase

**Which persona should Reef optimize for first?**

**Answer:** The **Platform team PM** managing 5+ services with no documentation.

**Why this persona wins:**

- **Recurring need.** Services change, teams rotate, knowledge decays. This persona needs Reef *continuously*, not once. That's a subscription, not an impulse purchase.
- **Highest pain.** They're in meetings where someone asks "how does service X talk to service Y?" and nobody knows. They've tried getting engineers to write docs — it doesn't stick. They've tried Confluence — it's a graveyard. Reef solves their actual daily problem.
- **Multi-source is the killer feature.** This persona oversees *multiple* services. Single-repo tools don't help them. Reef's multi-source model with cross-system contracts is built for this exact use case. The CON- and RISK- artifacts are their deliverables.
- **Budget authority.** PMs at platform teams have tooling budgets. $29/month for a tool that replaces weeks of doc writing is an easy sell.
- **Network effect.** If one platform PM finds Reef useful, they show it to their engineering lead, who shows it to the CTO. The wiki itself becomes a shared asset.

**The startup CTO is the second persona** — similar pain (no docs), but one-time use rather than recurring. Good for initial traction and word-of-mouth.

**The consulting firm is v2** — they need white-labeling, export formats, and possibly multi-tenant features. Don't optimize for them now.

**The solo founder is a trap** — lowest willingness to pay, smallest repos, least need for multi-source. They'll use Claude Code directly and be fine.

---

## F. Technical Risks

### F1. Claude's file reading ability

Reef depends on Claude being able to read source files and extract meaningful information. In practice:

- Can Claude understand a 50KB file well enough to produce accurate artifacts?
- What about minified files, generated code, or binary-adjacent formats (protobuf, SQL migrations)?
- What if the most important information is spread across 20 files? Claude's tool use loop needs to read them all.

**Should Reef pre-process certain file types?** (e.g., parse OpenAPI specs, extract SQL schema from migrations, summarize large files)

**Answer:** Claude's file reading ability is good enough for Reef's use case, with two caveats.

**What works well (tested empirically with CSG repos):**
- Python/TypeScript/Go source files up to ~40KB — Claude reads, understands, and synthesizes accurately.
- OpenAPI JSON specs — Claude can parse and interpret these, though large specs (>100KB) benefit from being broken into sections.
- Markdown documentation — trivially good.
- SQL migration files — Claude understands CREATE TABLE, ALTER TABLE, and can reconstruct the current schema from a migration history.
- YAML/TOML config files — no issues.

**What struggles:**
- **Files >50KB:** Claude's accuracy degrades. Long files get summarized rather than fully understood. Mitigation: Reef's `read_file` tool should return a warning if a file exceeds 40KB and offer to return it in chunks (first N lines, or a specific function/class).
- **Generated/minified code:** Useless to read directly. Mitigation: the source indexer should skip common generated patterns (`*.min.js`, `dist/`, `node_modules/`, `__pycache__/`, files with a "generated" header comment). This is already handled by `.gitignore` respecting, but add additional patterns.
- **Binary-adjacent formats (protobuf, Avro, Thrift):** `.proto` files are readable and useful. Compiled binary formats are not. Mitigation: read `.proto` definitions, skip compiled outputs.

**Pre-processing — selective, not universal:**
- **OpenAPI specs:** Copy to `sources/raw/` via sync-sources (already decided). Claude reads from there. No further processing needed — Claude handles JSON/YAML specs natively.
- **SQL migrations:** Don't pre-process. Claude can read migration files directly and is good at reconstructing current state from sequential ALTER TABLE statements. If the repo has a schema dump (many do — `schema.sql` or `schema.rb`), point Claude at that instead.
- **Large files:** Don't summarize automatically — that loses the detail that makes Deep-diving valuable. Instead, give Claude the `read_file` tool with offset/limit parameters so it can read sections of large files.

**The real risk isn't file reading — it's reading *enough* files.** The RDP playbook required reading ~50 files. A single Claude conversation with tool use can handle this, but it's slow (each file read is a tool call round-trip). Mitigation for MVP: accept the latency. Mitigation for v2: batch file reads (return multiple files in one tool response).

---

### F2. Artifact quality without validation

Reef writes whatever Claude generates (after user acceptance) to disk. There's no validation that:
- The frontmatter matches the schema
- The artifact body has the required sections for its type
- The `relates_to` targets actually exist
- The `sources` references point to real files

**Is user review sufficient quality control, or does Reef need automated validation?**

**Answer:** Already answered comprehensively in C3 (Health Check) and A3 (validation-on-accept). Summary:

**User review is necessary but not sufficient.** Users are good at judging whether an artifact is *useful* and *accurate*. They are bad at checking whether frontmatter schema is valid, whether `relates_to` targets exist, and whether source file paths are correct. Those are machine jobs.

**Two layers of validation, already decided:**

1. **Validation on accept** (blocking + warning):
   - Blocking: frontmatter schema, required fields, id/filename match, valid enums, Key Facts present.
   - Warning: `relates_to` targets exist, `sources` refs resolve, body sections present, `## Related` / frontmatter sync.

2. **Health Check** (on-demand, post-hoc):
   - Mechanical: orphans, dangling refs, source file existence, freshness, schema compliance.
   - LLM-assisted: contradictions, stale claims, suspiciously empty `known_unknowns`.

This is not a gap — it's already the plan.

---

### F3. Conversation context growth

As the conversation grows (20+ messages, 10+ tool calls, 5+ artifacts), the conversation history sent to Claude grows. Combined with the system prompt, this could approach context limits.

**Mitigations:**
- Summarize older messages
- Drop tool call results from history (keep only the latest N)
- Use a sliding window
- Start a new conversation for each discovery phase

**Answer:** Context growth is a real constraint but manageable with a layered strategy.

**The math:** Claude's context window is 200K tokens. System prompt (compact, per D1): ~3,000 tokens. Each user message + Claude response pair: ~500-2,000 tokens. Each tool call (file read) result: ~1,000-5,000 tokens. A 30-minute Scuba session might have 20 message pairs + 15 file reads = ~60,000-100,000 tokens of conversation history. That leaves 100K-140K tokens of headroom. Tight but workable for a single session.

**Mitigation strategy (layered, cheapest first):**

1. **Compact tool results in history.** After a `read_file` result has been used to generate an artifact, replace the full file contents in conversation history with a summary: "Read cdm:src/models/study.py (287 lines, SQLAlchemy model with Patient, Study, MedicalImage entities)." This alone recovers 60-80% of context consumed by tool calls.

2. **Artifact snapshots replace conversation.** Once an artifact is accepted, the artifact itself captures the knowledge from that conversation segment. Claude doesn't need to remember the back-and-forth that produced it — the artifact is the compressed output. Include accepted artifact IDs in the system prompt ("Existing artifacts: SYS-CDM, SCH-CDM-CASE-MODEL, ...") so Claude knows what's been covered.

3. **Session boundaries for natural breaks.** Don't start a new conversation per phase (too rigid, per C2). Instead, offer a "New session" option when context is getting full (~70% used). The new session starts with: full system prompt + existing artifact list + a summary of the previous session's key findings. The user never loses context — it's compressed into the artifact layer.

4. **Never silently truncate.** If context is approaching the limit, tell the user: "This session is getting long. I'd recommend starting a new session — I'll carry forward everything in your wiki." Transparent, not magical.

**What NOT to do:**
- Sliding window (drops early context that might be critical — the user said something in message 3 that's relevant in message 25).
- Automatic summarization of user messages (lossy — the user's exact words matter for artifact quality).

---

## G. Experience & Feel

Reef's thesis is that **deep human involvement produces dramatically better knowledge than automation**. The CDM discovery file alone is 1,792 lines across 36 questions — each answered with Fact / Why it matters / Source / Confidence / Open question. This depth is the product's moat. But depth requires sustained effort, and sustained effort requires an experience that rewards it.

### G1. What makes the discovery process feel fun vs. feel like work?

Jessi described the CSG discovery process as genuinely enjoyable — "digging up truths." What specifically made it fun?

**Possible sources of joy:**
- The surprise of finding something you didn't know about your own system
- The satisfaction of seeing messy knowledge become structured
- The feeling of building something cumulative (each artifact adds to the whole)
- The collaborative dynamic with Claude (it asks, you answer, it synthesizes)
- The visual result (a clean wiki where there was nothing before)

**Which of these does the current Reef UI support? Which does it undermine?**

Consider:
- Chat messages disappear above the fold. Do you feel the accumulation?
- Artifacts appear as cards and then vanish once accepted. Is there a sense of building?
- The status bar says "12 artifacts" but you can't see them without opening Finder. Is that satisfying?
- The compact window means you never see the full wiki. Is that a feature (focus) or a loss (no reward)?

**Answer (from lived experience building CSG knowledge repo):**

Not everything was fun. Sometimes it was heavy, sometimes tedious. But three things produced genuine happiness:

1. **Discovery surprise.** Finding out what I hadn't known before about my own systems. This was real and intrinsic — no UX trick can manufacture it, but the product can amplify it (Claude highlighting unexpected findings).
2. **Creation satisfaction.** Watching 180+ artifacts get created at one click, one enter, one command. Seeing messy knowledge become well-structured, laid-out artifacts. The magic of seeing it happen.
3. **Impact anticipation.** Organizing the Confluence documentation layer — knowing it would help coworkers, solve a real problem that I had failed to solve months earlier with manual documentation. The output *mattered*.

**What was missing / what would improve the experience:**

- **Knowing how far I've come and how far to go.** I gauged progress based on curated questions, but the number wasn't fixed — it grew or shrank as my knowledge landscape changed. There was no stable progress indicator.
- **Visible artifact accumulation.** Seeing how many artifacts were made adds to pride and satisfaction. A count is nice; a *shape* (types, depth, coverage) is better.
- **Rewarding deep effort.** Deep discovery takes a lot from you. You think hard, dig through code, reframe questions. The UX should acknowledge and reward that effort visually.

**How Reef addresses each of these:**

**Progress → Coverage indicator (not percentage):**
The scope is genuinely unknown — can't show "60% complete" when the total is undefined. Instead, show *coverage*:

```
┌─────────────────────────────────────┐
│  [cdm] ████████▓▓▓▓░░░░  74% · deep · 6 artifacts
│  [ctl] ███▓░░░░░░░░░░░░  18% · shallow · 1 artifact
│  [rdp] ░░░░░░░░░░░░░░░░  not started
│
│  34 Key Facts · 7 Known Unknowns
│  3 SYS · 2 SCH · 1 PROC · 1 CON · 1 RISK
└─────────────────────────────────────┘
```

Each source gets a single dual-layer bar:
- Light fill (█) = **breadth** — files Claude has read at least once.
- Dark fill (▓) = **depth** — files that contributed Key Facts, were read multiple times, or explored in Scuba/Deep-dive.
- Depth label (shallow / moderate / deep) is a heuristic: <2 Key Facts per artifact = shallow, 2-5 = moderate, 5+ = deep.

This gives an instant read: "I've *seen* 74% of CDM and *deeply explored* most of it. CTL is barely touched." Actionable — the user knows where to invest next.

**Accumulation → Artifact ribbon + progress narrative:**
- Artifact ribbon (pills colored by type) grows visually as artifacts are accepted. You *see* the wiki building.
- Status footer tells a story: "3 systems · 2 schemas · 1 contract · 1 risk flagged" — not just "8 artifacts."

**Rewarding depth → Visual weight:**
- Deep-dived artifacts feel *weightier* in the ribbon (thicker border, subtle glow).
- Session summary distinguishes: "3 surface artifacts, 2 deep artifacts."
- Deep artifacts have more Key Facts, more sources — and these counts are visible on the card.

**Seeing the result → "Open in Obsidian" button:**
- Status footer includes an "Open in Obsidian" button that uses `obsidian://open?path={wiki_folder}/index.md` to launch the wiki directly in Obsidian.
- If Obsidian is installed: one click to see the full knowledge graph.
- If not installed: falls back to "Open in Finder."
- The Obsidian graph view — with SYS- nodes as hubs and connections radiating out — is the visual payoff that makes all the effort feel worth it.

---

### G2. What should the "moment of pride" look like?

After 30 minutes of discovery, the user has a wiki with 8-12 artifacts. What does the product do to make them feel proud of what they built?

**Options:**
- Show a visual summary: "You documented 3 systems, 4 processes, and 2 contracts. Your wiki covers 847 source files across 4 repos."
- Generate a beautiful index.md they can screenshot and share
- Animate the artifact count growing in the status bar
- Show a relationship graph (even simple) of how artifacts connect
- Produce a "wiki health" score (coverage, gaps, freshness)
- Open the wiki folder automatically and highlight the new files

**Which of these would make a PM want to post a screenshot on LinkedIn?**

**Answer:** Three moments of pride, in sequence:

**Part 1: See how much you covered (coverage indicator).**
The dual-layer coverage bars show breadth and depth per source. Already addressed in G1. This is the "I explored a lot" feeling.

**Part 2: See how much you created (session summary + Obsidian graph).**
After a discovery session, Reef shows a summary card:

```
Your reef is growing

3 SYS · 2 SCH · 1 PROC · 1 CON · 1 RISK
34 Key Facts · 7 Known Unknowns
847 source files · 4 repos · 28 minutes

[Open in Obsidian]  [Test Your Reef]
```

Then "Open in Obsidian" → the user sees the knowledge graph with SYS- nodes as hubs and connections radiating out. This is the visual payoff. The screenshot moment.

**Part 3: See it genuinely answer real-life questions ("Test Your Reef").**

This is the moment that converts pride into conviction. After building the wiki, the user asks a real question they'd normally need a meeting with 4 engineers to answer:

```
User: "Which systems are affected if we change CDM's case status model?"

Claude (grounded in your reef):

  ✓  CDM case lifecycle would need updating
     → PROC-CDM-CASE-LIFECYCLE (8 Key Facts)

  ✓  CTL annotation handoff depends on case status
     → CON-CDM-CTL-ANNOTATION (status must be 'ready')

  ✓  RDP ingestion reads case status for study upload
     → PROC-RDP-CS-TASK-PLAYBOOK (study_upload_to_cc flow)

  ⚠  DAIP authorization rules may reference case status
     → SYS-DAIP (shallow — 3 Key Facts, needs deeper exploration)

  3 artifacts answered fully · 1 needs deeper exploration
```

**Why this is the most important pride moment:**
- It validates the whole approach — "I spent 30 minutes and now I can answer questions that used to require a cross-team meeting."
- It cites which artifacts answered the question — the user sees their work paying off.
- It surfaces gaps honestly — "DAIP is shallow, I can't fully answer this part." Not a failure — a guide for where to dive next.
- **The gap-to-action loop:** When the reef can't fully answer, Claude offers: "Want me to deep-dive into DAIP's authorization rules to fill this gap?" The user's real question becomes the discovery directive. This is the most natural transition from surface to depth — driven by a real need, not an abstract "explore more."

**Part 3 extended: Question Bank as persistent validation.**

"Test Your Reef" is powerful as a one-off, but even more powerful as a **living benchmark**. Before or during discovery, the user submits real questions they need answered: "How does auth work across services?", "What's the disaster recovery plan for RDP?", "Which systems are affected if we change the case status model?"

These questions become:
- **A north star** — the reef exists to answer them. "7/12 questions answered" is the most meaningful progress metric possible.
- **A discovery guide** — unanswered questions tell Claude where to focus during Scuba/Deep-dive. The user's real problems steer the discovery.
- **An ongoing health check** — run "Validate all" anytime. If a ✓ drops to ⚠ after code changes, that's freshness signal grounded in real impact.
- **A design input** — during Scuba, Claude prioritizes exploring areas related to unanswered questions.

Stored in `.reef/questions.json`. Lightweight input: text field + "Add" button. Not required — but if present, deeply integrated into the discovery loop and progress display.

**For MVP:** All parts are buildable:
1. Coverage indicator — string generation from tracked file reads (already planned).
2. Session summary card — counting accepted artifacts by type (trivial).
3. "Test Your Reef" / Question Bank — Claude reads existing artifacts + answers grounded in them. Questions stored in `.reef/questions.json`. Validate button runs all questions. Status shows "7/12 answered" in footer. No new infrastructure — just a mode where Claude answers from the wiki instead of from source code, plus a JSON file for the question list.

---

### G3. Should Reef have personality?

The system prompt currently says "You are Reef, a knowledge architect." Should the product have a consistent voice and personality?

**Arguments for:**
- PMs spend 30+ minutes in conversation. Personality makes it engaging, not transactional.
- A distinctive voice ("I found something interesting in your auth module...") creates emotional connection.
- It differentiates from generic AI tools.

**Arguments against:**
- Personality can be annoying if it gets in the way of work.
- Different users have different tolerance for "personality."
- It's hard to maintain consistently across long conversations.

**If yes, what personality? Options:**
- Curious researcher: "Hmm, this is interesting — your CDM has two separate auth patterns..."
- Calm architect: "Based on what I've read, the system boundary is here. Let me verify."
- Enthusiastic intern: "Oh wow, I found the entity model! This is more complex than I expected."

**Answer:** Yes, personality — but **Curious Researcher**, not the other two.

**Why Curious Researcher:**
- It matches the activity. Discovery IS research. The user is investigating their own systems. A personality that mirrors genuine curiosity validates the user's effort: "this is worth being curious about."
- It creates the right dynamic: two people exploring together, not a tool executing commands (Calm Architect) or a subordinate reporting findings (Enthusiastic Intern).
- Curiosity naturally produces the best conversational patterns: "Hmm, this is interesting — I see two auth patterns in CDM. Was that intentional, or did the second one creep in?" That's a question that surfaces a DEC- artifact.

**Why NOT Calm Architect:**
- Too dry for a 30-minute session. PMs aren't looking for a stoic consultant — they want a collaborator who makes the process engaging.
- "Based on what I've read, the system boundary is here" is *informative* but not *inviting*. It doesn't pull the user into the discovery.

**Why NOT Enthusiastic Intern:**
- Undermines trust. If the tool is surprised by what it finds, the user wonders if it understands the codebase. "Oh wow, this is more complex than I expected" signals *incompetence*, not enthusiasm.
- Gets annoying fast. Sustained enthusiasm feels performative after 10 minutes.

**Implementation notes:**
- The personality lives in the system prompt's Identity layer. Not hard-coded responses — just tone guidance.
- Keep it subtle. "I noticed something interesting" not "🔍 Fascinating discovery!" No emojis. No exclamation marks in findings.
- The personality should adapt to depth mode: more curious and conversational in Scuba, more efficient and direct in Snorkeling, more thorough and precise in Deep-diving.

---

### G4. Does the compact window help or hurt the experience?

520×740 was chosen for "utility, not IDE" feel. But:

- **Helps:** Focus. No distractions. The conversation is intimate, like a DM. The tool feels light, approachable.
- **Hurts:** Chat messages are narrow. Artifact previews are cramped. You can't see the file tree and the conversation simultaneously. Complex artifacts (schemas, APIs) need width.

**Should Reef be resizable?** Options:
- Fixed size (current): consistent, opinionated, utility-like
- Fixed with an "expand" mode: compact by default, but can pop out to full-size for artifact review
- Freely resizable with a minimum: user chooses their experience
- Two modes: "chat mode" (compact) and "review mode" (wider, shows wiki alongside chat)

**Answer:** Two modes — **compact (default) + full screen**. No in-between.

The original 520×740 felt right for conversation, but with the new elements we've added (artifact ribbon, coverage indicator, question bank status, reef health, depth-weight visuals), there's too much to cram into compact mode. Rather than a contextual expand that feels unpredictable, give the user two clear modes:

**Compact (520×740, default):** The focused utility. Chat + source bar + artifact ribbon (single row) + input bar + status footer. This is where conversation and discovery happen. The status footer shows compressed info: "7/12 questions · 8 artifacts · fresh".

**Full screen (Cmd+F toggle):** The full picture. Chat on the left (~60%), detail panel on the right (~40%). Everything visible: coverage bars with breadth+depth, question bank with ✓/⚠/✗, artifact preview with full-width markdown, reef health bitmap, health check reports. This is where you review, validate, and see your reef.

**Why this works:**
- Compact stays clean — detailed views moved to full screen. No cramming.
- Two opinionated sizes. No manual resizing, no ambiguity.
- One toggle (keyboard shortcut or title bar button). Simple mental model: "working" vs "seeing everything."
- The status footer is the bridge — compact shows counts, full screen shows details.

**Why not the other options:**
- **Contextual expand (previous answer):** Unpredictable. Window changing size based on content is disorienting.
- **Freely resizable:** Kills the opinionated feel. Reef decides, not the user.
- **Fixed only:** Can't fit everything we've designed. The compact window was right for v1 scope; the stress test expanded the scope.

---

### G5. What's the visual identity?

The current UI is dark theme with indigo accent. It's functional but generic — could be any Electron app.

**What should Reef look and feel like?**

Consider the metaphor: a coral reef is organic, colorful, alive, layered. Not a dark terminal. Not a sterile dashboard.

**Directions to consider:**
- **Ocean depth:** Dark base but with subtle blues, teals, gradients that evoke water. Source pills as colorful coral. Artifacts as living organisms.
- **Warm workspace:** Lighter theme, warm tones, feels like a well-organized desk. Artifacts as cards/papers. Professional, not technical.
- **Minimal/ink:** Near-white background, black text, minimal color. Let the content speak. Like a beautifully typeset document.
- **Keep current dark theme:** It works, developers expect it, don't overthink it.

**What would make a PM open this app and think "this is beautiful, I want to use this"?**

**Answer:** **Deep ocean-blue + text-rendered graphics + bitmap coral character.**

The key insight: we can't build fancy futuristic UI in 4 days, and we don't need to. **Text is the medium.** All data visualization uses Unicode block characters in monospace — coverage bars, progress indicators, accumulation counts. This is both beautiful and achievable. It's not a compromise — it's the identity.

**The design system:**

1. **Deep ocean-blue base.** Not pure black, not gradient — solid `#0a1628` with slightly lighter panels (`#0f2035`) for cards and inputs. Very subtle variations of the same deep blue. Feels like depth without trying hard.

2. **Text-rendered graphics everywhere.** Coverage bars (`████████▓▓▓▓░░░░`), artifact counts (`3 SYS · 2 SCH · 1 PROC`), progress status (`Snorkeling · reading src/models/...`). Rendered as monospace `<pre>` blocks. Copy-pasteable. Updates by regenerating strings. No SVG, no canvas, no custom components.

3. **Bitmap coral character.** A small pixel-art coral motif — 8x8 or 12x12 grid — in the spirit of Claude Code's terminal aesthetic. Appears in: title bar (tiny), startup/loading, session summary header, app icon (scaled up). Blocky, minimal, monospace-compatible. Not illustrated — pixel art.

4. **One warm accent: coral (#FF7F50).** Source pills, artifact type badges, ribbon highlights. The only warm color against the deep blue. Like actual coral on a reef floor.

5. **Monospace for data, proportional for prose.** Chat messages and artifact body text use a proportional font. Everything structural (coverage, metadata, status, Key Facts) uses monospace. Two type systems that reinforce the distinction between "conversation" and "structured output."

**Why this works better than a designed UI:**
- Achievable in 4 days — CSS custom properties + string generation, not component design.
- Distinctive — no other Electron app looks like this. It's recognizable.
- Consistent with the product — Reef produces structured text (markdown artifacts). The UI renders structured text. The medium is the message.
- Copy-pasteable — coverage indicators, session summaries can be shared as text. Users paste them in Slack/GitHub.
- Beautiful on dark backgrounds — Unicode blocks with the ocean-blue palette have a terminal-meets-depth aesthetic that's genuinely appealing.

---

### G6. What micro-interactions matter?

Small UX details that make sustained effort feel rewarding:

- **Artifact accepted:** What happens? Currently: "Saved to disk" text appears. Should it: animate, pulse, celebrate, play a subtle sound, update a progress indicator?
- **Source added:** A new pill appears. Should it: slide in, glow briefly, trigger a re-index animation?
- **Discovery phase transition:** Claude moves from System Boundaries to Data Model. Should there be a visual marker? A progress bar? A phase indicator?
- **Known unknown captured:** Claude admits it doesn't know something. Should this feel like progress (honest gap found) or failure?
- **Chat streaming:** Currently tokens appear as text. Should there be: a typing indicator, a thinking animation, a status like "Reading cdm:src/models/study.py..."?

**Which of these are worth building for MVP? Which are distractions?**

**Answer (from lived experience):**

All micro-interactions are text-rendered. No animations. No sound effects. Consistent with the design system: monospace status text updating to show progress.

**MVP — all text-based, all present-participle:**

- **Chat streaming status (the most important one).** During every Claude interaction, a monospace status line shows what's happening:
  ```
  Snorkeling · reading cdm:src/models/study.py...
  Scuba-diving · exploring auth patterns in daip...
  Deep-diving · tracing 12 files in flows/ingestion...
  Validating · checking 12 questions against reef...
  Refreshing · 2 sources updated, checking artifacts...
  ```
  Always a present participle. Always showing the specific thing. The user never stares at a blank screen.

- **Artifact created.** Pill appears in ribbon. Status footer updates: "8 artifacts → 9 artifacts". Question count may tick up if the new artifact answers a question: "7/12 → 8/12 questions".

- **Question answered.** Status footer ticks the count. That's it — subtle but satisfying.

- **Freshness check done.** Reef health updates in status footer: "aging → fresh". In full screen, bitmap coral fills back in.

- **Known unknown captured.** Amber text treatment in the artifact: "Gap identified: image dedup across modalities." Feels like progress (honest gap found), not failure.

- **Source added.** Pill appears in source bar with "◔ indexing..." state, then "✓ 342 files". No animation — just text state change.

**Not building:**
- Sound effects — no. Apps that make unexpected sounds get force-quit.
- Animations (slide-in, pulse, confetti) — no. Text state changes are the interaction.
- Phase transition markers — phases are gone (C2).

---

## H. The Big Question

### H1. Is Reef a product, a tool, or a methodology?

- **As a product:** A desktop app you download, point at repos, and get a wiki. Competes with documentation tools.
- **As a tool:** An open-source CLI or library that developers integrate into their workflow. Competes with Claude Code.
- **As a methodology:** A published framework (like Karpathy's LLM Wiki doc) that anyone can implement with any LLM. Competes with blog posts.

**Which of these is the primary thing Reef should be?** The answer determines everything: pricing, distribution, open-source vs. closed, marketing, community.

**Answer:** Reef is a **product** — and the methodology is its moat, not its deliverable.

**Why product, not tool or methodology:**

- **A methodology** (like Karpathy's blog post) is free and inspires many implementations — but generates zero revenue and has no defensibility. Jessi already has the methodology (the CSG knowledge repo proves it). Publishing it helps Reef's credibility but isn't the business.
- **A tool** (CLI/library) competes with Claude Code, which is free and infinitely more flexible. Every developer who can use a CLI will use Claude Code + their own CLAUDE.md. Jessi already proved this works. There's no gap to fill for developers.
- **A product** bundles the methodology + the tool + the UX into something that non-developers can use without building it themselves. The artifact contract, the discovery flow, the multi-source indexing, the validation — none of these are available to someone who just has Claude Code and good intentions. They'd have to invent all of it. That invention is what Reef sells.

**What this means for key decisions:**

| Decision | Implication |
|----------|------------|
| **Pricing** | Paid product (after validation). Free trial or generous free tier to reduce friction. |
| **Distribution** | Direct download from seaof.ai. Not npm, not homebrew, not a VS Code extension. |
| **Open-source** | The methodology documents (artifact contract, discovery flow) can be open. The product (Electron app, system prompt, validation logic) is closed-source. Open methodology builds trust and community; closed product captures value. |
| **Marketing** | "Reef builds structured knowledge from your codebases" — not "here's a framework for building knowledge." The value prop is the output, not the process. |
| **Community** | Users share their wikis and discovery patterns, not their Reef forks. The community forms around the output format (Obsidian-compatible markdown with the artifact contract), not the tool's source code. |

---

### H2. What is the one thing that makes Reef worth existing?

Strip away everything — the tech stack, the artifact types, the system prompt. If Reef does exactly one thing better than anything else, what is it?

**Candidates:**
- "It makes the invisible knowledge in your codebases visible and structured."
- "It turns a PM's questions into a navigable knowledge graph."
- "It's the only tool where human curiosity and AI synthesis compound together."
- "It produces documentation that agents can actually use."

**Pick one. That's your tagline, your pitch, and your design north star.**

**Answer:** *Jessi — only you can pick this. But here's my honest ranking and why:*

**My pick: "It makes the invisible knowledge in your codebases visible and structured."**

**Why this one:**
- It describes a transformation the user can *see*. Before Reef: scattered code across repos, knowledge trapped in developers' heads. After Reef: a structured, navigable wiki. The before/after is immediate and compelling.
- "Invisible" is the key word. The knowledge already exists — in code, in architecture decisions, in cross-system dependencies — but nobody can see it. Reef makes it visible. That's not generating docs — it's revealing what's already there.
- It works for every persona: the PM who can't read code ("my codebases have knowledge I can't access"), the CTO who needs onboarding docs ("the knowledge is there but invisible to new hires"), the platform team ("we have 12 services and nobody can see how they connect").

**Why not the others:**

- "Turns a PM's questions into a navigable knowledge graph" — too narrow. Limits the market to PMs and overemphasizes the graph view. The knowledge graph is one output, not the core value.
- "The only tool where human curiosity and AI synthesis compound together" — too abstract. "Human curiosity" and "compound" require explanation. A tagline shouldn't need a footnote.
- "Produces documentation that agents can actually use" — the agent-readability angle is technically true but emotionally flat. PMs don't care about agents. And "documentation" undersells what Reef produces — it's not docs, it's structured knowledge with relationships, validation, and freshness tracking.

**Shortened for marketing:** "Make the invisible visible." Or simply: "Your codebases, mapped."

---

*All 34 questions answered. Now: update PLAN.md with decisions from Sections C-H, then proceed to build.*
