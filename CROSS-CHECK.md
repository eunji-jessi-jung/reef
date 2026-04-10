# PLAN.md vs PLUGIN-PLAN.md — Cross-Check & Gap Analysis

## Summary

PLUGIN-PLAN.md successfully inherited the **core architecture and methodology** from PLAN.md. However, several sections from the original plan are missing or underspecified. This document identifies the gaps and recommends which ones to add to PLUGIN-PLAN.md.

---

## What PLUGIN-PLAN.md Got Right

These PLAN.md elements are fully represented:

- 8 artifact types (Pattern deferred to v2) with all required sections
- 7 relationship types with semantics
- 3-zone wiki structure (artifacts/ + sources/ + .reef/)
- Onco-PE state management (source snapshots, artifact-state/, source-artifact-map, log.md, sessions/)
- Freshness tracking (freshness_note + freshness_triggers)
- Change classification vocabulary (new/updated/renamed/deleted/unchanged)
- Validation on accept (blocking + warning, 8-point checklist)
- Health check (7 mechanical + 3 LLM-assisted checks)
- Key Facts as claims-lite (each fact linked to source, individually lintable)
- Obsidian dual strategy (frontmatter relates_to + body [[wikilinks]])
- Curious Researcher personality (no emojis, no exclamation marks, adapts to depth mode)
- Guided priorities, not rigid phases
- Question Bank (.reef/questions.json) with gap-to-action loop
- 4-phase lifecycle (Bootstrap → Expand → Maintain → Lint)
- Registry files in sources/registries/
- Local-first principle
- Compact source summaries (~200 tokens/source)
- Determinism rules (sorted arrays, stable field ordering)
- Contract detection always-on
- SCH-/API- as interpretation, not spec restatement
- 33-question discovery template adapted for generic use
- Frontmatter field ordering specification
- All generic adaptations (domain free-form, owner optional, sources repo-relative, etc.)

---

## Gaps: Missing from PLUGIN-PLAN.md

### Gap 1: Who It's For (PLAN.md Section 2) — ADD

PLAN.md defines the target persona: **"Platform team PM managing 5+ services."** Recurring need, highest pain, multi-source is killer feature, has budget authority.

PLUGIN-PLAN.md has no target persona. This matters for skill design — the README, the questions we ask during init, and the depth of registry file prompts all depend on knowing who we're building for.

**Recommendation:** Add a short "Who It's For" section to PLUGIN-PLAN.md.

### Gap 2: Success Criteria (PLAN.md Section 15) — ADD

PLAN.md has 6 concrete success criteria:
1. First artifacts in 5 min, zero questions
2. Wiki useful without Reef, beautiful in Obsidian
3. Experience feels like collaborative discovery
4. Cross-system contracts are the "aha" moment
5. Validation catches errors before disk
6. Wiki can be maintained, not just created

PLUGIN-PLAN.md has no success criteria. The verification section tests functionality but doesn't define what "good" looks like.

**Recommendation:** Add plugin-adapted success criteria. Most translate directly — just remove Electron-specific items (artifact ribbon, session summary card).

### Gap 3: Risks (PLAN.md Section 16) — ADD

PLAN.md has 10 risks with likelihood/impact/mitigation. PLUGIN-PLAN.md has none.

