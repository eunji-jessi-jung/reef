---
description: "Exhaustive line-by-line tracing of critical areas"
---

# /reef:deep

Deep is the final depth in the reef pipeline. It's not about covering more ground — scuba already did that. Deep is about discovering what's worth going deeper on, then tracing it exhaustively.

The user arrives here after completing scuba. They have a working reef. Deep helps them see its shape, find the most interesting gaps, and follow the threads that pull them in.

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

### 2. Gate: scuba must be complete

Read `.reef/scuba-manifest.json`.

- **If not found:** Stop. Tell the user:
  ```
  This reef hasn't been through scuba yet. Deep builds on scuba-level
  artifacts — without them, there's not enough foundation to dive from.

  Run /reef:scuba first.
  ```

- **If found but `planned` is non-empty:** Scuba isn't finished. Tell the user:
  ```
  Scuba isn't finished — {N} items still remaining in the manifest.
  Run /reef:scuba to resume and complete it first.
  ```
  Do not allow the user to bypass this. Deep on an incomplete reef produces shallow results dressed up as deep ones.

- **If found and `planned` is empty:** Proceed.

### 3. Read the reef

Before surfacing anything to the user, build a full picture of the reef's current state. Read:

1. `.reef/project.json` — scope, services, source roots.
2. `.reef/scuba-manifest.json` — what was completed, what was skipped (and why).
3. `.reef/questions.json` — the question bank. Note which are answered, partially answered, or unanswered.
4. `artifacts/` — read frontmatter of all artifacts. Build a mental map of: artifact counts by type and service, `known_unknowns` across all artifacts, `relates_to` edges (which artifacts connect, which are isolated).
5. `sources/infra/` — infrastructure extraction output (storage, runtime, queues). Note what was extracted but never traced into artifacts.
6. `sources/apis/` and `sources/schemas/` — note coverage gaps (services with schemas but no SCH- artifacts, APIs with no API- artifacts).
7. `sources/context/` and `sources/raw/` — scan for files not yet referenced by any artifact. If new context exists, mention it in the briefing: "I see you've added N new context files since the last update — I'll weave these in as we explore." New context docs are especially valuable for deep — they often contain the design rationale that code doesn't reveal.

### 4. Surface the briefing

Present the user with a single integrated briefing that incites curiosity through three lenses. This is not a status report — it's an invitation to explore.

#### 4a. Topology

Show a compact visual of the reef's shape — services, artifact density, infrastructure dependencies, and cross-service connections. Use a simple diagram (ASCII or Mermaid) that fits in one screen.

The goal is to let the user *see* what they built and notice the asymmetries: where coverage is dense vs thin, which services are well-connected vs isolated, where infrastructure is extracted but not traced.

**Rules:**
- One diagram, compact enough to scan in 10 seconds.
- Show artifact counts per service, grouped by type.
- Show infrastructure dependencies (storage, queues, runtime) as a separate layer.
- Show cross-service connections (CON- artifacts, shared entities).
- Do not list every artifact — show the shape, not the inventory.

#### 4b. Unanswered questions

Surface questions from the question bank (`.reef/questions.json`) that are unanswered or partially answered. These are questions the user seeded during init — they already cared about these.

For partially answered questions, frame them as "the reef knows X but not Y" — the partial answer is more compelling than a blank.

**Rules:**
- Maximum 3 questions. Pick the ones with the highest gap-to-value ratio.
- Phrase each as a genuine question, not an artifact ID or coverage metric.
- If all questions are fully answered, skip this section — don't manufacture gaps.

#### 4c. Spots worth tracing

From the reef reading in Step 3, identify areas where surface-level coverage hides real complexity. These come from:

- `known_unknowns` that cluster around a specific area (multiple artifacts flagging uncertainty about the same thing)
- Infrastructure that was extracted but never followed into artifacts (e.g., 46 GCS flow paths but only 3 traced)
- Cross-service boundaries with implicit contracts (services that interact but have no CON- artifact)
- Skipped manifest items whose skip reasons suggest complexity, not irrelevance

**Rules:**
- Maximum 3 spots. Phrase each as a curiosity hook — a question the user might actually wonder about.
- Never use artifact type prefixes in user-facing text. Say "How does the system recover when a pipeline fails at layer 3?" not "PROC-PIPELINE-LAYER3-ERROR-RECOVERY needs deep tracing."
- Each spot should make the user think "huh, I actually don't know that" — not "I should probably document that."

#### 4d. Invitation for raw input

After the topology and questions, invite the user to contribute context that never made it into code:

