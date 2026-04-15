---
description: "Explore a topic, capture knowledge, or update an artifact"
---

# /reef:artifact

Work with reef artifacts conversationally. The user never needs to know artifact types or IDs — reef figures out where knowledge belongs.

## Setup

Read these references before doing anything else:

- `${CLAUDE_PLUGIN_ROOT}/references/artifact-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/references/methodology.md`

## Voice

Curious Researcher. Present-participle narration. No emojis. No exclamation marks.

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

Read `.reef/project.json` for service list and source paths.

### 2. Determine mode

Parse the user's request to determine which mode to use. The user will NOT say "explore mode" or "capture mode" — they will speak naturally. Match their intent:

**Explore mode** — the user has a topic or question they want to investigate:
- "I want to dig deeper into how order finalization works"
- "What do we know about the notification system?"
- "Is there anything about how Orders and Payments share transaction data?"
- "I want to create something about the caching layer"

**Capture mode** — the user learned something and wants to persist it:
- "Oh, I didn't know that — can we add that to the reef?"
- "We should document that the queue uses RabbitMQ, not Redis"
- "Can we save what we just discussed about auth token rotation?"

**Update mode** — the user names a specific artifact to modify:
- "Update SCH-ORDERS-CORE"
- "Add a Key Fact to PROC-ORDERS-FULFILLMENT about the new validation"
- "The freshness note on SYS-PAYMENTS is wrong"

If the intent is ambiguous, ask one clarifying question. Do not ask the user to pick a mode — just ask about their topic.

---

### 3. Explore mode

The user arrives with a topic, question, or area of interest. Reef's job: find what exists, read the source code, and either enrich an existing artifact or create a new one.

#### 3a. Search the reef

Search for existing coverage of the user's topic:

1. Scan artifact filenames and titles for keyword matches.
2. Read `index.md` for the full artifact catalog.
3. Grep artifact bodies (Key Facts, Overview, Known Unknowns) for the topic.
4. Check `.reef/questions.json` for related unanswered questions.

Report what you found:

```
Searching the reef for "{topic}"...

Found:
  SCH-ORDERS-CORE — mentions "{topic}" in Key Fact 12 (brief context)
  PROC-ORDERS-FULFILLMENT — covers related flow (brief context)
  Q-023 (unanswered): "How does {topic} interact with..."

Not covered:
  No artifact specifically about {topic}. Closest is SCH-ORDERS-CORE
  which mentions it but doesn't go deep.
```

#### 3b. Read the source code

Based on the search results, identify and read the relevant source files:

1. If existing artifacts reference the topic, read their `sources` files.
2. Search source repos for the topic (model names, function names, module names).
3. Read the actual code — don't rely on artifact summaries alone.

Report what you found in the code, focusing on facts not yet captured in any artifact.

#### 3c. Propose where it belongs

Based on what you found in the reef and source code, propose one of:

**Enrich an existing artifact:**
```
This fits best in SCH-ORDERS-CORE. I'd add:
  - 2 new Key Facts about the fulfillment routing strategy
  - 1 worked example showing the order-to-shipment flow
  - Update known_unknowns: remove Q about partial fulfillments (now answered)

Want me to make these changes?
```

**Create a new artifact:**
```
This doesn't fit in any existing artifact. I'd create:
  PROC-ORDERS-RETURN-LIFECYCLE
  - 8 Key Facts covering the request → approve → refund → restock flow
  - Worked example: what happens when a partial return is requested
  - Links to SCH-ORDERS-CORE and API-ORDERS-REST

Want me to create it?
```

**Both:**
```
This spans two artifacts:
  1. Enrich SCH-ORDERS-CORE — add 2 Key Facts about return policy fields
  2. Create PROC-ORDERS-RETURN-LIFECYCLE — the full lifecycle flow

Want me to do both?
```

Wait for user confirmation before writing. The user may redirect ("actually, put it in the schema, not a new proc") — follow their lead.

#### 3d. Write

On confirmation, proceed to Step 6 (write the artifact).

---

### 4. Capture mode

The user learned something — from this conversation, from a colleague, from reading code — and wants to persist it in the reef.

#### 4a. Clarify the fact

Restate what the user wants to capture as a concrete, citable fact:

```
Capturing: "The fulfillment queue targets RabbitMQ in production,
configured via FULFILLMENT_BROKER_URL env var."

Is that accurate?
```

If the user said something vague ("save what we just discussed"), summarize the key facts from the recent conversation and ask which ones to capture.

