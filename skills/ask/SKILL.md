---
description: "Turn the reef's known_unknowns into a ranked question bank the owner can answer"
---

# /reef:ask

Every artifact carries `known_unknowns`. They are the reef's honest gaps — the things
the code could not settle. Left alone they stay where they were written: scattered
across dozens of artifacts, one or two at a time, invisible as a body of work.

This skill collects them, decides which ones a human actually has to answer, and
deposits those as a ranked question bank at `.reef/questions-for-owner.md`.

**The inversion this skill exists for.** Scuba's original posture was "AI found the
answers, I asked the questions" — a domain expert sits beside the agent and answers as
it goes. That posture assumes someone is available and already knows. Often neither
holds: a consultant on day one, an engineer inheriting a system whose authors left, an
agent running unattended overnight. In those cases the reef still gets built, and the
questions it could not resolve should not evaporate. They should queue up, addressed,
with the groundwork already done, for whoever can answer them later.

So: **the agent asks the questions, and the owner answers only the ones that nobody
else could.**

## Setup

Read `${CLAUDE_PLUGIN_ROOT}/references/methodology.md` for voice and anti-patterns.

## Voice

Curious Researcher. The question bank is written for a busy owner who did not ask for
it — every entry has to justify its own existence in its first two lines. No emojis.
No exclamation marks. Never rhetorical: "Does anyone know how this works?" is not a
question, it is a complaint.

## Procedure

### 1. Harvest

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py unknowns --reef <reef-root>
```

Add `--pending-only` to skip artifacts whose unknowns are all routed already. Use it
on any run after the first.

Each unknown comes back as an object, not a bare string:

```json
{ "uid": "92479d03", "text": "...", "deposited": false, "deposited_in": null }
```

The `uid` is stable for as long as the text is unchanged, and it is how an entry in the
bank claims an unknown (step 5). Reword an unknown and its uid changes — correctly, since
a reworded question needs re-routing.

Also in the output and worth reading before you start:

- `source_roots` — where each source name resolves on disk. Use it; do not guess paths.
- `last_verified` and `freshness_note` per artifact — how recently anyone checked.
- `artifacts_claiming_no_unknowns` — artifacts declaring none at all. Per methodology, an
  empty list that should have entries is worse than a long one. If this is non-empty, name
  those artifacts in the wrap-up as review candidates. `no_unknowns_check: "complete"`
  confirms the check ran, so an empty list means "none found", not "not implemented".

**If the bank predates this mechanism**, `routed_uids` is 0 and everything reads as
pending even though entries exist. Do not duplicate them. Read the bank first, and as you
work, add the `Routes to` line (step 5) to the existing entries that already cover an
unknown. The bank converges over a run or two.

### 2. Triage every unknown before asking anyone

**This is the gate that makes the bank worth opening.** An unknown that a careful read
would settle is not an owner question; it is unfinished work.

Sort each into one of four buckets:

- **Already asked** — an existing bank entry covers it. Add its uid to that entry's
  `Routes to` line. Do not write a second entry. On a mature reef this is the most common
  outcome, and it is a success, not a skip.
- **Resolvable from sources** — grep, read, trace. If you find the answer, update the
  artifact: move the fact into Key Facts with its citation and drop the unknown from
  frontmatter. It never reaches the bank.
- **Resolvable but expensive** — the answer is in the sources but needs a long trace.
  `/reef:deep` is the right tool, not the owner. Record it in the bank's
  `## Deferred to /reef:deep` section (step 5) with its uid and a one-line reason. This
  is the only place deferrals are recorded; do not leave them implicit.
- **Genuinely outside the sources** — runtime behaviour, history, intent, ownership,
  anything in a system the reef cannot see. **These become questions.**