```
If you have design docs, SRDs, runbooks, or incident postmortems that
capture why things were built the way they are — drop them into
sources/context/ (by type) or sources/raw/ (anything else). I'll use
them to surface questions that code alone can't answer.
```

This is an invitation, not a requirement. One sentence. Do not present it as a checklist or a blocker.

#### 4e. Ask

End the briefing with a single open question:

```
Which of these pulls you in? Or bring your own — something you've
been wondering about but never had time to chase down.
```

**Total briefing budget: max 5 questions/spots across 4b and 4c combined.** The user should be able to scan the briefing in under a minute and feel pulled toward one thread, not overwhelmed by options.

### 5. Follow the thread

Once the user picks a question or names their own, begin exhaustive tracing.

#### 5a. Scope the dive

Before reading code, state the scope:
- What specific area will be traced
- Which source files/directories are the likely entry points
- What existing artifacts are relevant (read them first to avoid re-deriving known facts)

Get a quick confirmation from the user: "Starting here — does this scope feel right?"

#### 5b. Exhaustive reading

This is not snorkel. Read deeply. Trace paths. Check edge cases.

- **Read entire directories** relevant to the target. Do not sample — read all files.
- **Trace execution paths.** Follow function calls, imports, middleware chains, decorators, and signal handlers from entry point to final effect.
- **Map every function** that materially affects runtime behavior in the target area.
- **Read config files** — environment setup, dependency injection, feature flags, constants.
- **Check test files** for behavioral documentation. Tests often reveal edge cases and intended behavior that source code does not make obvious.
- **Read error handling paths.** What happens when things fail is often more important than the happy path.

#### 5c. Collaborative domain framing

The deep dive is collaborative. The user provides context that reshapes how Claude interprets the code:

- "That retry logic was added after the March incident" — becomes a DEC- artifact or enriches a PROC-.
- "The dedup logic is supposed to work but we are not confident it does" — becomes a RISK- artifact.
- "This module is owned by the platform team, not us" — updates ownership context on existing SYS- artifacts.

When the user provides context, integrate it immediately. Do not wait for a batch update.

### 6. Dense artifact generation

Deep dives produce dense artifacts. The standard is higher here:

- **5+ Key Facts per artifact minimum.** This is the deep dive bar. If an artifact has fewer than 5, keep reading — there is more to find.
- **Precise line citations required.** Use `src/services/order.py:L45-89`, not just `src/services/order.py`. Every Key Fact must cite specific lines.
- **Each Key Fact should capture behavior that is not obvious from a casual read.** If someone could learn it from a 30-second skim, it does not belong in a deep dive artifact.
- **`known_unknowns` should flag things that require running the code or checking infrastructure to verify.** Runtime behavior, environment-specific config, race conditions, actual error rates.

### 7. Cross-referencing

As the deep dive proceeds:

- Update `relates_to` on existing artifacts that connect to new findings.
- Flag contradictions between deep findings and existing draft artifacts. Be specific: "SYS-INGEST says the order service is stateless, but the deep dive shows session state stored in L34-41 of order_handler.py."
- Propose CON- artifacts when cross-system interactions are discovered.
- If raw input (docs in `sources/raw/`) informed the findings, cite the doc and the specific section.

### 8. Post-write

**Immediately after writing each artifact file, lint it:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
```

Parse the JSON output, filter to errors for this artifact's ID. If errors are found, fix them now.

Then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <artifact-id> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Deep: <artifact-id>" --reef <reef-root>
```

### 9. Continue or surface

After completing a thread, present what was found and created. Then:

- If the dive surfaced new questions or adjacent areas worth tracing, mention them briefly (1-2 sentences each).
- Ask if the user wants to follow another thread or stop here.
- Do not pressure. "The reef is richer for this. Want to keep going, or is this a good place to stop?" is the right tone.

If the user is done, close with a summary of what deep added: artifacts created/updated, contradictions resolved, known_unknowns closed.

## Key Rules

- **Gate is absolute.** Scuba must be complete. No exceptions.
- **Briefing, not assignment.** Deep surfaces interesting questions — the user decides which to follow.
- **Max 5 questions/spots in the briefing.** Overwhelm kills curiosity.
- **Read deeply. Trace paths. Check edge cases.** This is not snorkel.
- **5+ Key Facts per artifact.** Line citations required.
- **Do not summarize — explain actual behavior.**
- **Never invent facts.** If uncertain, add to `known_unknowns`.
- **Flag contradictions with existing artifacts explicitly.**
- **No artifact type prefixes in user-facing text.** Questions, not IDs.