Plugin-specific risks differ from Electron risks (no binary size concern, no API cost concern for Max users), but new risks exist:
- SKILL.md context size limits (skills can't be infinitely long)
- Plugin discovery/installation friction
- Claude Code version compatibility
- User confusion between 7 skills (too many entry points?)
- Skill execution quality varies with model (Sonnet vs Opus)

**Recommendation:** Add a plugin-specific risk table.

### Gap 4: UX Language Guidelines (PLAN.md Section 5a) — ADD

PLAN.md has a clear principle: **reef metaphor for status, plain language for CTAs.** Examples:
- Status: "Your reef is aging" (not "3 artifacts are stale")
- CTAs: "Run /reef-health" (not "Check the reef's health")
- The metaphor adds warmth and personality, never friction

This directly shapes how skills narrate progress and report results.

**Recommendation:** Add to `references/methodology.md` specification in PLUGIN-PLAN.md, or as a separate section.

### Gap 5: Post-MVP Roadmap (PLAN.md Section 14) — ADD

PLAN.md has a detailed roadmap: v1.1 (Expand+Maintain), v1.2 (richer discovery), v1.3 (Claude Code plugin — now v1.0!), v1.4 (Tauri), v2.0 (output layer + collaboration), v3.0 (agent autonomy + spec-code loop).

PLUGIN-PLAN.md has "Not in Scope" but no forward roadmap. Key items worth preserving:
- Reef Desktop (Electron reads wiki output) — v2
- Output layer (Confluence/Notion/GitBook) — v2
- Pattern artifact type — v2
- Automated expansion mode — after bootstrap proves out
- Multi-agent (one per system, coordinator for contracts) — v3
- **Work zone + Spec-code loop** — v3 (this is the long-term vision)

**Recommendation:** Expand "Not in Scope" into a proper roadmap section.

---

## Smaller Refinements

### Gap 6: Doc Source Support (PLAN.md Section 6) — CONSIDER

PLAN.md has detailed doc source handling: `type: 'docs'`, PDF text extraction, HTML tag stripping, distinct pill style, "Claude suggests after surface pass when uncertain." Doc sources improve terminology accuracy and code comprehension.

PLUGIN-PLAN.md doesn't mention doc sources at all. In Claude Code, the user could manually provide docs, but the structured support (suggesting docs, reading docs before code) is lost.

**Recommendation:** Add doc source awareness to reef-init and reef-scuba skills. During init, ask if user has architecture docs, SRS, wiki exports. During scuba, suggest adding docs when Claude notices terminology ambiguity. No PDF parsing needed (Claude Code can read PDFs natively).

### Gap 7: Registry File Examples (PLAN.md Section 11) — ADD

PLAN.md has concrete YAML examples for repos.yaml, org-chart.yaml, and raci.yaml. PLUGIN-PLAN.md mentions registry files but doesn't show the structure.

**Recommendation:** Add registry file examples to the reef-init skill specification or to references/methodology.md.

### Gap 8: Privacy Disclosure (PLAN.md Section 12a) — CONSIDER

PLAN.md has a first-run privacy disclosure: what data goes to Anthropic, API key handling, zero-retention for enterprise.

For the Claude Code plugin, the user already consented to Claude Code's terms. But the README should note that Reef skills read source code files during analysis.

**Recommendation:** Add a brief privacy note to README specification. Not a blocking gap.

---

## Correctly Skipped (Not Needed in Plugin)

| PLAN.md Section | Why It's Skipped |
|----------------|-----------------|
| Section 5b: Visual Design System | Electron UI only (palette, typography, spacing, elevation). Brand elements belong to seaof.ai / Reef Desktop. |
| Section 6: Architecture | Electron architecture (IPC, preload, renderer). Plugin has no custom architecture. |
| Section 7: Tech Stack | Electron + React + electron-vite. Not applicable. |
| Section 12: Current State | Status table of Electron components. Not applicable. |
| Section 12a: Error Handling | API failures (429, 402, context window) handled by Claude Code natively. |
| Section 13: Build Plan | Replaced by PLUGIN-PLAN.md's 5-phase implementation plan. |

---

## Action Plan

Update PLUGIN-PLAN.md with the following additions:

| # | What to Add | Source | Priority |
|---|------------|--------|----------|
| 1 | "Who It's For" section | PLAN.md Section 2 | High |
| 2 | "Success Criteria" section | PLAN.md Section 15, adapted | High |
| 3 | "Risks" section | New, plugin-specific | High |
| 4 | UX Language Guidelines in methodology.md spec | PLAN.md Section 5a | High |
| 5 | Expand "Not in Scope" into Roadmap | PLAN.md Section 14 | Medium |
| 6 | Doc source awareness in skill specs | PLAN.md Section 6 | Medium |
| 7 | Registry file YAML examples | PLAN.md Section 11 | Medium |
| 8 | Privacy note in README spec | PLAN.md Section 12a | Low |
