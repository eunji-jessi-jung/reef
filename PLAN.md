# Reef — Product & Build Plan

## 1. What Reef Is

Reef is a compact macOS desktop utility that builds structured knowledge repositories from multiple codebases and sources. You point it at your source folders, chat with Claude, and it generates a living wiki of structured, interlinked markdown artifacts on disk — then helps you keep it current as your systems evolve.

**Brand:** Reef is the product. seaof.ai is the company/domain.

**Metaphor:** A coral reef — knowledge compounds through many small structured contributions over time. Anti-fragile, living, self-sustainable.

**One-liner:** "Make the invisible knowledge in your codebases visible and structured."

**Short:** "Your codebases, mapped."

---

## 2. Who It's For

**Primary persona:** Platform team PM managing 5+ services with no documentation. Recurring need — services change, teams rotate, knowledge decays. They're in meetings where someone asks "how does service X talk to service Y?" and nobody knows. Multi-source with cross-system contracts is their killer feature.

**Secondary:** Startup CTOs needing onboarding docs, engineering leads needing bird's-eye views.

**Anti-persona:** Solo founders with small codebases (Claude Code is enough), consulting firms (need features we don't have yet).

**What they have in common:** They deal with knowledge that spans multiple repos, services, and teams. Documentation is scattered, stale, or nonexistent. They understand Git and repos but don't have time to synthesize everything by hand.

**Reef is a product, not a tool or methodology.** The methodology (artifact contract, discovery flow) can be published openly for credibility. The product (app, system prompt, validation) is closed-source. Distribution is direct download from seaof.ai. **Free for now** — monetization is deferred (employment constraint). BYOK is the only model.

---

## 3. Core Value Proposition

1. **Multi-source discovery** — Point at N repos/folders simultaneously. Reef indexes them all and gives Claude cross-system context.
2. **Progressive depth** — Starts fast: drop a folder, get surface-level artifacts in under 5 minutes with zero questions. Then go deeper: Scuba (conversational discovery) and Deep-dive (exhaustive analysis) unlock naturally as the user engages. No mode picker — depth is a progression, not a setting.
3. **Structured output** — Not loose markdown. Every artifact has typed YAML frontmatter, relationships, source references, Key Facts, and explicit known unknowns. The output is a queryable knowledge graph, not a pile of notes.
4. **Local-first** — Everything runs on your machine. No server, no cloud, no database. Output is plain markdown files you own, can git-commit, and can open in Obsidian, VS Code, or any editor.
5. **Cross-system contracts** — The real power: once individual systems are documented, Reef identifies the boundaries between them and generates contract artifacts documenting what two systems agree on (and where they don't).
6. **Code + docs reconciliation** — Reef reads both code (ground truth) and documentation (organizational context). When they conflict, Reef flags it: "the architecture doc says X, the code does Y."
7. **Four-phase lifecycle** — Human-guided bootstrap for depth, then increasingly automated expansion, maintenance, and health checks. The product gets you past the manual phase into sustainable automated maintenance.
8. **Foundation for agent work** — The wiki isn't the end product — it's the layer that makes everything downstream possible. Agents can use the structured knowledge to plan features, find systemic risks, write PRDs/SRDs grounded in real system understanding, and even implement from specs. The closed loop: code → knowledge → specs → code.

---

## 4. Product Lifecycle Model

Reef's value proposition includes not just building the initial library, but sustaining it over time. Human involvement scales down as the library matures:

### Phase 1: Bootstrap (human-heavy)

Guided discovery. Claude asks questions, reads code, proposes artifacts one at a time. The user validates everything. This is where depth and context come from — organizational knowledge, business decisions, the *why* behind architectural choices. No pipeline can replace this phase.

### Phase 2: Expand (mixed)

Once the initial library exists, Claude scans unexplored files, proposes new artifacts in batches. The user reviews batches rather than guiding every step. "I found 14 files in `cdm:src/services/` that aren't covered by any artifact. Here are 3 proposed artifacts — review?"

### Phase 3: Maintain (mostly automated)

Source changes detected via git diffs + content hashes. Affected artifacts flagged. Claude proposes updates. User reviews diffs, not full artifacts. The health check runs, the change classification kicks in, `log.md` gets appended.

### Phase 4: Lint & Health Check (fully automated)

Orphans, dangling refs, stale Key Facts, contradictions between artifacts — all checked without human trigger. Reports generated. User decides what to act on.

---

## 5. How It Works (User Flow)

### First Launch (3 steps — under 90 seconds)

1. Open Reef → compact 520×740 floating panel appears
2. Enter Anthropic API key → one field, one button. Stored encrypted. Model defaults to Sonnet. Privacy disclosure shown inline.
3. Drop a folder onto Reef (or use file picker).
  - **Smart repo detection:** If the dropped folder contains `.git/` repos at depth 1-2 (e.g., dropping `~/Projects/cdm/` which contains `csg-case-curator-backend/` and `csg-case-curator-frontend/`), Reef asks: "I found 2 repos inside cdm/. Add them as separate sources?"
  - Each repo becomes a labeled source pill. Labels auto-generated from repo folder names. User can rename.
  - Indexing happens in background per-repo (pill shows "◔ indexing..." → "✓ 342 files").
  - **Repo-to-system mapping:** Before the surface pass, Claude asks in natural language: "Which repos belong together as one system? Tell me in your own words." User can type freely (e.g., "case-curator-backend and case-curator-frontend are both CDM") or click **Skip** to treat each repo as its own system. Mapping is stored in `.reef/project.json` and editable later via source bar context menu. Claude may also suggest merges later when it discovers connections in code (e.g., shared API contracts).

### Surface Pass — First 5 Minutes (automatic, zero questions)

1. The moment indexing completes, Claude auto-starts in **Snorkeling mode**. No mode picker. No questions. No "Start" button. The user sees: "Analyzing your codebase..."
2. Claude reads the source summary, key files, and directory structure. Generates surface-level artifacts in rapid succession: SYS- first, then SCH-, API-, GLOSSARY- as it finds them.
3. Artifact cards appear one at a time. User just clicks **Accept** or **Skip**. No conversation needed.
4. Each accepted artifact slides into the **artifact ribbon** at top. Status footer updates: "3 artifacts · 1 system mapped"
5. After the surface pass (typically 3-6 artifacts in ~4 minutes), Claude pauses and invites depth:
  > "I've mapped the surface of [source]. Some of these are shallow — want me to dig deeper into [specific area]? Or drop another folder to find cross-system connections."

**The surface pass is the "aha moment."** User went from empty folder to a structured wiki without answering a single question. Now they understand what Reef produces, what artifact types look like, and what "structured knowledge" means. They're equipped to go deeper.

### Going Deeper (user-initiated, after surface pass)

1. **Scuba-diving** — User responds to Claude's invitation. "Tell me more about the case lifecycle." Claude asks targeted questions, reads code to verify, proposes richer artifacts one at a time. This is the conversational mode where organizational context, business rules, and the "why" get captured.
2. **Documentation sources (Claude-prompted, optional).** After the surface pass, Claude may notice terminology uncertainty or shallow context. It suggests docs naturally:
  > "I've mapped CDM's surface — I'm calling it 'Case Data Manager' based on the code. If you have any documentation (architecture docs, SRS, wiki exports), dropping them in would help me get the names and context right."
  >   User can drop doc files/folders at any time. Doc sources get a distinct pill style (`[cdm-docs 📄]`). Supported formats: markdown, plain text, PDF (text extracted on ingest), HTML (Confluence exports). Dropped docs are **copied** into `sources/docs/` in the wiki folder (originals stay put) — keeps the wiki self-contained and portable. For PDFs, both the original and extracted `.txt` are stored. Claude can `read_file("cdm-docs:architecture-overview.md")` just like code. After ingestion, Claude offers to correct existing artifacts: "Now that I've read the SRS, I see CDM is actually 'CSG Data Manager'. Want me to update SYS-CDM and the glossary?" **Not a required step** — but dramatically improves terminology accuracy and code comprehension when provided.
3. **Deep-diving** — User directs Claude to explore specific areas exhaustively. "Map every execution unit in the ingestion flows." Claude traces execution paths across the entire repo. Produces detailed canonical references (like the RDP playbook).
4. **Add more sources** — User drops another folder. Snorkeling runs automatically on the new source. Then Claude flags cross-system boundaries: "I notice [ctl] makes webhook calls to [cdm]. Want me to map this contract?"

There is no depth selector in the UI. Depth is a natural progression:

- **Snorkeling** happens automatically on every new source.
- **Scuba** happens when the user starts conversing after the surface pass.
- **Deep-diving** happens when the user gives Claude a specific directive to go exhaustive.

### Ongoing

1. User can add more source folders at any time (drag onto source bar → auto-snorkel).
2. User can open the wiki folder in Finder/Obsidian at any time (click status bar).
3. Session persists — close and reopen, resume where you left off.
4. Health Check button always accessible — runs lint: orphans, dangling refs, stale artifacts, contradictions (7 mechanical + 3 LLM-assisted checks).
5. **Question Bank + "Validate Reef"** — before or during discovery, user submits real questions they need answered. Stored in `.reef/questions.json`. Status footer shows "7/12 questions answered." "Validate" button runs all questions against the wiki — Claude cites which artifacts answered each, surfaces gaps, offers to deep-dive into unanswerable areas. Questions also guide Claude during Scuba (prioritize areas related to unanswered questions).
6. **Reef Health (always visible)** — automatic freshness indicator based on source git commits vs artifact `last_verified` dates. No user action needed. Shown as ✱ logo on project home + compact text in status footer. Health communicated by fading: Fresh (full brightness) / Aging (muted) / Stale (nearly invisible). No color for decay — coral stays purely positive. "Refresh" button re-indexes changed sources, runs quick health check, Claude proposes targeted updates for stale artifacts.
7. Any Claude message has a subtle "Save" icon. Clicking it triggers Claude to auto-select the relevant message range (the thread that produced the insight, not just one message), highlight it for review, and synthesize into an artifact proposal. User can adjust the selection before Claude generates.
8. Session summary card appears at natural stopping points: artifact counts by type, source file coverage, time spent.

---

## 5a. UX Language Guidelines

**Reef metaphor for status and personality. Plain language for actions and CTAs.**


| Context                       | Style                                            | Examples                                                                                                                 |
| ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **Status labels**             | Reef/ocean metaphor OK                           | "Snorkeling · reading src/models/...", "Scuba-diving · exploring auth patterns", "Deep-diving · tracing execution paths" |
| **Progress/accumulation**     | Reef metaphor OK                                 | "Growing · 4 artifacts · 2 systems", "Your reef is growing"                                                              |
| **Present-participle status** | Claude Code style — always show what's happening | "Analyzing...", "Reading cdm:src/models/study.py...", "Validating frontmatter..."                                        |
| **CTA buttons**               | Plain, instantly legible                         | "Drop a folder to start", "Accept", "Skip", "Start fresh session"                                                        |
| **Error messages**            | Plain, actionable                                | "Your Anthropic spending limit has been reached." — not "The reef hit a wall"                                            |
| **Artifact type labels**      | Plain                                            | "System", "Schema", "Contract" — not "Coral", "Reef node"                                                                |


---

## 5b. Visual Design System

**Design principle: Text is the medium, everywhere.** Not a limitation — an identity. All data visualization uses Unicode block characters in monospace. This is achievable in 4 days, distinctive, and beautiful on a dark background.

### Color Palette (v2)

**Principle: Seven blues. One coral. Nothing else.** No traffic-light colors. Coral is purely positive — brand, CTA, life. Staleness is communicated by fading, never by color.


| Name        | Hex       | Use                                       |
| ----------- | --------- | ----------------------------------------- |
| **Abyss**   | `#060f1d` | Base background                           |
| **Deep**    | `#0a1628` | Cards, panels, surfaces                   |
| **Mid**     | `#0f1e33` | Borders, dividers, hover states           |
| **Muted**   | `#7d93ad` | Secondary text, metadata                  |
| **Primary** | `#dbe4ef` | Body text, prose                          |
| **Bright**  | `#e8f0fe` | Headings, active elements                 |
| **Coral**   | `#FF7F50` | CTA, brand, type badges — always positive |


**Chat background gradient:** `radial-gradient(ellipse at 50% 75%, #0e2440 0%, #091828 35%, #060f1d 70%)` — subtle reef-floor glow.

**Health fading scale:** Fresh (`#dbe4ef`) → Aging (`#7d93ad`) → Stale (`#3d5068`). No color signal for decay — the reef just goes quiet.

### Text-Rendered Graphics

All data visualization uses monospace Unicode characters — no SVG, no canvas, no custom components:

```
Coverage bars:  ████████▓▓▓▓░░░░  (█ breadth, ▓ depth, ░ unseen)
Progress:       Snorkeling · reading src/models/study.py...
Accumulation:   3 SYS · 2 SCH · 1 PROC · 1 CON · 1 RISK
```

Rendered via `<pre>` or react-markdown in monospace. Copy-pasteable. Updates by regenerating the string.

### Logo — ✱ Heavy Asterisk (U+2731)

The logo is a Unicode glyph: ✱ (Heavy Asterisk). Coral-colored on deep blue.

- Works at every size — favicon, status bar, heading, watermark, app icon
- Already in every font, no asset file needed
- Looks like a coral polyp or sea urchin — radial, organic, branching
- Favicon: coral ✱ on `#0a1628` rounded rectangle (deep blue only, never coral background)

**Wordmark options:**

- Serif: `✱ Reef` (Iowan Old Style / Georgia)
- Mono: `✱ reef` (SF Mono)
- Umbrella: `✱ seaof.ai` (serif)

The ✱ doubles as a **health indicator** — three states by fading:

- **Fresh:** Full brightness (`#dbe4ef`)
- **Aging:** Muted (`#7d93ad`)
- **Stale:** Nearly invisible (`#3d5068`)

Shown on project home + status footer. Glanceable — the user instantly sees whether their reef is healthy without clicking anything.

### Typography

System fonts only. No web fonts, no license concerns.


| Role          | Font Stack                                         | Size | Weight | Line Height | Letter Spacing     |
| ------------- | -------------------------------------------------- | ---- | ------ | ----------- | ------------------ |
| Display       | Iowan Old Style, Palatino Linotype, Georgia, serif | 28px | 400    | 1.10        | -0.3px             |
| Heading       | Iowan Old Style, Palatino Linotype, Georgia, serif | 20px | 400    | 1.14        | -0.2px             |
| Body          | -apple-system, system-ui, sans-serif               | 14px | 400    | 1.47        | -0.1px             |
| Body emphasis | -apple-system, system-ui, sans-serif               | 14px | 600    | 1.24        | -0.1px             |
| Caption       | -apple-system, system-ui, sans-serif               | 12px | 400    | 1.33        | -0.08px            |
| Data/metadata | ui-monospace, SF Mono, Cascadia Code, monospace    | 12px | 500    | 1.5         | 0                  |
| Artifact ID   | ui-monospace, SF Mono, monospace                   | 11px | 500    | 1.0         | 0                  |
| Section label | -apple-system, sans-serif                          | 11px | 500    | 1.0         | 0.12em (uppercase) |


**Principles:** Tight headlines (1.10–1.14), open body (1.47). Negative letter-spacing at every size. Weight stays 400–600.

**Korean note:** Serif headings will fall back to system sans-serif for Hangul. Tight line-heights and negative tracking may need locale adjustment for Korean.

### Spacing, Radius & Elevation

**Spacing (8px base unit):** 2, 4, 8, 12, 16, 24, 32, 48, 80px

**Border radius:**


| Use                       | Radius |
| ------------------------- | ------ |
| Micro (inline elements)   | 4px    |
| Small (small buttons)     | 6px    |
| Default (buttons, inputs) | 8px    |
| Card                      | 10px   |
| Panel                     | 12px   |
| Chat bubble               | 14px   |
| Pill                      | 999px  |


**Elevation (3 levels):**

- **Flat:** Background contrast only. No shadow. Default for everything.
- **Raised:** `box-shadow: 0 2px 24px rgba(0,0,0,0.3)`. Chat frame, modals.
- **Glass:** `backdrop-filter: saturate(150%) blur(16px)` on translucent bg. Chat header/input, nav.

**Buttons:**


| Size    | Padding   | Radius | Font     | Min height |
| ------- | --------- | ------ | -------- | ---------- |
| Large   | 11px 28px | 10px   | 17px/500 | 44px       |
| Default | 8px 20px  | 8px    | 14px/500 | 36px       |
| Small   | 6px 14px  | 6px    | 12px/500 | 28px       |
| Pill    | 3px 10px  | 999px  | 11px/500 | —          |


### What This Means for Implementation

- `global.css` defines the palette as CSS custom properties
- Chat background uses radial gradient (reef-floor glow), everything else is flat
- Three font stacks: serif for headings, sans for prose/UI, mono for data
- Source pills are coral-accented. Non-system type badges use muted pills.
- Scrollbars: 6px wide, nearly invisible, `rgba(125,147,173,0.15)` thumb
- The overall feel: like a beautiful terminal app that happens to have a chat interface
- **Design reference file:** `project-tower/reef/design-system.html` — full interactive spec
- **Korean test file:** `project-tower/reef/korean-test.html`

**Principle:** The user should never have to decode the metaphor to understand what to do. The metaphor adds *warmth and personality* to status, not *friction* to actions.

---

## 6. Architecture

### System Architecture

```
┌──────────────────────────────┐
│        Reef (Electron)       │
│   Compact panel (520×740)    │
│                              │
│  ┌────────────────────────┐  │
│  │    Renderer (React)    │  │
│  │  Setup → Project → Chat│  │
│  └──────────┬─────────────┘  │
│             │ IPC             │
│  ┌──────────┴─────────────┐  │
│  │    Preload (Bridge)    │  │
│  └──────────┬─────────────┘  │
│             │ IPC             │
│  ┌──────────┴─────────────┐  │
│  │   Main Process (Node)  │  │
│  │                        │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Claude Client   │  │──── Claude API (Anthropic)
│  │  └──────────────────┘  │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Source Indexer   │  │──── Local filesystem (source repos)
│  │  └──────────────────┘  │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Wiki Manager    │  │──── Local filesystem (wiki output)
│  │  └──────────────────┘  │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Artifact Linter │  │  │  ← NEW: validation + health check
│  │  └──────────────────┘  │  │
│  │  ┌──────────────────┐  │  │
│  │  │  System Prompt   │  │  │
│  │  └──────────────────┘  │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### Source Types

Sources have a `type` field: `'code' | 'docs'`. Both are dropped onto the source bar the same way.


|                   | Code sources                                | Doc sources                                                                                  |
| ----------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **What**          | Git repos, project folders                  | PDFs, markdown docs, Confluence exports, SRS, architecture docs                              |
| **Indexing**      | Respects `.gitignore`, code-aware file tree | No `.gitignore`, all files included                                                          |
| **Parsing**       | None — Claude reads raw files               | PDF → text extraction on ingest (via `pdf-parse`). HTML → strip tags. Markdown/text → as-is. |
| **System prompt** | Compact directory summary (~200 tokens)     | File list with one-line descriptions (~100 tokens)                                           |
| **Pill style**    | `[cdm]` with coral accent                   | `[cdm-docs 📄]` with muted accent                                                            |
| **read_file**     | Returns raw file content                    | Returns extracted text (for PDF/HTML) or raw content (for md/txt)                            |
| **When added**    | At project creation (step 3)                | Any time — Claude suggests after surface pass when it notices terminology gaps               |


Doc sources improve Claude's output in two specific ways:

1. **Terminology accuracy** — without docs, Claude infers names from code (often wrong: "Case Data Manager" instead of "CSG Data Manager"). Docs fix this.
2. **Code comprehension** — SRS/architecture docs give Claude the "why" before it reads the "what." It reads code through the right lens.

### Data Flow

```
Source folders (N repos + doc folders/files)
  → Source Indexer (compact summaries + content hashes; PDF/HTML text extraction for doc sources)
  → System Prompt Builder (summaries + artifact contract + discovery methodology + depth mode)
  → Claude API (streaming, tool use)
  → Tool: list_directory (browse source tree on demand)
  → Tool: search_files (glob search across source index)
  → Tool: read_file (reads from source folders, with offset/limit for large files; returns extracted text for PDFs)
  → Tool: write_artifact (proposes artifact)
  → Artifact Linter (validates frontmatter, refs, required sections)
  → User approval (with validation warnings visible)
  → Wiki Manager (writes to disk, captures source snapshot, updates index, appends log)
  → Wiki folder (~/reef-wikis/{project}/)
```

### File Structure (Reef source)

```
reef/
├── package.json
├── tsconfig.json
├── electron-vite.config.ts
├── src/
│   ├── shared/                    # Types & constants shared across processes
│   │   ├── types.ts               # All TypeScript interfaces
│   │   └── constants.ts           # Artifact types, models, colors, ignore patterns
│   ├── main/                      # Electron main process
│   │   ├── index.ts               # App lifecycle, window config, IPC handlers
│   │   ├── claude-client.ts       # Claude API wrapper, streaming, tool dispatch
│   │   ├── source-indexer.ts      # Multi-source file tree walking + content hashing + repo detection
│   │   ├── source-syncer.ts       # NEW: detect + copy raw specs (OpenAPI, schemas) to sources/raw/
│   │   ├── system-prompt.ts       # Prompt assembly (identity + contract + discovery + context)
│   │   ├── wiki-manager.ts        # Wiki folder CRUD, artifact lifecycle, index generation
│   │   └── artifact-linter.ts     # NEW: validation on write + health check
│   ├── preload/
│   │   └── index.ts               # Secure IPC bridge (contextBridge)
│   └── renderer/                  # React UI
│       ├── main.tsx               # Entry point
│       ├── App.tsx                # Root component, view routing
│       ├── styles/
│       │   └── global.css         # Dark theme, compact layout
│       └── components/
│           ├── SetupScreen.tsx    # API key only (model defaults to Sonnet)
│           ├── ProjectHome.tsx    # Source folder drag-and-drop, project creation
│           ├── ChatPanel.tsx      # Chat UI with streaming + artifact cards + save icon
│           ├── SourceBar.tsx      # Source pills in chat view
│           ├── ArtifactCard.tsx   # Artifact proposal (accept/skip/preview)
│           ├── ArtifactRibbon.tsx # NEW: accepted artifact pills at top of chat
│           ├── SurfaceProgress.tsx # NEW: progress indicator during auto-snorkel ("Analyzing... 2/5 artifacts")
│           ├── CoverageIndicator.tsx # NEW: source coverage bars, artifact counts by type, Key Facts/Unknown counts
│           ├── SessionSummary.tsx # NEW: pride moment card (counts by type, coverage, deep vs surface)
│           └── HealthReport.tsx   # NEW: lint results display
└── resources/                     # App icon (reef/coral, ocean depth palette)
```

### Wiki Output Structure (generated per project)

```
~/reef-wikis/{project-name}/
├── index.md                       # Auto-generated artifact catalog
├── log.md                         # Append-only wiki evolution log
├── artifacts/                     # Zone 1: Canonical knowledge
│   ├── systems/                   #   SYS- artifacts (one per system/domain)
│   ├── schemas/                   #   SCH- artifacts (data models)
│   ├── apis/                      #   API- artifacts (service contracts)
│   ├── processes/                 #   PROC- artifacts (workflows, lifecycles)
│   ├── decisions/                 #   DEC- artifacts (architectural decisions)
│   ├── glossary/                  #   GLOSSARY- artifacts (term registries)
│   ├── contracts/                 #   CON- artifacts (cross-system boundaries)
│   └── risks/                     #   RISK- artifacts (known issues + severity)
├── sources/                       # Zone 2: Evidence + registries
│   ├── registries/                #   repos.yaml, org-chart.yaml, raci.yaml
│   ├── raw/                       #   API specs, schema dumps (auto-synced from source repos)
│   └── docs/                      #   User-provided docs (SRS, architecture, wiki exports) — copied on drop, PDF + extracted .txt
├── .reef/                         # Zone 3: Operational state (hidden)
│   ├── project.json               #   Project config: name, sources, model, timestamps
│   ├── source-index.json          #   Combined file manifest (paths + sizes + hashes)
│   ├── conversation.json          #   Chat history for resume
│   ├── artifact-state/            #   Per-artifact operational state
│   │   └── {artifact-id}.json     #     Source snapshot at write time, freshness status
│   ├── questions.json              #   User's question bank (north star + validation benchmark)
│   ├── source-artifact-map.json   #   Reverse index: source file → which artifacts
│   └── sessions/                  #   Lightweight session logs
│       └── {timestamp}.json       #     Sources scanned, artifacts created/flagged
└── .gitignore                     # Ignores conversation.json, .reef/sessions/
```

**Three zones:**

- **artifacts/** — canonical knowledge. The product's output. Human-reviewed, structured, interlinked.
- **sources/** — raw evidence, organizational registries, and user-provided documentation. Things code alone can't tell you.
- **.reef/** — operational state. Never edited by hand. Powers freshness, lint, and resume.

---

## 7. Tech Stack

### Runtime & Build


| Component       | Technology           | Version       | Why                                                                                                |
| --------------- | -------------------- | ------------- | -------------------------------------------------------------------------------------------------- |
| Desktop runtime | Electron             | 36.3.1        | Full filesystem access, compact window support, macOS vibrancy. Ship fast; migrate to Tauri in v2. |
| Build system    | electron-vite + Vite | 3.1.0 / 6.3.2 | Fast dev server, HMR, TypeScript, three-target build (main/preload/renderer).                      |
| Language        | TypeScript           | 5.8.3         | Strict mode. Shared types across all processes.                                                    |
| UI framework    | React                | 19.1.0        | Fast iteration on small UI. No SSR needed.                                                         |
| Packaging       | electron-builder     | 26.0.12       | macOS DMG distribution.                                                                            |


### Core Libraries


| Library           | Version | Purpose                                                                                     |
| ----------------- | ------- | ------------------------------------------------------------------------------------------- |
| @anthropic-ai/sdk | 0.39.0  | Claude API. Tool use for read_file and write_artifact. Streaming responses.                 |
| gray-matter       | 4.0.3   | Parse and serialize YAML frontmatter in artifact markdown files.                            |
| ignore            | 7.0.4   | Parse .gitignore files during source indexing.                                              |
| react-markdown    | 10.1.0  | Render artifact markdown in the UI. (Currently installed, not yet integrated.)              |
| remark-gfm        | 4.0.1   | GitHub Flavored Markdown support (tables, task lists, strikethrough).                       |
| pdf-parse         | 1.1.1   | Extract text from PDF documentation sources on ingest. Lightweight, no native dependencies. |


### What We're NOT Using (and Why)

- **No database.** State = filesystem + JSON files in `.reef/`. Simplest possible persistence.
- **No server.** Everything runs locally in Electron's main process. BYOK (bring your own key).
- **No state management library.** React state + prop drilling is enough for this UI size.
- **No CSS framework.** Custom dark theme in one CSS file. No build overhead.
- **No RAG/embeddings.** Claude reads files directly via tool use. No vector store, no chunking pipeline.
- **No authentication.** Local app, local data. The API key is the only credential.

### Architecture Decisions

**Why Electron over Tauri?**
Tauri would give us a 10MB binary instead of 150MB, with native OS webview. But Tauri's Rust backend means rewriting source-indexer, wiki-manager, and claude-client — or bridging them to Node. That's 2+ days spent on plumbing instead of product. Decision: ship with Electron, migrate to Tauri in v2 once product logic is proven.

**Why tool use instead of parsing Claude's text output?**
Claude's tool use API (`read_file`, `write_artifact`) gives us structured, validated input/output. No regex parsing of markdown blocks. The tool schema enforces that every artifact has an `id`, `type`, and `content`. This is more reliable and easier to extend.

**Why local filesystem instead of a database?**
The output IS the product. Users want markdown files they can git-commit, open in Obsidian, grep, and share. A database would be a translation layer between Claude's output and what users actually want. The `.reef/` directory handles app state as simple JSON.

---

## 8. The Artifact Contract (Product IP)

This is Reef's core intellectual property — the structured schema that makes the output valuable.

### 8 Artifact Types


| Type     | Prefix      | Purpose                                                     | Required Sections                                                   |
| -------- | ----------- | ----------------------------------------------------------- | ------------------------------------------------------------------- |
| System   | `SYS-`      | Entry point for a domain/service                            | Overview, Key Facts, Responsibilities, Core Concepts, Related       |
| Schema   | `SCH-`      | *Interpretation* of data models (not the raw ERD)           | Overview, Key Facts, Entities, Related                              |
| API      | `API-`      | *Interpretation* of API surfaces (not the raw OpenAPI spec) | Overview, Key Facts, Source of Truth, Resource Map, Related         |
| Process  | `PROC-`     | Workflow/lifecycle/behavior                                 | Purpose, Key Facts + archetype-dependent body, Related              |
| Decision | `DEC-`      | Architectural decision record                               | Context, Decision, Key Facts, Rationale, Consequences, Related      |
| Glossary | `GLOSSARY-` | Domain term registry                                        | Terms table (with `[[wikilinks]]` in Context column), Related       |
| Contract | `CON-`      | Cross-system boundary agreement                             | Parties, Key Facts, Agreement, Current State, Related               |
| Risk     | `RISK-`     | Known issues with severity tracking                         | Description, Key Facts, Impact, severity/resolution fields, Related |


**SCH- and API- clarification:** These artifacts capture the *interpretation and context* that raw specs can't provide — business rules, usage patterns, deprecation status, cross-system dependencies. The raw spec (OpenAPI, ERD, schema dump) lives in `sources/raw/` and the artifact points to it. They are NOT prose restatements of the spec.

`**## Related` section:** Every artifact (except Glossary, which uses wikilinks in the Terms table) ends with a `## Related` section that renders `relates_to` relationships as `[[wikilinks]]`. This duplicates frontmatter intentionally — frontmatter is for machines, Related is for Obsidian's graph view and human scanning. Claude generates both; validation checks they stay in sync.

### Frontmatter Schema

Every artifact has this YAML frontmatter. Designed for three consumers: agents (machine-parseable), Obsidian (graph + Properties + Dataview), and standard YAML libraries (gray-matter).

```yaml
---
id: "SYS-CDM"
type: "system"
title: "CSG Data Manager"
domain: "cdm"
status: "draft"                    # draft | active | deprecated
last_verified: 2026-04-09         # unquoted ISO date — Obsidian date picker
freshness_note: "review when CDM's case model or auth middleware changes"
freshness_triggers:                # machine-checkable conditions
  - "cdm:src/models/study.py"
  - "cdm:src/services/case.py"
  - "cdm:src/middleware/auth.py"
known_unknowns:
  - "Unclear how image deduplication works across modalities"
tags:                              # Obsidian tag pane + graph filtering
  - cdm
  - system
aliases:                           # Obsidian quick switcher
  - "CDM"
  - "CSG Data Manager"
relates_to:                        # sorted alphabetically by target
  - type: "depends_on"
    target: "[[SYS-DAIP]]"        # quoted wikilink — valid YAML + Obsidian resolves
  - type: "feeds"
    target: "[[SYS-RDP]]"
  - type: "integrates_with"
    target: "[[SYS-CTL]]"
sources:                           # sorted alphabetically by ref
  - category: "implementation"
    type: "github"
    ref: "cdm:src/models/study.py"
  - category: "implementation"
    type: "github"
    ref: "cdm:src/services/case.py"
notes: ""
---
```

**Obsidian compatibility note:** Obsidian's graph view only draws edges from `[[wikilinks]]` in the note body, not from frontmatter. Reef uses a dual strategy: structured `relates_to` in frontmatter (for agents/Dataview) AND `[[wikilinks]]` in Key Facts, prose, and a `## Related` section (for graph view). Claude generates both; validation checks they stay in sync.

### Relationship Types


| Type              | Meaning                                              | Example                         |
| ----------------- | ---------------------------------------------------- | ------------------------------- |
| `parent`          | This artifact is a detail of a higher-level artifact | PROC-CDM-CASE → SYS-CDM         |
| `depends_on`      | This artifact assumes another artifact's content     | SCH-CDM-STUDY → SCH-CDM-IMAGE   |
| `refines`         | This artifact adds peer-level detail to another      | API-CDM-REST → SYS-CDM          |
| `constrains`      | This artifact governs/limits another                 | DEC-AUTH-PATTERN → API-CDM-AUTH |
| `supersedes`      | This artifact replaces a previous one                | DEC-NEW-AUTH → DEC-OLD-AUTH     |
| `feeds`           | This system sends data to another                    | SYS-CDM → SYS-RDP               |
| `integrates_with` | Bidirectional exchange between systems               | SYS-CDM ↔ SYS-CTL               |


### Key Facts Section

Every artifact (except Glossary) includes a Key Facts section — individually verifiable assertions linked to sources:

```markdown
## Key Facts
- CDM owns breast and chest radiology case management → `cdm:src/services/case.py`
- CDM does NOT own annotation workflows (that's CTL) → verified with CTL team
- Case status transitions are enforced at the service layer → `cdm:src/services/case.py:L45-89`
- Image deduplication uses perceptual hashing → `cdm:src/utils/dedup.py`
```

Each fact can be individually verified during lint. When a source file changes, only the facts referencing that file need re-verification — not the entire artifact.

### Source References

Every claim traces to a source file:

```yaml
sources:
  - category: "implementation"     # what kind of evidence
    type: "github"                 # where it lives
    ref: "cdm:src/models/study.py" # source_label:relative/path
```

Categories: `implementation`, `documentation`, `decision`, `data`, `reference`
Types: `github`, `openapi`, `confluence`, `db`, `pdf`, `jira`, `slack`, `other`

### Known Unknowns

Explicit gaps are first-class. If Claude can't verify something, it goes here — never omitted silently:

```yaml
known_unknowns:
  - "Authentication flow for service-to-service calls not found in code"
  - "Unclear if soft deletes are used for studies"
```

### Risk-Specific Fields (RISK- type only)

```yaml
severity: "medium"                 # high | medium | low
impact: "Auth bypass possible under race condition"
resolution_status: "open"          # open | in_progress | resolved | accepted
resolution_target: ""              # Jira ticket or project name
resolution_notes: ""
```

### Determinism Rules

To keep diffs clean and prevent spurious changes:

- `relates_to` arrays sorted alphabetically by target
- `sources` arrays sorted alphabetically by ref
- `freshness_triggers` sorted alphabetically
- Frontmatter field ordering: id, type, title, domain, status, last_verified, freshness_note, freshness_triggers, known_unknowns, relates_to, sources, notes (+ risk fields for RISK- type)
- Key Facts sorted by source label, then path

---

## 9. Validation & Lint (Product IP)

### Validation on Artifact Accept

Before writing to disk, Reef validates. **Block** on schema errors, **warn** on reference errors:

**Blocking (artifact not written):**

- YAML frontmatter present and parseable
- All required fields present for the artifact type
- `id` matches intended filename
- Valid enum values for type, status
- `freshness_note` is not empty
- Key Facts section present with at least one fact (except Glossary)

**Warning (user decides):**

- `relates_to` targets reference existing artifacts
- `sources` refs point to real files in indexed sources
- Required body sections present for the artifact type
- Risk-specific fields present (if RISK- type)
- `## Related` section present and consistent with frontmatter `relates_to`
- `tags` and `aliases` fields present (Obsidian compatibility)

### Health Check (Lint)

Two tiers. **Quick Health Check** runs mechanically (no API calls). **Deep Health Check** uses Claude (costs API tokens, user triggers explicitly).

**Quick Health Check (mechanical, 7 checks):**

1. **Orphan detection** — artifacts with no incoming `relates_to` references (SYS- excluded as roots)
2. **Dangling references** — `relates_to` targets that don't resolve to an existing artifact ID
3. **Source file existence** — `sources` entries pointing to files that no longer exist in the source index
4. **Frontmatter schema validation** — required fields, valid enums, id matches filename, dates parseable
5. **Key Facts without sources** — Key Facts that don't reference a source file
6. **Wikilink/frontmatter sync** — body `[[wikilinks]]` in `## Related` should match `relates_to` entries
7. **Freshness** — artifacts whose `last_verified` is older than last-modified of their source files (via `.reef/artifact-state/` snapshots)

**Deep Health Check (LLM-assisted, 3 checks):**
8. **Empty known_unknowns** — Claude reviews artifacts flagged as "suspiciously confident" and checks for genuine gaps
9. **Contradiction detection** — Claude reads pairs of artifacts sharing `relates_to` targets and checks for conflicting Key Facts
10. **Stale claims** — Claude re-reads source files referenced by Key Facts and checks if claims still hold

**Report format:** Categorized findings (errors / warnings / info), each with artifact ID, issue, and suggested fix. Results logged to `.reef/log.md`.

### Change Classification

When detecting source changes during health check or update:


| Classification | Meaning                        | Action                                         |
| -------------- | ------------------------------ | ---------------------------------------------- |
| `new`          | File appeared since last check | Flag artifacts in same directory/module        |
| `updated`      | Content hash changed           | Flag artifacts that reference this file        |
| `renamed`      | Path changed, content similar  | Update source refs in affected artifacts       |
| `deleted`      | File removed                   | Warn — artifacts referencing it may be invalid |
| `unchanged`    | No movement                    | Skip                                           |


Health check output is a structured report: "3 files updated (affects SYS-CDM, PROC-CDM-CASE-LIFECYCLE), 1 file deleted (CON-CDM-CTL-ANNOTATION may be invalid)."

### Source Snapshots

When an artifact is accepted, Reef captures the state of every source file Claude read:

```json
// .reef/artifact-state/SYS-CDM.json
{
  "artifact_id": "SYS-CDM",
  "written_at": "2026-04-09T14:30:00Z",
  "source_snapshot": [
    {
      "ref": "cdm:src/models/study.py",
      "hash": "sha256:a1b2c3...",
      "last_modified": "2026-04-08T10:00:00Z"
    },
    {
      "ref": "cdm:src/services/case.py",
      "hash": "sha256:d4e5f6...",
      "last_modified": "2026-04-07T15:00:00Z"
    }
  ],
  "freshness_status": "fresh",
  "last_checked": "2026-04-09T14:30:00Z",
  "stale_sources": []
}
```

### Wiki Evolution Log

`log.md` at wiki root — append-only, human-readable timeline:

```markdown
## 2026-04-09
- Added sources: cdm (342 files), ctl (218 files)
- Created SYS-CDM, SYS-CTL, SCH-CDM-STUDY-MODEL
- Flagged known unknown: CDM auth pattern unclear

## 2026-04-15
- Health check: 2 artifacts stale (auth refactor in cdm:src/middleware/)
- Updated SYS-CDM, regenerated PROC-CDM-AUTH
```

---

## 10. The System Prompt (Product IP)

The system prompt is assembled at runtime from four layers:

### Layer 1: Identity (~400 tokens)

- Role: knowledge architect for multi-system ecosystems
- **Personality: Curious Researcher.** Genuine curiosity about the codebase. "I noticed something interesting..." not "Based on my analysis..." Adapts to depth mode: conversational in Scuba, efficient in Snorkeling, thorough in Deep-diving. No emojis. No exclamation marks in findings.
- Tools: `read_file(source, path)`, `list_directory(source, path, depth)`, `search_files(source, pattern)`, `write_artifact(id, type, content)`
- Rules: never invent facts, populate known_unknowns, one artifact at a time, ask for corrections

### Layer 2: Artifact Contract (~2000 tokens)

- Complete frontmatter schema (8 types, 7 relationship types)
- Obsidian-compatible fields: `tags`, `aliases`, `[[wikilinks]]` in `relates_to` targets
- Naming conventions per type
- Required body sections per type (including Key Facts and `## Related`)
- SCH-/API- clarification: interpret the raw spec, don't restate it. Point to `sources/raw/`.
- Validation rules and determinism rules
- Registry file awareness (ask about org context)

### Layer 3: Discovery Methodology (~1000 tokens)

- **Surface pass first.** On every new source, start in Snorkeling mode automatically. Generate surface-level artifacts (SYS-, SCH-, API-, GLOSSARY-) rapidly with no questions. Priority order: SYS- first, then fill in based on what Claude finds.
- **Invite depth after surface pass.** Once surface artifacts are generated, pause and offer the user a choice: go deeper on a specific area, add another source, or explore cross-system connections. Don't ask questions during the surface pass.
- **Depth is progressive, not selected.** Snorkeling = automatic on new sources. Scuba = when user starts conversing. Deep-diving = when user gives a specific exhaustive directive. No mode picker UI.
- 33 baseline questions baked in as Claude's internal guide — used during Scuba/Deep-dive, NOT during surface pass.
- **Contract detection is always-on.** When Claude reads code that calls another system (webhooks, API clients, shared DB, message queues), flag the cross-system boundary immediately.
- Artifact type dependencies as soft constraints: if a PROC- is proposed before its parent SYS- exists, Claude notes it and suggests creating the SYS- first.
- During Scuba: "After each artifact, ask: What did I get wrong? What am I missing?"
- After surface pass, prompt user to add another source for cross-system discovery.
- **Suggest documentation sources when uncertain.** If Claude notices terminology ambiguity or shallow context after the surface pass, suggest the user drop in documentation (architecture docs, SRS, wiki exports). Read doc sources before code when both exist — docs provide the lens for interpreting code. After doc ingestion, offer to correct existing artifacts.
- During Scuba/Deep-dive: proactively ask about organizational context (team structure, ownership, RACI)

### Layer 4: Dynamic Context (variable)

- **Compact source summaries** per source: code sources ~200 tokens each (label, path, file count, annotated top-2-level directory structure), doc sources ~100 tokens each (label, file list with one-line descriptions). NOT full file trees.
- List of artifacts generated so far (IDs + titles + types)
- Registry files (if they exist)
- Current depth mode
- Injected fresh on every API call

### Token Budget

- Static layers: ~3,400 tokens
- Dynamic context: 800–2,000 tokens (reduced from 2,000-6,000 by using compact summaries instead of full file trees)
- Total system prompt: ~4,200–5,400 tokens per call
- Full file trees accessed on-demand via `list_directory` and `search_files` tools

---

## 11. Registry Files

Registry files live in `sources/registries/` and capture organizational knowledge that code can't provide. Claude proactively asks about these during discovery and helps the user create them.

### repos.yaml

```yaml
# Which repos exist, what they do, who owns them
repos:
  - name: cdm
    full_name: CSG Data Manager
    domain: csg
    team: data-curation
    description: Case/study/image curation for breast and chest radiology
  - name: ctl
    full_name: Closing The Loop
    domain: csg
    team: annotation
    description: Radiology annotation management
```

### org-chart.yaml

```yaml
# Team structure and ownership
teams:
  - name: data-curation
    lead: TBD
    systems: [cdm]
    domain: csg
  - name: annotation
    lead: TBD
    systems: [ctl]
    domain: csg
```

### raci.yaml (optional)

```yaml
# Decision-making context
decisions:
  - topic: "CDM schema changes"
    responsible: data-curation
    accountable: csg-lead
    consulted: [annotation, platform]
    informed: [analytics]
```

These are optional but valuable. Claude references them when generating artifacts to populate domain, ownership, and cross-team context.

---

## 12. Current State (as of 2026-04-09)

### What's Built (1,737 lines across 15 source files)


| Component             | Status              | Notes                                                                                                                                                                                                          |
| --------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Electron app scaffold | Done                | 520×740 compact panel, frameless, macOS vibrancy                                                                                                                                                               |
| Setup screen          | Done                | API key (encrypted), model picker                                                                                                                                                                              |
| Project home          | Done                | Drag-and-drop + file picker, source pills, project naming                                                                                                                                                      |
| Source indexer        | Done                | Multi-source, .gitignore respect, depth/size limits                                                                                                                                                            |
| Claude client         | Done                | Streaming, tool use (read_file, write_artifact), conversation state                                                                                                                                            |
| System prompt         | Done (needs update) | 4-layer assembly, multi-source context — needs Key Facts, `## Related`, 8 types, 7 relations, freshness fields, Obsidian-compatible output (tags/aliases/wikilinks), SCH/API clarification, registry awareness |
| Wiki manager          | Done (needs update) | Folder creation, artifact write, index generation — needs 3-zone structure, source snapshots, log.md, validation, `sources/raw/` for spec syncing                                                              |
| Chat panel            | Done                | Streaming display, artifact cards, source bar, status footer                                                                                                                                                   |
| Source bar            | Done                | Pills with colors, drag-and-drop, add/remove                                                                                                                                                                   |
| Artifact cards        | Done                | Accept/skip/preview inline in chat                                                                                                                                                                             |
| Preload bridge        | Done                | All 19 IPC methods exposed securely                                                                                                                                                                            |
| Dark theme CSS        | Done                | Compact layout, consistent design system                                                                                                                                                                       |


### What Needs Updating (from stress test Sections A-H)


| Item                                                                  | Priority | Effort | What Changed                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------- | -------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| types.ts — 8 artifact types                                           | High     | Small  | Add 'risk', add risk-specific fields                                                                                                                                                                                                                                                 |
| types.ts — 7 relationship types                                       | High     | Small  | Add 'constrains', 'supersedes', 'feeds', 'integrates_with'                                                                                                                                                                                                                           |
| types.ts — new frontmatter fields                                     | High     | Small  | Add freshness_note, freshness_triggers, tags, aliases                                                                                                                                                                                                                                |
| types.ts — ArtifactState type                                         | High     | Small  | New type for `.reef/artifact-state/`                                                                                                                                                                                                                                                 |
| types.ts — ChangeClassification                                       | High     | Small  | New enum for health check                                                                                                                                                                                                                                                            |
| types.ts — SourceEntry type field                                     | Medium   | Small  | Add `type: 'code'                                                                                                                                                                                                                                                                    |
| constants.ts — 8 types/prefixes/folders                               | High     | Small  | Add RISK prefix and risks/ folder                                                                                                                                                                                                                                                    |
| wiki-manager.ts — 3-zone init                                         | High     | Medium | Create sources/registries/, sources/raw/, .reef/artifact-state/, .reef/sessions/                                                                                                                                                                                                     |
| wiki-manager.ts — source snapshots                                    | High     | Medium | Capture hashes on acceptArtifact()                                                                                                                                                                                                                                                   |
| wiki-manager.ts — log.md                                              | High     | Small  | Append to log.md on artifact accept                                                                                                                                                                                                                                                  |
| wiki-manager.ts — source-artifact-map                                 | Medium   | Medium | Build reverse index on accept                                                                                                                                                                                                                                                        |
| wiki-manager.ts — index.md with wikilinks                             | Medium   | Small  | Generate index.md using `[[wikilinks]]` for Obsidian graph                                                                                                                                                                                                                           |
| artifact-linter.ts — new file                                         | High     | Medium | Validation on accept + health check + Related/frontmatter sync check                                                                                                                                                                                                                 |
| source-indexer.ts — content hashing + repo detection + system mapping | Medium   | Medium | Add SHA-256 hash per file. Detect `.git/` repos at depth 1-2 when user drops a parent folder. Auto-label from repo folder name. Store repo-to-system mapping in `project.json`.                                                                                                      |
| source-indexer.ts — doc source support                                | Medium   | Medium | Accept `type: 'docs'` sources. Skip `.gitignore` for doc sources. PDF text extraction via `pdf-parse`, HTML tag stripping. Store extracted text alongside originals in index.                                                                                                        |
| source-syncer.ts — new file                                           | Medium   | Medium | Detect OpenAPI/schema files, copy to sources/raw/, hash tracking                                                                                                                                                                                                                     |
| system-prompt.ts — full rewrite                                       | High     | Large  | 8 types, Key Facts, `## Related`, 7 relations, freshness fields, Obsidian output (tags/aliases/wikilinks), SCH/API clarification, 33 questions, registry awareness                                                                                                                   |
| preload/index.ts — new IPC methods                                    | Medium   | Small  | Health check, registry management, sync-sources, list_directory, search_files                                                                                                                                                                                                        |
| claude-client.ts — new tools                                          | High     | Medium | Add list_directory, search_files tools. Add offset/limit to read_file. Compact old tool results in history.                                                                                                                                                                          |
| claude-client.ts — context management                                 | High     | Medium | Compact tool results after use. Artifact snapshots replace conversation. Session boundary detection at ~70% context.                                                                                                                                                                 |
| system-prompt.ts — compact summaries                                  | High     | Medium | Replace full file trees with per-source directory summaries (~200 tokens each). Full trees via list_directory on demand.                                                                                                                                                             |
| system-prompt.ts — depth modes                                        | High     | Small  | Depth mode parameter changes discovery methodology layer. Snorkeling: batch, minimal questions. Scuba: conversational. Deep-diving: exhaustive.                                                                                                                                      |
| system-prompt.ts — personality                                        | Medium   | Small  | Curious Researcher personality in identity layer. Adapts tone to depth mode.                                                                                                                                                                                                         |
| system-prompt.ts — guided priorities                                  | High     | Small  | Replace 7 rigid phases with guided priority order. Contract detection always-on.                                                                                                                                                                                                     |
| SetupScreen.tsx — simplify                                            | Medium   | Small  | Remove model picker. Default Sonnet. Model changeable in settings later.                                                                                                                                                                                                             |
| ChatPanel.tsx — save-to-artifact                                      | Medium   | Medium | "Save" icon on Claude messages. On click: Claude infers relevant message range, highlights in chat, user adjusts, Claude synthesizes into artifact proposal. Thread-based, not single-message.                                                                                       |
| ArtifactRibbon.tsx — new component                                    | Medium   | Medium | Thin ribbon of artifact pills above chat. Grows as artifacts accepted. Color by type. Click to preview.                                                                                                                                                                              |
| SurfaceProgress.tsx — new component                                   | Medium   | Small  | Progress indicator during auto-snorkel pass ("Analyzing... 2/5 artifacts generated").                                                                                                                                                                                                |
| SessionSummary.tsx — new component                                    | Low      | Small  | Summary card: artifact counts by type (surface vs deep), source coverage, session time. "Open in Obsidian" + "Test Your Reef" buttons.                                                                                                                                               |
| Question Bank + Validate                                              | Medium   | Medium | User submits real questions (`.reef/questions.json`). "Validate" runs all against wiki — ✓/⚠/✗ per question with citations. Status footer: "7/12 answered." Unanswered questions guide Scuba discovery. Questions also feed into system prompt so Claude prioritizes relevant areas. |
| CoverageIndicator.tsx — new component                                 | Medium   | Small  | Monospace text block with Unicode block characters — no custom UI. Dual-layer bars per source (█ breadth, ▓ depth), depth labels, artifact counts by type, Key Facts + Known Unknowns. Rendered via react-markdown or `<pre>`. Copy-pasteable.                                       |
| "Open in Obsidian"                                                    | Medium   | Small  | Detect Obsidian install, use `obsidian://open?path={wiki}/index.md` URI scheme. Fall back to "Open in Finder".                                                                                                                                                                       |
| Reef Health indicator                                                 | Medium   | Small  | Auto-computed from source git commits vs artifact `last_verified`. Three states by fading: fresh/aging/stale. ✱ logo on project home + compact text in status footer. "Refresh" button triggers targeted update pass.                                                                |
| HealthReport.tsx — new component                                      | Medium   | Medium | Display lint results: errors/warnings/info, categorized by check type.                                                                                                                                                                                                               |
| global.css — ocean depth theme                                        | Medium   | Small  | Seven-blue palette (v2) + coral accent. CSS custom properties. Three font stacks (serif/sans/mono). Radial gradient for chat bg. Scrollbar styling. See `design-system.html`.                                                                                                        |


### What's NOT Built Yet


| Item                                   | Priority | Effort                                                                     |
| -------------------------------------- | -------- | -------------------------------------------------------------------------- |
| Markdown rendering in artifact preview | High     | Small — react-markdown already installed                                   |
| Conversation auto-save during chat     | High     | Small — wiring existing saveConversation call                              |
| Project resume (load existing project) | High     | Small — WikiManager.load exists, needs UI                                  |
| Error recovery for API failures        | High     | Medium — three failure modes with distinct UX (see Section 12a)            |
| "Update Wiki" trigger (Phase 3)        | Medium   | Medium — re-index, detect changes, prompt Claude                           |
| Sync Sources action                    | Medium   | Small — subtle refresh icon on source bar, syncs raw specs to sources/raw/ |
| Health Check button (Phase 4)          | Medium   | Medium — lint + report UI                                                  |
| Source folder validation on add        | Low      | Small — check folder exists and is readable                                |
| App icon and about screen              | Low      | Small — design + resources                                                 |
| electron-builder DMG config            | Low      | Small — config file                                                        |
| True token-by-token streaming          | Low      | Medium — streaming + tool use is complex                                   |


---

## 12a. Error Handling & Resilience

### API Failure Modes


| Failure                                   | Cause                                      | UX Response                                                                                                                                                                                                                              |
| ----------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Rate limit (429)**                      | Too many requests/minute                   | Auto-retry with exponential backoff. Show: "Claude is busy, retrying..." User doesn't need to do anything.                                                                                                                               |
| **Spending limit (402/payment_required)** | User's Anthropic account hit monthly cap   | Show: "Your Anthropic spending limit has been reached." + direct link to console.anthropic.com/settings/limits + instructions to increase it. Actionable, not scary.                                                                     |
| **Context window exceeded**               | Conversation too long for 200K token limit | Catch before it happens (~70% usage). Offer: "This session is getting long. Start a fresh session? Your wiki and all accepted artifacts are safe." If it happens unexpectedly: auto-start fresh session with wiki state carried forward. |
| **Network failure**                       | Connection dropped mid-stream              | Show: "Connection lost. Retrying..." Auto-retry 3x. If persistent: "Check your internet connection. Your conversation is saved — pick up where you left off."                                                                            |
| **Invalid API key (401)**                 | Wrong or revoked key                       | Show: "Your API key isn't working." + link to console.anthropic.com/settings/keys. Redirect to setup screen.                                                                                                                             |


### Session Continuity

- Conversation persisted to `.reef/conversation.json` after every message exchange.
- If Reef crashes, user closes abruptly, or comes back the next day — conversation loads and resumes. The Anthropic API is stateless; there's no "session" that expires on their end.
- The wiki (all accepted artifacts) is always on disk, independent of conversation state. Even if conversation.json is corrupted, the wiki is intact and Claude can see existing artifacts in the system prompt.
- If conversation history exceeds context limits: Reef starts a fresh session with the wiki state (artifact list + source summaries) carried forward. Previous conversation is archived to `.reef/sessions/`.

### Privacy Disclosure

First-run disclosure shown before API key entry (not buried in settings):

> **How Reef uses your data**
>
> Reef sends file contents from your source folders to Anthropic's Claude API for analysis. This is required for Reef to read and understand your code.
>
> - Files are processed under Anthropic's API data policy — **they are not used for model training**.
> - Your API key is stored locally on this device and never sent to seaof.ai or any other server.
> - No data leaves your machine except via the Anthropic API.
> - For enterprise use: Anthropic offers zero-retention API plans for business accounts.
>
> [Read Anthropic's data policy →]

### Path Resilience (moved/renamed repos and wiki folders)

Reef stores absolute paths for source repos and the wiki folder. Users move and rename things. Reef must handle this gracefully.

**Source repo moved/renamed:**

- On project load, validate that each `sources[].path` exists on disk.
- If missing: show source pill in error state (red, "⚠ not found") with a **Relocate** action.
- "Relocate" opens a file picker. User points to the new location. Reef updates `project.json` and re-indexes.
- The source label and all artifact refs (`cdm:src/...`) remain valid — only the absolute root path changes. The `source_label:relative_path` format decouples label from location.
- Claude tools (`read_file`, `list_directory`, `search_files`) check source availability before attempting reads. Clear error if source is missing: "Source [cdm] not found. Relocate it in the source bar."

**Wiki folder moved/renamed:**

- `WikiManager.load(folder)` self-heals: update `project.json.wikiFolder` to match the actual folder path being loaded from. The stale absolute path in JSON is silently corrected.
- All internal paths (artifact refs, source-artifact-map, artifact-state) are relative to wiki root — moving the folder is inherently safe.

**Wiki subdirectory renamed manually (e.g., `artifacts/systems/` → `artifacts/sys/`):**

- Not supported. Subdirectory names are managed by Reef (type → folder mapping in `constants.ts`).
- Old artifacts in renamed folders remain valid markdown but won't be found by `listArtifacts()`.
- Not worth fixing — document as "don't rename internal folders."

---

## 13. Build Plan

### Day 1 (Thu Apr 9) — Foundation ✅ DONE

- Scaffold Electron + Vite + React + TypeScript
- Multi-source types and constants
- Source indexer (multi-source, .gitignore, file tree formatting)
- Wiki manager (multi-source project config, artifact lifecycle)
- Claude client (streaming, tool use)
- System prompt (4-layer assembly, 7 discovery phases)
- Setup screen (API key, model)
- Project home (drag-and-drop, source pills)
- Chat panel (streaming, artifact cards, source bar)
- Compact window (520×740, frameless)
- Rename to Reef
- Stress test Section A (completed — major architectural refinements)

### Day 2 (Fri Apr 10) — Apply Stress Test + Complete the Loop

**Goal:** Apply all stress test learnings. End-to-end working product with real repos.

**Priority key:** P0 = blocks working demo, P1 = ships in MVP, P2 = post-ship / Day 3+

**Step 1: System prompt first (do this before anything else)**

- **P0** Rewrite system-prompt.ts: compact summaries, depth modes, guided priorities (not phases), curious researcher personality, contract detection always-on, 33 questions, registry awareness, 8 types, Key Facts, 7 relations, Obsidian output
- **P0** Test the system prompt manually against real repos (cdm, ctl) via Claude API or claude.ai before wiring into the app. Verify: surface pass generates valid SYS- artifacts with correct frontmatter, Key Facts, and `## Related` section. This is the highest-risk item — if the prompt is wrong, everything downstream fails.

**Step 2: Core architecture changes (after prompt is validated)**

- **P0** Update types.ts: 8 types, 7 relations, freshness fields, ArtifactState, ChangeClassification, DepthMode
- **P0** Update constants.ts: RISK prefix, risks/ folder, depth mode enum, v2 palette (seven blues + coral)
- **P0** Update wiki-manager.ts: 3-zone init, source snapshots, log.md
- **P0** Update claude-client.ts: add list_directory, search_files tools, offset/limit on read_file
- **P0** Update source-indexer.ts: compact directory summaries for system prompt
- **P1** Create artifact-linter.ts: validation on accept (blocking + warning)
- **P1** Path resilience: validate source paths on project load, error state on source pill ("⚠ not found · Relocate"), file picker to update path, self-heal wikiFolder on load
- **P1** Doc source support: `type: 'docs'` on SourceEntry, doc-aware indexing (no .gitignore), PDF text extraction via `pdf-parse`, HTML tag stripping, distinct pill style, system prompt distinguishes code vs doc summaries
- **P1** Update source-indexer.ts: content hashing
- **P1** Update wiki-manager.ts: source-artifact-map reverse index
- **P2** claude-client.ts: compact old tool results in history (context management)

**Step 3: UI + End-to-end testing**

- **P0** Add auto-snorkel: Claude starts surface pass immediately when source indexed (no questions, rapid artifact generation)
- **P0** Simplify SetupScreen: remove model picker, default Sonnet
- **P0** Auto-save conversation on every message
- **P0** Test with real codebases (cdm, ctl at minimum) — full loop: drop folder → snorkel → accept artifacts → verify wiki output
- **P0** System prompt tuning based on real results
- **P1** Add SurfaceProgress component (progress during snorkel pass)
- **P1** Add ArtifactRibbon component (accepted artifacts as pills)
- **P1** Update status footer: progress narrative ("3 systems · 1 contract")
- **P1** Integrate react-markdown in ArtifactCard preview

### Day 3 (Sat Apr 11) — Polish & Edge Cases

**Goal:** Product feels solid. Error states handled. UX polished. Ocean depth theme.

**P0 — must ship:**

- **P0** Ocean depth visual theme (v2 palette, typography metrics, spacing/radius/elevation — per design-system.html)
- **P0** Error handling: 429 rate limit (auto-retry + "Claude is busy"), 401 invalid key (redirect to setup), 402 spending limit (link to Anthropic console), network failure (auto-retry 3x)
- **P0** Tool call status in chat ("Snorkeling · reading cdm:src/models/study.py...")
- **P0** Context management: track cumulative input_tokens from API `usage` field, offer fresh session at ~140K tokens

**P1 — ships if time allows:**

- **P1** Health Check button + HealthReport component (Quick Health Check — 7 mechanical checks)
- **P1** "Open in Obsidian" button: detect Obsidian install, use `obsidian://open?path=` URI scheme, fall back to Finder
- **P1** Session summary card (SessionSummary component)
- **P1** Large repo handling (>300 files per source, 40KB file warning, chunked reads)
- **P1** Drag-and-drop feedback (visual highlight on source bar)
- **P1** Artifact-linter.ts: Quick Health Check (7 mechanical checks) — if not done on Day 2

**P2 — post-ship (v1.1 or later):**

- **P2** ✱ logo integration (favicon, title bar, health indicator, empty state watermark, app icon)
- **P2** "Save as artifact" icon on Claude messages (thread-based — complex UI interaction)
- **P2** Full screen mode (Cmd+F toggle): chat left panel + detail right panel
- **P2** CoverageIndicator: dual-layer source coverage bars, artifact counts by type
- **P2** Depth-weight visuals: deep artifacts get thicker border/glow in ribbon
- **P2** Question Bank + Validate Reef button
- **P2** Reef Health bitmap indicator
- **P2** Keyboard shortcuts (Cmd+N, Cmd+O, Cmd+W)

### Day 4 (Sun Apr 12) — Ship

**Goal:** Distributable macOS app. Tested on clean machine.

- App icon (reef/coral motif — simplified version, not bitmap character)
- About screen (version, "Built by seaof.ai")
- electron-builder config (macOS DMG)
- Build DMG: `npm run package`
- Test on clean macOS machine (full flow: setup → sources → chat → artifacts → wiki)
- README.md
- Ship

---

## 14. Post-MVP Roadmap

### v1.1 — Phase 2 & 3 (Expand + Maintain) + Pricing

- Automated artifact expansion: Claude proposes artifacts for unexplored files
- "Update Wiki" detects changed files and proposes updates to affected artifacts
- Dependency tracking via source-artifact-map
- Freshness indicators in UI (stale artifact badges)
- Deep Health Check (LLM-assisted: contradictions, stale claims, empty known_unknowns)

### v1.2 — Richer Discovery

- Pattern artifact type (emerges from cross-system synthesis)
- Process archetype detection (lifecycle vs. workflow vs. boundary)
- Better handling of non-code sources (Confluence exports, PDFs, design docs)
- Obsidian plugin for deeper integration (beyond native graph compatibility, which ships in MVP)

### v1.3 — Claude Code Plugin (distribution play)

- Extract core logic into standalone module: artifact contract, validator, wiki-manager, system prompt builder
- Package as Claude Code MCP server + slash commands:
  - `/reef-init` — create wiki folder structure + `.reef/` state
  - `/reef-discover` — run surface pass on current directory or specified folders
  - `/reef-health` — run 7 mechanical lint checks
- Ship a `CLAUDE.md` template that injects artifact contract + discovery methodology into any Claude Code session
- Validation logic as a Claude Code hook on artifact writes
- Publish to Claude Code marketplace
- **Same output format as Electron app** — wikis are interchangeable between app and plugin
- This reaches developers who won't download a separate app but already have Claude Code

### v1.4 — Tauri Migration

- Rewrite main process for Tauri (Rust backend or sidecar Node process)
- 10MB binary instead of 150MB
- Native macOS feel

### v2.0 — Output Layer + Collaboration

- Export to Confluence / Notion / GitBook / HTML (tool-agnostic)
- "Share via Git" action (init repo + push wiki to remote)
- Team features (shared API key pool, usage tracking)
- Headless `reef-cli` for CI/scheduled jobs (same core logic, no Electron shell)
- Landing page on seaof.ai

### v3.0 — Agent Autonomy + Downstream Specs

- Scheduled wiki updates (cron-based re-indexing and artifact refresh)
- CI/CD integration (update wiki on PR merge)
- Multi-agent: one agent per system, coordinator agent for contracts
- Query mode: ask questions against the wiki, Claude answers grounded in artifacts
- **Work zone:** Planning workspace where agents use the wiki to draft PRDs, SRDs, impact analyses, and implementation specs — grounded in structured knowledge, not hallucination
- **Spec → code loop:** Publish SRDs as markdown to GitHub. Agents read wiki + SRD + codebase to implement with full context. The closed loop: code → knowledge → specs → code

---

## 15. Success Criteria (MVP)

The MVP is successful if:

1. **First artifacts appear within 5 minutes of dropping a folder — with zero questions asked.**
  - Surface pass auto-generates 3-6 artifacts (SYS-, SCH-, API-, GLOSSARY-) from a single source.
  - Artifacts have valid frontmatter, Key Facts with source refs, honest known_unknowns, and freshness notes.
  - After 30 minutes of Scuba/Deep-dive, the wiki has 8-12+ artifacts with organizational depth.
2. **The wiki is useful without Reef — and beautiful in Obsidian.**
  - Output is plain markdown. Readable in Obsidian, VS Code, GitHub, or any editor.
  - index.md serves as a navigable entry point with `[[wikilinks]]`.
  - `[[wikilinks]]` in Key Facts, prose, and `## Related` create a connected graph in Obsidian.
  - `tags` and `aliases` enable Obsidian filtering and quick switcher.
  - Frontmatter `relates_to` with typed relationships enables Dataview queries.
3. **The experience feels like collaborative discovery, not document generation.**
  - Three depth modes work as expected: Snorkeling produces batch artifacts, Scuba feels conversational, Deep-diving produces exhaustive references.
  - Claude's curious researcher personality makes the session engaging, not transactional.
  - The user feels like they're teaching Claude about their systems.
  - Artifacts improve when the user corrects Claude.
  - Progressive disclosure — conversation, not questionnaire.
  - Artifact ribbon provides visible accumulation. Session summary card creates a "pride moment."
4. **Cross-system contracts are the "aha" moment.**
  - After documenting 2+ systems, Claude identifies boundaries and proposes CON- artifacts.
  - These artifacts surface things the user knew implicitly but never documented.
5. **Validation catches errors before they hit disk.**
  - Frontmatter schema errors are blocked.
  - Dangling references are warned.
  - Source snapshots are captured for every accepted artifact.
6. **The wiki can be maintained, not just created.**
  - Health Check identifies stale artifacts, orphans, and broken refs.
  - log.md provides a readable timeline of the wiki's evolution.
  - The path from Phase 1 (manual) to Phase 3 (automated maintenance) is clear.

---

## 16. Risks


| Risk                                                                                   | Likelihood | Impact | Mitigation                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| System prompt too long for large multi-repo setups                                     | Low        | High   | Compact summaries (~200 tokens/source) instead of full trees. list_directory + search_files for on-demand access. Total prompt: ~4,200-5,400 tokens.                                                               |
| Claude generates low-quality artifacts without enough source context                   | Medium     | High   | Discovery flow forces Claude to read files before generating; known_unknowns + Key Facts capture gaps; validation on accept                                                                                        |
| Tool use loop gets stuck (Claude keeps calling read_file without generating artifacts) | Low        | Medium | Add max tool calls per turn; system prompt instructs "work one artifact at a time"                                                                                                                                 |
| Electron binary size deters users                                                      | Medium     | Low    | Tauri migration in v1.3; for MVP, target users care about output quality not binary size                                                                                                                           |
| API costs surprise users (BYOK model)                                                  | Medium     | Medium | Actionable error messages for rate limits (auto-retry) and spending limits (link to Anthropic console). Default to Sonnet (cheaper). No cost display — unreliable estimates create more anxiety than they resolve. |
| Artifact schema too complex for new users (8 types, 7 relations)                       | Medium     | Medium | Progressive disclosure in discovery — Claude introduces types gradually, not all at once. Key Facts and frontmatter are Claude's job, not the user's.                                                              |
| Validation too strict blocks useful artifacts                                          | Low        | Medium | Block only on schema errors; warn on reference issues. User always has the final say.                                                                                                                              |
| Scope creep from stress test delays shipping                                           | High       | High   | Stress test informs architecture but implementation is incremental. Day 2: core changes + working loop. Day 3: polish + theme. Day 4: ship. Lint, save-as-artifact, expand mode are Day 3 items.                   |
| Context window exhaustion in long sessions                                             | Medium     | Medium | Compact tool results after use. Track cumulative input tokens via `usage` field from Claude API responses — when input_tokens exceeds ~140K, offer fresh session. Never silently truncate.                         |
| Depth modes add complexity                                                             | Medium     | Medium | Snorkeling and Scuba are the same flow with different system prompt parameters. Deep-diving is user-directed (no special UI). Low implementation cost.                                                             |


---

## 17. What Changed (Stress Test Decisions — All Sections)

Summary of architectural decisions made during the stress test that changed the original plan:


| Decision                  | Before                                               | After                                                                             | Why                                                                                                                                                                                                                                                                   |
| ------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Artifact types            | 7 (no Risk)                                          | 8 (added Risk)                                                                    | PMs need a `risks/` folder answering "what should I be worried about?"                                                                                                                                                                                                |
| Relationship types        | 3 (parent, depends_on, refines)                      | 7 (+ constrains, supersedes, feeds, integrates_with)                              | System architecture semantics matter for PMs understanding data flow                                                                                                                                                                                                  |
| Wiki zones                | 2 (artifacts + .reef/)                               | 3 (artifacts + sources + .reef/)                                                  | Registry files and raw evidence need a home                                                                                                                                                                                                                           |
| Frontmatter               | Basic                                                | + freshness_note, freshness_triggers                                              | Every artifact needs human-readable freshness guidance and machine-checkable triggers                                                                                                                                                                                 |
| Artifact body             | Prose only                                           | + Key Facts section                                                               | Individually verifiable assertions linked to sources, enabling per-fact lint                                                                                                                                                                                          |
| State layer               | project.json + source-index.json + conversation.json | + artifact-state/, source-artifact-map.json, sessions/                            | Source snapshots at write time enable freshness detection; reverse index powers lint                                                                                                                                                                                  |
| Wiki log                  | None                                                 | log.md (append-only)                                                              | Curated timeline of wiki evolution, not raw chat history                                                                                                                                                                                                              |
| Validation                | None                                                 | Blocking (schema) + Warning (refs) on accept                                      | Catches errors before they hit disk                                                                                                                                                                                                                                   |
| Lifecycle model           | Manual only                                          | 4-phase: Bootstrap → Expand → Maintain → Lint                                     | Hand-building is only viable for Phase 1. Automation is core product, not nice-to-have.                                                                                                                                                                               |
| Framing                   | "Hand-built library"                                 | "Well-crafted library: human-guided foundation, increasingly automated"           | CSG experience proves manual maintenance doesn't scale past ~50 artifacts                                                                                                                                                                                             |
| vs. Onco-PE               | Dismissed as "different approach"                    | Adopted state management discipline, change classification, determinism rules     | Engineering rigor in state tracking is universal, regardless of pipeline vs. conversation                                                                                                                                                                             |
| vs. Karpathy              | Missing lint                                         | Health Check feature with full change classification                              | lint/health-check is a core operation, not optional                                                                                                                                                                                                                   |
| Discovery delivery        | ~18 questions shown to user                          | 33 questions as Claude's internal guide, progressive disclosure                   | Conversation, not questionnaire. Seed questions per phase, reactive follow-ups.                                                                                                                                                                                       |
| Registry files            | Not planned                                          | MVP in sources/registries/                                                        | Captures organizational knowledge code can't provide. Critical differentiator.                                                                                                                                                                                        |
| Obsidian compatibility    | v1.2 roadmap item                                    | MVP — native graph works out of the box                                           | `[[wikilinks]]` in body + `## Related` section + `tags`/`aliases` in frontmatter. Dual strategy: frontmatter for machines, body links for graph.                                                                                                                      |
| SCH-/API- artifact intent | "Document the schema/API"                            | "Interpret the raw spec — don't restate it"                                       | Raw specs live in `sources/raw/`. Artifacts add context, business rules, usage patterns.                                                                                                                                                                              |
| Sync Sources              | Not planned                                          | MVP — subtle refresh icon, copies raw specs to sources/raw/                       | Keeps OpenAPI and ERD snapshots current. Separate from Health Check (quick + non-destructive).                                                                                                                                                                        |
| `## Related` section      | Not in artifacts                                     | Required in every artifact (except Glossary)                                      | Obsidian graph only sees body `[[wikilinks]]`, not frontmatter. Duplicates `relates_to` intentionally. Validation checks sync.                                                                                                                                        |
| Source freshness strategy | Not defined                                          | Git diffs for code, content hashes for non-git, confluence_version for Confluence | Different strategies for different source types. Git diffs are more informative (what changed, not just that it changed).                                                                                                                                             |
| Discovery approach        | Question-driven only                                 | Progressive depth: auto-snorkel first, then user-initiated Scuba/Deep-dive        | Surface pass is automatic on every new source — zero questions, artifacts in under 5 minutes. Depth unlocks naturally when user engages. No mode picker.                                                                                                              |
| Activation design         | 10 steps, user chooses mode                          | 3 steps to first artifact, depth is a progression                                 | Drop folder → auto-snorkel → accept/skip artifacts. User sees value before they invest effort. Scuba/Deep-dive come after the "aha moment", not before.                                                                                                               |
| Discovery phases          | 7 rigid phases in sequence                           | Guided priorities, any type any time                                              | Phases were too rigid — discovery isn't linear. Priority order (SYS- first) but no gates.                                                                                                                                                                             |
| Contract detection        | Phase 7 only                                         | Always-on during any discovery                                                    | Contracts should be proposed when Claude spots cross-system calls, not held until end.                                                                                                                                                                                |
| File tree in prompt       | Full tree for all sources                            | Compact summaries + on-demand tools                                               | Full trees waste 3,000-15,000 tokens. Summaries (~200 tokens/source) + list_directory + search_files tools.                                                                                                                                                           |
| Claude tools              | read_file, write_artifact                            | + list_directory, search_files. read_file gains offset/limit.                     | Lazy-loaded navigation. Claude browses on demand, doesn't memorize 1,200 paths.                                                                                                                                                                                       |
| Path validation           | None                                                 | Validate against source index, fuzzy match on 404                                 | Every read_file checks index. Returns 5 closest matches on miss.                                                                                                                                                                                                      |
| Chat answer retention     | Lost in conversation                                 | "Save as artifact" from conversation threads                                      | Artifacts come from threads, not single messages. Claude auto-selects relevant message range, user adjusts, Claude synthesizes. Closes Karpathy's "file good answers back" gap.                                                                                       |
| Context management        | Unlimited growth                                     | Compact tool results, session boundaries at ~70%                                  | Tool results compressed after use. Session break offered when context gets full.                                                                                                                                                                                      |
| Personality               | Generic assistant                                    | Curious Researcher                                                                | Genuine curiosity, conversational, adapts to depth mode. Not dry (Calm Architect) or cloying (Enthusiastic Intern).                                                                                                                                                   |
| Window behavior           | Fixed 520×740                                        | Two modes: compact (520×740) + full screen (Cmd+F)                                | Compact for conversation. Full screen for review: coverage bars, question bank, artifact preview, reef health. No in-between. Status footer bridges the two.                                                                                                          |
| Visual identity           | Generic dark theme                                   | Seven-blue palette + ✱ logo + design system                                       | Seven blues, one coral. ✱ (Heavy Asterisk) as logo. Health by fading, not color. Typography with tight headlines + negative tracking. Full spec in `design-system.html`.                                                                                              |
| Accumulation feel         | Status bar count only                                | Artifact ribbon + progress narrative                                              | Ribbon shows accepted artifacts growing. Status footer tells a story ("3 systems · 2 contracts · 1 risk").                                                                                                                                                            |
| Pride moment              | None                                                 | Three-part: coverage, creation, validation                                        | 1) Coverage bars show exploration breadth+depth. 2) Session summary + Obsidian graph show what was created. 3) Question Bank — user's real questions as north star. "7/12 answered" is the most meaningful progress metric. Gaps steer discovery.                     |
| Activation flow           | 10 steps, model picker                               | 7 steps, no model picker, auto-start                                              | Model defaults to Sonnet. Discovery starts automatically on first source indexed. No "Start" button.                                                                                                                                                                  |
| Health Check              | Unspecified                                          | 7 mechanical + 3 LLM-assisted checks                                              | Quick (free, instant) and Deep (API cost, thorough) tiers. Report with errors/warnings/info.                                                                                                                                                                          |
| Product identity          | Unclear                                              | Product (not tool, not methodology)                                               | Methodology is open (credibility). Product is closed (captures value). Direct download from seaof.ai.                                                                                                                                                                 |
| Target persona            | Generic PMs/TPMs                                     | Platform team PM managing 5+ services                                             | Recurring need, highest pain, multi-source is killer feature, has budget authority.                                                                                                                                                                                   |
| Pricing model             | BYOK only                                            | BYOK permanently (employment constraint — no monetization for now)                | Free product, BYOK only. No cost display (unreliable, creates anxiety). Subscription deferred indefinitely.                                                                                                                                                           |
| Error handling            | Not specified                                        | Three distinct failure modes with actionable UX                                   | Rate limit (auto-retry), spending limit (link to Anthropic console), context exceeded (fresh session with wiki carried forward).                                                                                                                                      |
| Session continuity        | Assumed                                              | Explicit resume mechanism                                                         | conversation.json persists after every exchange. User can close, come back next day, resume. Wiki always safe on disk.                                                                                                                                                |
| Privacy                   | Not addressed                                        | First-run disclosure before API key entry                                         | Clear about what goes to Anthropic API. Link to data policy. Note about zero-retention enterprise plans.                                                                                                                                                              |
| Local-first               | V1 constraint                                        | Permanent principle                                                               | Privacy is a prerequisite, not a feature. Sharing via git. Headless CLI possible in v2.                                                                                                                                                                               |
| Micro-interactions        | Not planned                                          | Artifact ribbon animation, tool call status, gap-as-progress                      | MVP: ribbon pulse on accept, "Reading cdm:..." status, amber highlight for known unknowns.                                                                                                                                                                            |
| Progress visibility       | None                                                 | Dual-layer coverage indicator (breadth + depth)                                   | Per-source bars: light = files seen, dark = files deeply explored. Depth labels (shallow/moderate/deep). Artifact counts by type, Key Facts, Known Unknowns. User knows where to invest next.                                                                         |
| Open in Obsidian          | "Open in Finder"                                     | Direct `obsidian://` URI scheme launch                                            | One click to see the knowledge graph. Falls back to Finder if Obsidian not installed.                                                                                                                                                                                 |
| Depth-weight visuals      | All artifacts look the same                          | Deep artifacts visually weightier                                                 | Thicker border/glow in ribbon, session summary distinguishes surface vs deep, more Key Facts visible on card.                                                                                                                                                         |
| Source model              | Flat (one folder = one source)                       | Smart repo detection + natural language system mapping                            | Drop parent → detect `.git/` repos inside. Claude asks "Which repos belong together?" in plain language before surface pass. Skip = each repo separate. Editable later. Claude suggests merges when it finds connections in code.                                     |
| Documentation sources     | Not supported                                        | Doc sources (`type: 'docs'`) alongside code sources                               | Docs dramatically improve terminology accuracy and code comprehension. Claude suggests after surface pass when uncertain. PDF/HTML parsed on ingest. Not mandatory — but when provided, Claude reads docs before code for context. Distinct pill style in source bar. |