**When an unknown already documents its own search**, take it at its word. A mature reef's
unknowns often name the greps that were run and what they returned ("no migration creates
this table; a grep across all five repos returns only the INSERT"). Spot-check a sample of
those rather than re-running every search — re-deriving 200 conclusions the text already
states is not diligence, it is the slowest possible way to learn nothing. Re-run the search
when the unknown is vague about what was checked, when `last_verified` is old, or when your
spot-check finds the stated result wrong.

Where an unknown says nothing about what was checked, go read. That is the default.

### 3. Cluster

The same question usually surfaces in several artifacts, phrased differently each
time. `SCH-` asks whether a table exists, `PROC-` asks what happens when the write
fails, `RISK-` asks whether the exposure is real — one answer settles all three.

Group unknowns that a single human answer would resolve. One cluster is one entry.
Collect every member's uid; they go on the entry's `Routes to` line so the answer can be
routed back to every artifact it settles.

### 4. Rank

Order the bank by what the answer unblocks, not by artifact order:

1. **Answers that change a conclusion.** If the answer could flip a finding the reef
   currently states, it goes first. Say which finding, by artifact id.
2. **Answers that unblock the most artifacts.** Cluster size is a proxy; a three-artifact
   cluster outranks a one-artifact cluster at equal weight.
3. **Answers only one named person can give.** If a source names the person or team who
   would know, that question is cheap to route and should not sit at the bottom.
4. **Everything else**, by cluster size.

**The exclusion test is the inverse of rank 1.** If you cannot name a single artifact
whose text would change when the answer arrives, the unknown does not go in the bank.
Drop it and say how many you dropped in the report. A short bank that is all
load-bearing beats a complete one nobody finishes.

### 5. Write the bank

Write `.reef/questions-for-owner.md`. Every entry has exactly these five parts:

```markdown
## {cluster label} — {the question as a single sentence}

**Question.** One sentence, answerable. If there are genuinely two, number them — but
two is the limit, and they must share an answer source.

**Why it matters.** What the reef currently cannot state, or states with a hedge,
until this is answered. Name the artifacts by id. If a conclusion would flip, say so
here and say which way.

**Already checked.** What you exhausted, specifically enough that the owner does not
repeat it: files read, greps run and their results, what was absent. This part is not
optional. An entry without it is a complaint, not a question.

**Files a human would need.** Where the answer lives, or — where it does not live in
any source the reef can see — what artefact outside the reef would hold it.

**Routes to.** The artifacts this answer updates, each with the uids it settles:
`SYS-INVENTORY (u:92479d03, u:1f0ab5cc)`, `SCH-INVENTORY (u:77c31e40)`
```

End the file with one section for deferrals:

```markdown
## Deferred to /reef:deep

Answerable from the sources, but only by a trace long enough to be its own task.
Not owner questions.

- `u:3ab90f12` PROC-ORDER-CANCEL — every caller of the outbox relay across two repos
```

**Rules for the bank as a whole:**

- **`Routes to` is mandatory and is the file's index.** `reef.py unknowns` reads those
  uids to decide what is still pending. An entry without them is invisible to the next
  run and will be written again by somebody.
- **Idempotent.** On a re-run, keep entries that are still open, drop entries whose
  unknowns have all disappeared from the frontmatter, and append new ones. **Never rewrite
  the file from scratch** — an owner may have annotated it.
- **New entries follow the five-part format; old entries are left as they are.** A bank
  written before this format existed will use different labels. Do not restyle it — that
  is a rewrite, and it destroys annotations. Add the `Routes to` line to an old entry when
  you route an unknown to it, and leave the rest alone.
- **No entry without "Already checked."**
- **Absence is a finding, and it is stated as one.** "No `CREATE TABLE` exists in any of
  the six migrations, and a grep across all five repos returns only the INSERT" is the
  answer to *have you checked* — write it, do not summarise it as "not found".

### 6. Post-write

If step 2 resolved unknowns and changed artifacts, snapshot **each changed artifact by
id** — there is no reef-wide snapshot — then rebuild:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py snapshot <ARTIFACT-ID> --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py lint --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-index --reef <reef-root>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py rebuild-map --reef <reef-root>
```

Then log, whether or not artifacts changed:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Owner question bank: N questions from M unknowns across K artifacts." --reef <reef-root>
```

Lint must end at 0 errors.

### 7. Report

Report the numbers **for the scope you actually worked**, not the harvest header. If you
ran `--pending-only` or worked a subset, say so on the first line.

```
Question bank — N new entries (scope: {what you covered})

  Harvested     {pending in scope} unknowns across {artifacts in scope} artifacts
  Already asked {A} routed to existing entries
  Resolved      {B} from sources — artifacts updated, unknowns dropped
  Deferred      {C} to /reef:deep
  Dropped       {D} blocking nothing
  Deposited     {N} new questions

  Top of the bank:
    1. {question} — would settle {k} artifacts, could flip {ARTIFACT-ID}
    2. ...

  Bank is now {total} entries. Written to .reef/questions-for-owner.md
```

The five middle numbers must account for every unknown in scope. If they do not sum,
say which ones you could not classify rather than adjusting a number.

Then say what it is for, once: the bank is what the owner reads when they have twenty
minutes, and what the next `/reef:scuba` session uses as its agenda instead of starting
from a blank page.

## When to Run

- **After scuba or deep**, whenever the reef was built without a domain expert present.
  This is the common case for unattended runs.
- **Before a walkthrough** with whoever owns the system. The bank is the agenda.
- **After `/reef:update`**, when a change introduced unknowns the code cannot settle.

## Key Rules

- Never invent facts. An unknown is not a licence to speculate about the answer.
- **Triage before asking.** The owner's time is the scarcest input the reef has.
- One question per entry. A paragraph with four question marks gets answered zero times.
- Every entry routes. An answer with nowhere to land was not worth asking for.
- The bank is a working document, not a report. Owners annotate it; respect that.

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No artifacts**: "No artifacts yet — nothing to harvest. Run `/reef:snorkel` first."
- **Zero unknowns across the whole reef**: do not celebrate it. Report it as a warning —
  a reef with no declared unknowns has almost certainly stopped noticing them. Point at
  `artifacts_claiming_no_unknowns` and suggest `/reef:test`.
- **reef.py fails**: report the error. Do not silently swallow.
