---
description: "Test the reef against your question bank"
---

# /reef:test

Test whether the reef actually answers the user's real questions. Uses the question bank seeded during `/reef:init` as the north star.

This is the accountability skill. Reef can generate beautiful artifacts all day, but if those artifacts do not answer the questions that matter, the reef is decorative. This skill finds the gaps.

---

## Context Loading

Before doing anything else, read these reference files:

1. `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md` — voice, personality, and the core principle that drives this skill.
2. `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md` — you need to understand artifact structure to evaluate whether answers are sourced.

---

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If not found, stop and tell the user to run `/reef:init` first.

### 2. Load the question bank

Read `.reef/questions.json` from the reef root.

If the file does not exist or the `questions` array is empty, enter **seed mode**:

Ask the user: "This reef has no questions yet. What questions do you need this wiki to answer? These become the test suite — the thing that tells you whether the reef is actually useful."

Give a few examples to prime the pump:
- "How does data flow between these services?"
- "What happens when X fails?"
- "Which teams own which boundaries?"

Collect questions one at a time or in a batch (follow the user's pace). Write them to `.reef/questions.json`:

```json
{
  "questions": [
    {
      "id": "Q-001",
      "text": "How does data flow from service-a to service-d?",
      "added": "2026-04-10",
      "status": "unanswered"
    }
  ]
}
```

Auto-increment the ID. Set `status` to `"unanswered"` for all new questions. Then proceed to Step 3.

### 3. Load all artifacts

Scan `artifacts/` and its subdirectories. Read each artifact file — frontmatter and body. Build a mental index of what each artifact covers: its type, its Key Facts, its known_unknowns, its sources.

Do not read source code. The entire point of this skill is to test whether the **artifacts alone** contain the answers. If you have to read source code to answer a question, the reef has a gap.

### 4. Answer each question

For each question in the question bank, attempt to answer it using **only** the content of existing artifacts. No source code. No external knowledge. Only what the reef contains.

Rate each question:

**Fully answered** — The artifacts contain a clear, sourced answer. You can point to specific Key Facts, specific artifact sections, and the answer is complete enough that a reader would not need to look elsewhere.

**Partially answered** — Some relevant information exists in the artifacts, but gaps remain. The answer is incomplete, shallow, or missing important dimensions.

**Not answerable** — The artifacts do not cover this topic at all, or the coverage is so thin that it does not constitute an answer.

For each rating, note:
- Which artifacts contributed to the answer (by ID)
- What specific Key Facts or sections were relevant
- What is missing (for partial and unanswered)

### 5. Render the report

Present the results as a text-rendered report:

```
Test Your Reef — {project name}                      {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: ████████████░░░░░░░░ {N}/{total} questions answered

 ✓  {question}      → {artifact references}
 ~  {question}       → partial: {artifact} (shallow)
 ✗  {question}

Gaps to explore:
  {artifact} is shallow — N Key Facts, needs /reef:scuba
  {source} has no PROC- artifacts — run /reef:deep on {path}
```

**Progress bar rules:**
- Width: 20 characters
- Fully answered questions count as filled blocks
- Partially answered count as half (round down)
- Not answerable count as empty
- Use `█` for filled and `░` for empty

**Report ordering:**
- Fully answered first (✓)
- Partially answered second (~)
- Not answerable last (✗)

**Gaps section:**
- For each gap, suggest a specific action: which skill to run, which artifact to deepen, which area to explore
- Be specific. "SYS-INGEST is shallow" is less useful than "SYS-INGEST has 2 Key Facts and 4 known_unknowns — the order lifecycle is not documented. Run `/reef:scuba` and ask about state transitions."

### 6. Update question status

After presenting the report, update `.reef/questions.json`:
- Set `status` to `"answered"` for fully answered questions
- Set `status` to `"partial"` for partially answered questions
- Leave `status` as `"unanswered"` for not answerable questions
- Add `last_tested` date field to each question

### 7. Gap-to-action loop

After the report, offer to act on the gaps:

"Want to start filling gaps? I can transition into:
- `/reef:scuba` to deepen a shallow artifact through guided questioning
- `/reef:deep` to do line-by-line tracing of a specific area

Which gap feels most important?"

If the user picks a gap, hand off to the appropriate skill. If not, end the session.

### 8. Log results

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Test pass: {answered}/{total} answered, {partial} partial, {unanswered} gaps" --reef <reef-root>
```

---

## Voice and Personality

Curious Researcher. Honest assessment — the purpose of this skill is to find gaps, not to celebrate coverage. A reef that answers 3 of 10 questions is not a failure; it is a reef that knows where to grow next.

- No emojis. No exclamation marks.
- Present-participle narration for progress: "Testing Q-001 against existing artifacts...", "Found a partial answer in SYS-INGEST..."
- When an artifact is shallow, say so plainly: "SYS-INGEST covers the basics but does not trace the order lifecycle."
- When a question is fully unanswered, do not soften it: "Nothing in the reef addresses this."
- Frame gaps as opportunities, not failures. The whole point is to know where to dig next.

---

## Error Handling

- **No reef found**: "No reef found in this directory. Run `/reef:init` first to set one up."
- **No questions and user declines to seed**: "Without questions, there is nothing to test. You can seed questions anytime by running `/reef:test` again or by editing `.reef/questions.json` directly."
- **No artifacts exist**: "This reef has no artifacts yet. Run `/reef:snorkel` to generate some drafts, then come back and test."
- **`reef.py` not found**: check that `/Users/jessi/Projects/seaof-ai/reef/scripts/reef.py` exists. If not, tell the user the plugin may not be fully installed.

---

## Important

- Always use `/Users/jessi/Projects/seaof-ai/reef` to reference the plugin's own files. Never hardcode paths to the plugin directory.
- This skill reads artifacts only. It must not read source code to answer questions. If the answer requires source code, the reef has a gap — that is the finding.
- The question bank is the north star. Everything this skill does serves those questions.