#### 4b. Find where it belongs

Search artifacts for where this fact fits:

1. Match the domain/service.
2. Match the artifact type (schema fact → SCH-, process fact → PROC-, architectural choice → DEC-).
3. Check if an existing artifact's known_unknowns would be resolved by this fact.

```
This belongs in SYS-PIPELINE, Key Facts section.
It also resolves known_unknown: "What message broker does the pipeline use in production?"

Want me to add it?
```

If no existing artifact fits, propose creating one (same as explore mode 3c).

#### 4c. Write

On confirmation, proceed to Step 6 (write the artifact).

---

### 5. Update mode

The user names a specific artifact to modify.

1. Read the artifact file.
2. Identify what needs changing from the user's request.
3. If the user's request is vague ("update it"), re-read the artifact's source files and check for staleness. Report what changed and propose specific updates.
4. Preserve all unaffected content.
5. Proceed to Step 6.

---

### 6. Write the artifact

This step is shared by all three modes.

#### 6a. Evidence gathering

- Read relevant source files referenced by or related to the artifact.
- Check edges: read `relates_to` targets to understand connections.
- Trace claims back to sources. Every Key Fact needs a source citation (`→ path/to/file.py:line`).

#### 6b. Glossary cross-check

Cross-check against existing GLOSSARY- artifacts:

1. Read all GLOSSARY- artifacts in `artifacts/glossary/`.
2. Scan the artifact for domain terms that appear in the glossary.
3. If any term contradicts the glossary definition, align the artifact text — or update the glossary if the artifact is more accurate.
4. Disambiguate terms flagged as ambiguous in the glossary.

Skip if no GLOSSARY- artifact exists.

#### 6c. Validate before writing

**Blocking checks** (must all pass):

- YAML frontmatter is parseable.
- All required fields present (see `references/artifact-contract.md`).
- `id` matches the filename (lowercase of ID + `.md`).
- All enum fields use valid values.
- `freshness_note` is not empty.
- Key Facts section is present (except Glossary type).

**Warning checks** (report but do not block):

- All `relates_to` targets resolve to existing artifact files.
- All `sources` refs resolve to files on disk.
- All required body sections for the type are present.
- `## Related` wikilinks match `relates_to` frontmatter entries.

#### 6d. Write and post-write

Write the artifact file to the correct directory (see ID conventions below).

**Immediately after writing, lint it:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Parse the JSON output, filter to errors for this artifact's ID. If errors are found, fix them now.

Then run post-write commands:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Created <artifact-id>" --reef <reef-root>
```

Use "Updated" instead of "Created" in update/capture mode when modifying an existing artifact.

#### 6e. Confirm to user

```
Done. {Created|Updated} {ARTIFACT-ID}.
  {1-2 line summary of what was added/changed}
```

If the exploration surfaced new questions that weren't captured in the artifact, add them to `.reef/questions.json` and mention:

```
Also added {N} new questions to the question bank:
  Q-045: {question text}
Run /reef:deep to investigate these.
```

---

## Artifact ID Conventions

**Prefix by type:**

| Type | Prefix | Directory |
|---|---|---|
| system | SYS- | artifacts/systems/ |
| schema | SCH- | artifacts/schemas/ |
| api | API- | artifacts/apis/ |
| process | PROC- | artifacts/processes/ |
| decision | DEC- | artifacts/decisions/ |
| glossary | GLOSSARY- | artifacts/glossary/ |
| connection | CON- | artifacts/contracts/ |
| risk | RISK- | artifacts/risks/ |
| pattern | PAT- | artifacts/patterns/ |

**Format:** Uppercase, hyphen-separated. Examples: `SYS-INGEST`, `SCH-INGEST-ORDER`, `CON-INGEST-PIPELINE-FEED`.

**Filename:** Lowercase of the ID with `.md` extension. Example: `SYS-INGEST` → `sys-ingest.md`.

**Templates:** Read the matching template from `${CLAUDE_PLUGIN_ROOT}/references/templates/` when creating new artifacts. Follow the template structure exactly.

## Key Rules

- **The user never needs to know artifact types or IDs.** Reef determines these from context.
- **Always propose before writing.** Show the user what you plan to create or change. Wait for confirmation.
- **One artifact per invocation unless the user asks for more.** Keep it focused.
- **Every Key Fact must cite a source.** No uncited claims.
- **Lint-on-write, always.** Fix lint errors before finishing.
