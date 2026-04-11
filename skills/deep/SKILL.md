---
description: "Exhaustive line-by-line tracing of specific areas"
---

# /reef:deep

Maximum depth on a specific area. Exhaustive line-by-line tracing for critical systems where shallow reading misses the real behavior.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher at maximum depth. Methodical, precise. Present-participle narration — "Reading through the 14 handler functions in order_router.py..." No emojis. No exclamation marks.

Emphasis on what the code actually does versus what it appears to do: "The docstring says idempotent, but the implementation at L78 increments a counter on every call."

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Check readiness

Deep assumes scuba-level artifacts already exist. Check before proceeding:

- Read `.reef/project.json` to understand scope and source roots.
- Check if `.reef/scuba-manifest.json` exists. If it does not, the reef has not been through scuba yet — stop and tell the user:
  ```
  This reef hasn't been through scuba yet. Deep builds on scuba-level
  artifacts (SYS-, SCH-, API-, PROC-, CON-) — without them, a deep dive
  would be starting from too shallow a foundation.

  Run /reef:scuba first, then come back to /reef:deep for the areas
  that need line-by-line tracing.
  ```
- If the manifest exists, check its completion status. If fewer than half the planned artifacts are complete, warn:
  ```
  Scuba is only partially complete (N/M artifacts). Consider finishing
  scuba first — or if you want to deep-dive a specific area that already
  has scuba coverage, tell me the target.
  ```
  If the user insists on proceeding despite the warning, allow it — they may have a good reason.
- Scan `artifacts/` for existing artifacts — read their frontmatter to understand current coverage and what relates to the dive target.

### 3. User directs the dive

The user specifies the target: a system, subsystem, module, or flow.

Examples:
- "Deep dive into the order processing service"
- "Trace the data upload flow end to end"
- "Everything in src/services/billing/"

If the user is vague, ask for a specific entry point — a directory, file, or concept. Do not guess.

### 4. Exhaustive reading

This is not snorkel. Read deeply. Trace paths. Check edge cases.

- **Read entire directories** relevant to the target. Do not sample — read all files.
- **Trace execution paths.** Follow function calls, imports, middleware chains, decorators, and signal handlers from entry point to final effect.
- **Map every function** that materially affects runtime behavior in the target area.
- **Read config files** — environment setup, dependency injection, feature flags, constants.
- **Check test files** for behavioral documentation. Tests often reveal edge cases and intended behavior that source code does not make obvious.
- **Read error handling paths.** What happens when things fail is often more important than the happy path.

### 5. Dense artifact generation

Deep dives produce dense artifacts. The standard is higher here:

- **5+ Key Facts per artifact minimum.** This is the deep dive bar. If an artifact has fewer than 5, keep reading — there is more to find.
- **Precise line citations required.** Use `src/services/order.py:L45-89`, not just `src/services/order.py`. Every Key Fact must cite specific lines.
- **Each Key Fact should capture behavior that is not obvious from a casual read.** If someone could learn it from a 30-second skim, it does not belong in a deep dive artifact.
- **`known_unknowns` should flag things that require running the code or checking infrastructure to verify.** Runtime behavior, environment-specific config, race conditions, actual error rates.

### 6. Collaborative domain framing

The deep dive is collaborative. The user provides context that reshapes how Claude interprets the code:

- "That retry logic was added after the March incident" — becomes a DEC- artifact or enriches a PROC-.
- "The dedup logic is supposed to work but we are not confident it does" — becomes a RISK- artifact.
- "This module is owned by the platform team, not us" — updates ownership context on existing SYS- artifacts.

When the user provides context, integrate it immediately. Do not wait for a batch update.

### 7. Cross-referencing

As the deep dive proceeds:

- Update `relates_to` on existing artifacts that connect to new findings.
- Flag contradictions between deep findings and existing draft artifacts. Be specific: "SYS-INGEST says the order service is stateless, but the deep dive shows session state stored in L34-41 of order_handler.py."
- Propose CON- artifacts when cross-system interactions are discovered.

### 8. Artifact creation

When creating or updating an artifact, follow the full artifact contract.

**Read `references/artifact-contract.md`** for frontmatter field order, body requirements, determinism rules, and validation checks. All rules apply here.

Status may be "active" if confidence is high from deep reading. Use "draft" when the code was ambiguous or the user flagged uncertainty.

### 9. Post-write commands

Run these in order after each artifact file is written and accepted:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in the log message when updating an existing artifact.

## Key Rules

- This is not snorkel. Read deeply. Trace paths. Check edge cases.
- 5+ Key Facts per artifact is the minimum bar.
- Line citations are required — not just file citations.
- Do not summarize — explain the actual behavior.
- If a function is critical, describe what it does, not just that it exists.
- Never invent facts. If uncertain, add to `known_unknowns`.
- Flag contradictions with existing artifacts explicitly.
