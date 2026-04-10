---
description: "Deepen knowledge through Socratic questioning"
---

# /reef:scuba

Interactive, question-driven knowledge extraction. The user teaches Claude what matters; Claude produces deep, accurate artifacts. Core principle: "AI found the answers. I asked the questions."

## Setup

Read these references before doing anything else:

- `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md`
- `/Users/jessi/Projects/seaof-ai/reef/references/understanding-template.md` (33 baseline questions)

## Voice

Curious Researcher at scuba depth. Conversational, Socratic — asking good questions, not interrogating. Present-participle narration for progress. Genuine curiosity about the domain. No emojis. No exclamation marks.

Honest about limits: "I can see the code does X, but I can not tell from the code alone why this design was chosen. Do you know the history?"

The user is the domain expert. Claude reads code; the user knows context.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Load context

- Read `.reef/project.json` to understand scope and source roots.
- Read `.reef/questions.json` to see the question bank and what has been answered.
- Scan `artifacts/` for existing artifacts — read their frontmatter to understand current coverage.

### 3. Determine entry point

One of three modes based on what the user says:

**a. User names a topic** — e.g. "Let's explore the order processing lifecycle":

1. Read relevant source code for that topic.
2. Generate targeted questions that code reading alone cannot answer.
3. Begin the question-by-question flow.

**b. Deepen a draft** — e.g. "Deepen SYS-INGEST":

1. Read the existing artifact file.
2. Review its `known_unknowns` for gaps.
3. Generate questions specifically to fill those gaps.
4. Begin the question-by-question flow.

**c. Generate from template** — user has no specific direction:

1. Adapt the 33 baseline questions from `understanding-template.md` to what the structural scan reveals about this codebase.
2. Skip questions already answered by existing artifacts.
3. Present the adapted question list and let the user choose where to start.

### 4. Guided priorities

Follow these priorities loosely, not rigidly:

- SYS- boundaries first, then fill in with SCH-, API-, PROC-, and others.
- Any artifact type at any time based on the conversation flow.
- Warn (do not block) if a PROC- is proposed before its parent SYS- exists.
- Propose cross-system CON- artifacts whenever system boundaries emerge.

### 5. Question-by-question flow

For each question or topic:

1. **Present the question.** One at a time. Do not dump a list.
2. **Listen to the user's answer.** Let them talk. Ask follow-ups if something is unclear.
3. **Synthesize what was learned:**
   - Fact — what was established
   - Why it matters — how it connects to the system understanding
   - Source — user statement, code reference, or both
   - Confidence — high/medium/low
   - Open question — anything the answer raised but did not resolve
4. **When enough material accumulates for an artifact,** propose creating or updating one. Explain what artifact type, what ID, and what it would cover.
5. **After each artifact is written,** always ask: "What did I get wrong? What am I missing?"

Proactively suggest questions that code cannot answer:

- Team ownership and responsibility boundaries
- Decision rationale and historical context
- Operational reality vs design intent
- Cross-system boundaries and integration pain points
- When uncertain about code interpretation, suggest documentation sources the user might have

Prioritize unanswered questions from `.reef/questions.json`.

### 6. Artifact creation

When creating or updating an artifact, follow the full artifact contract.

**Frontmatter field order** (all fields required, in this order):

```yaml
id:
type:
title:
domain:
status:
last_verified:
freshness_note:
freshness_triggers:
known_unknowns:
tags:
aliases:
relates_to:
sources:
notes:
```

**Body requirements:**

- Include all required body sections for the artifact type (per the contract).
- Key Facts section with source citations using `→` syntax.
- `## Related` section with wikilinks that match `relates_to` in frontmatter.

**Determinism rules** (for reproducible diffs):

- `relates_to` sorted alphabetically by target.
- `sources` sorted alphabetically by ref.
- `freshness_triggers` sorted alphabetically.

**Validation** — same blocking and warning checks as `/reef:artifact`:

- Blocking: YAML parseable, all required fields present, `id` matches filename, valid enums, non-empty `freshness_note`, Key Facts present (except Glossary).
- Warning: `relates_to` targets resolve, `sources` resolve, required body sections present, wikilinks match frontmatter.

Status can be "draft" or "active" depending on confidence from the conversation.

### 7. Post-write commands

Run these in order after each artifact file is written and accepted:

```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-index --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py rebuild-map --reef <reef-root>
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in the log message when updating an existing artifact.

### 8. Session management

- Track which questions have been covered in this session.
- At natural pauses, summarize progress: artifacts created or updated, questions answered, remaining gaps.
- The user can end the session at any time. Do not push to continue.

## Key Rules

- Never invent facts. If uncertain, add to `known_unknowns`.
- Honest gaps beat confident lies.
- The user is the domain expert. Claude reads code; the user knows context.
- Do not ask all questions at once — work through them one at a time.
- Prioritize unanswered questions from the question bank.
- After every artifact written, ask what was gotten wrong and what is missing.
