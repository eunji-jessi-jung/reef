---
description: "Auto-discover 3-6 draft artifacts from source code"
---

# reef:snorkel

Question-guided auto-discovery. Reads source code, uses the discovery question bank for direction, and produces 3-6 draft artifacts per source. No user input needed.

The key difference from a blind scan: snorkel reads the question bank and uses it to decide what to look at, what to document, and what to flag as unknown. Questions are the steering mechanism.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for project name and source paths. If no sources: "No sources configured. Run `/reef:init` to add source paths."
3. **Read `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`** — the rulebook. Every artifact must conform exactly.
4. **Read `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`** — voice and personality.
5. **Read `.reef/questions.json`** — the discovery questions. These steer what you investigate and document.
6. **Read existing artifacts** in `artifacts/` to avoid duplicates.

---

## Step 1 — Refresh the source index

Report: "Refreshing the source index..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

Report results in natural language.

---

## Step 2 — Question-guided structural scan

For each source in project.json:

1. Read the 2-level directory tree.
2. Read README.md if present.
3. Identify entry points, routers/handlers, models/schemas, config, tests, API definitions.
4. Note the tech stack.
5. Flag cross-system boundaries (imports, HTTP clients, shared schemas).

**Now use the question bank to go deeper.** For each question tagged to this source (or untagged):

- **Orientation questions** (boundaries, dependencies): Read entry points, config, dependency files. Trace imports to external services. Identify databases, queues, auth providers.
- **Data questions** (entities, relationships, state machines): Read model files thoroughly. Map entity names, relationships, field types. Look for status/state fields that indicate lifecycles.
- **Behavior questions** (workflows, error handling): Read router/handler files. Trace the main request paths. Note middleware, decorators, and error handlers.
- **Cross-system questions**: Search for HTTP clients, message publishers/consumers, shared schema imports. Map which source calls which.

For each question you can answer from code, note:
- **Fact**: what you found
- **Source**: which files (relative paths)
- **Confidence**: high (directly visible in code) / medium (inferred from structure) / low (guessing)
- **Open questions**: what you cannot determine from a surface read

Report progress as you go: "Reading service-a's model layer — found 14 SQLAlchemy models across 6 files...", "Tracing the auth middleware — JWT validation with role-based access control...", "Found HTTP client for service-b in clients/service_b.py — flagging as cross-system boundary..."

---

## Step 3 — Generate artifacts

Generate artifacts guided by what you learned. For each source, produce:

1. **SYS-** first — always. This is the entry point artifact. Use orientation question findings to write a rich overview with real boundaries, dependencies, and tech stack details.
2. **SCH-** for major data models — use data question findings. Name actual entities, describe relationships, note lifecycle states.
3. **API-** for API surfaces — use behavior question findings. Group endpoints, note auth patterns, describe key request flows.
4. **GLOSSARY-** if domain terms emerged that need definition.
5. **CON-** for cross-system boundaries — use cross-system question findings. Name both parties, describe what flows between them, cite the client/server code.

**Target: 3-6 artifacts per source.** For a 4-source reef, that means 12-24 artifacts total. Adjust based on codebase complexity — a simple service might only warrant 2-3, a complex one might need 6.

### For each artifact

**a. Read the template** from `/Users/jessi/Projects/seaof-ai/reef/references/templates/` for the artifact type.

**b. Generate frontmatter** following the artifact contract exactly. All fields in correct order:

- `id`: uppercase prefix + uppercase name (e.g., `SYS-INGEST`, `SCH-INGEST-ORDER`)
- `type`: matches the prefix
- `title`: human-readable name
- `domain`: source name or domain label
- `status`: always `"draft"` for snorkel
- `last_verified`: today's date, unquoted ISO format
- `freshness_note`: honest about scan depth
- `freshness_triggers`: key source files that would invalidate this artifact
- `known_unknowns`: generous list of gaps — things the question bank asked that you could not fully answer
- `tags`: tech stack, domain terms
- `aliases`: common abbreviations
- `relates_to`: sorted by target, each with `type` and `target` as `[[WIKILINK]]`
- `sources`: sorted by ref, each with `category`, `type`, `ref` (relative to source root)
- `notes`: empty string

**c. Write body sections:**

- `## Overview` — 2-4 sentences grounded in what you actually found, not generic descriptions
- `## Key Facts` — each fact linked to source with `→` syntax. **Use the Fact/Source/Confidence structure from your question analysis.** Aim for 3-5 facts minimum, each citing specific files.
- Type-specific sections per the template
- `## Related` — wikilinks matching frontmatter `relates_to`

**d. Write the file** to the correct subdirectory. Filename: lowercase ID + `.md`.

**e. Snapshot:**
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id-lowercase> --reef <reef-root>
```

**f. Present to the user.** Show each artifact one at a time as it's written.

---

## Step 4 — Update question bank

After generating artifacts, update `.reef/questions.json`:

- Mark questions as `"answered"` if the artifacts fully address them
- Mark as `"partial"` if artifacts touch on it but gaps remain
- Leave as `"unanswered"` if the snorkel pass couldn't address them

This gives `/reef:test` and `/reef:scuba` a clear picture of what's covered and what needs deeper work.

---

## Step 5 — Wrap up

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Snorkel pass: generated N artifacts, answered M/T questions" --reef <reef-root>
```

Summarize:
- Artifacts created (list IDs and one-line descriptions)
- Questions answered vs remaining
- Key gaps discovered (the most important known_unknowns across artifacts)

Then suggest next steps:

"The snorkel pass answered M of T discovery questions. The remaining gaps are areas where code alone is not enough — domain context, decision rationale, operational reality.

- `/reef:scuba` — work through the unanswered questions together. You bring the domain knowledge, I read the code.
- `/reef:deep` — exhaustive line-by-line tracing of a specific area.
- `/reef:test` — see how well the reef answers your questions right now."

---

## Voice and Personality

- Curious Researcher voice. Present-participle narration.
- No emojis. No exclamation marks.
- Honest about uncertainty. Generous known_unknowns. When guessing, say so.
- Flag cross-system boundaries immediately when found.
- Do not narrate every file. Summarize at the source level, call out interesting findings.

---

## Key Rules

- **Always read the artifact contract before writing any artifact.**
- **Questions steer discovery.** Don't just scan blindly — use the question bank to decide what to investigate.
- **Artifact IDs**: uppercase prefix + uppercase domain/name, hyphen-separated.
- **Filenames**: lowercase ID + `.md`.
- **Source refs always relative** to source root.
- **Stop when diminishing returns.** If a source is simple, 2-3 artifacts is fine. Don't pad.
- **Cross-system contracts always-on.** When code calls another system, flag it.
- **No user input.** Snorkel is fully automated. Read, generate, report.

---

## If No Question Bank Exists

If `.reef/questions.json` is empty or missing, fall back to the understanding template:

1. Read `/Users/jessi/Projects/seaof-ai/reef/references/understanding-template.md`
2. Do a quick structural scan per source
3. Auto-generate questions (same logic as reef:init Step 5)
4. Write them to `.reef/questions.json`
5. Then proceed with the question-guided scan above

This ensures snorkel always has direction, even if called without init.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No sources**: "No sources configured. Run `/reef:init` to add source paths."
- **Source path missing**: warn, skip, continue with others.
- **reef.py fails**: report the error. Do not silently swallow.
- **No structures found in a source**: still generate a SYS- artifact with generous known_unknowns.
