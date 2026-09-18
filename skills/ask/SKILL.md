---
description: "Turn the reef's known_unknowns into a ranked question bank the owner can answer"
---

# /reef:ask

Every artifact carries `known_unknowns`. They are the reef's honest gaps — the things
the code could not settle. Until now they stayed where they were written: scattered
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

Returns every artifact's `known_unknowns` with its id, type, status, sources, file
path, and whether that artifact already appears in the deposit file.

Read `artifacts_claiming_no_unknowns`. Per methodology, an empty `known_unknowns` list
that should have entries is worse than a long one. If artifacts appear there, name
them in the wrap-up as candidates for review — do not silently treat them as complete.

### 2. Resolve what you can before asking anyone

**This is the gate that makes the bank worth opening.** An unknown that a careful read
of the sources would settle is not an owner question; it is unfinished work.

For each unknown, decide:

- **Resolvable from sources** — grep, read, trace. If you find the answer, update the
  artifact: move the fact into Key Facts with its citation and drop the unknown. Lint
  and snapshot as usual. It never reaches the bank.
- **Resolvable but expensive** — the answer is in the sources but would take a long
  trace. Note the cost and keep going; `/reef:deep` is the right tool, not the owner.
- **Genuinely outside the sources** — runtime behaviour, history, intent, ownership,
  anything in a system the reef cannot see. **These become questions.**

If you cannot tell which of the three a given unknown is, it is the first one. Go read.

### 3. Cluster

The same question usually surfaces in several artifacts, phrased differently each
time. `SCH-` asks whether a table exists, `PROC-` asks what happens when the write
fails, `RISK-` asks whether the exposure is real — one answer settles all three.

Group unknowns that a single human answer would resolve. One cluster is one entry.
Record every contributing artifact id so the answer can be routed back to all of them.

### 4. Rank

Order the bank by what the answer unblocks, not by artifact order:

1. **Answers that change a conclusion.** If the answer could flip a finding the reef
   currently states, it goes first. Say which finding, by artifact id.
2. **Answers that unblock the most artifacts.** Cluster size is a proxy; a three-artifact
   cluster outranks a one-artifact cluster at equal weight.
3. **Answers only one named person can give.** If a source names the person or team who
   would know, that question is cheap to route and should not sit at the bottom.
4. **Everything else**, by cluster size.

### 5. Write the bank

Write `.reef/questions-for-owner.md`. Every entry has exactly these four parts:

```markdown
## {ARTIFACT-ID or cluster label} — {the question as a single sentence}

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
```

**Rules for the bank as a whole:**

- **Idempotent.** On a re-run, keep entries that are still open, drop entries whose
  unknown has since been resolved, and append new ones. Never rewrite the file from
  scratch — an owner may have annotated it.
- **No entry without "Already checked."** If you cannot fill it, you have not done
  step 2 for that unknown.
- **Absence is a finding, and it is stated as one.** "No `CREATE TABLE` exists in any
  of the six migrations, and a grep across all five repos returns only the INSERT" is
  the answer to *have you checked* — write it, do not summarise it as "not found".
- **Do not invent the stakes.** If an unknown blocks nothing, it does not go in the
  bank. A short bank that is all load-bearing beats a complete one nobody finishes.

### 6. Post-write

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reef.py log "Owner question bank: N questions from M unknowns across K artifacts." --reef <reef-root>
```

If step 2 resolved unknowns and changed artifacts, also run `lint`, `snapshot`,
`rebuild-index` and `rebuild-map` as the other skills do.

### 7. Report

```
Question bank — N entries

  Harvested     {total_unknowns} unknowns across {artifacts_with_unknowns} artifacts
  Resolved      {X} from sources — artifacts updated, unknowns dropped
  Deferred      {Y} to /reef:deep — answerable but expensive
  Deposited     {N} questions for the owner

  Top of the bank:
    1. {question} — would settle {k} artifacts, could flip {ARTIFACT-ID}
    2. ...

  Written to .reef/questions-for-owner.md
```

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
- **Resolve before asking.** The owner's time is the scarcest input the reef has.
- One question per entry. A paragraph with four question marks gets answered zero times.
- Route the answer back. Every entry names the artifacts that will be updated when the
  answer arrives, so nothing is answered into a void.
- The bank is a working document, not a report. Owners annotate it; respect that.

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **No artifacts**: "No artifacts yet — nothing to harvest. Run `/reef:snorkel` first."
- **Zero unknowns across the whole reef**: do not celebrate it. Report it as a warning —
  a reef with no declared unknowns has almost certainly stopped noticing them. Point at
  `artifacts_claiming_no_unknowns` and suggest `/reef:test`.
- **reef.py fails**: report the error. Do not silently swallow.
