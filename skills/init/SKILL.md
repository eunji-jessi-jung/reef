---
description: "Bootstrap a new reef wiki from your codebase"
---

# reef-init

Bootstrap a new reef — a structured knowledge wiki for one domain of source code.

This skill walks the user through scoping, scaffolding, indexing, and configuring a new reef. The conversation should feel like a knowledgeable colleague helping you set up a knowledge base, not a wizard with numbered steps.

---

## Context Loading

Before doing anything else, read these reference files:

1. `/Users/jessi/Projects/seaof-ai/reef/references/artifact-contract.md` — you need the ID conventions and artifact types to guide the user's mental model during setup.
2. `/Users/jessi/Projects/seaof-ai/reef/references/methodology.md` — voice, personality, and UX principles. Follow the Curious Researcher voice throughout this entire skill.

---

## Step 1 — Check for an existing reef

Look for a `.reef/` directory in the current working directory and in any path the user provides.

- If `.reef/` exists: read `.reef/project.json` and report what you find — name, sources, creation date. Then ask: "This directory already has a reef. Do you want to continue building on it, or start fresh? Starting fresh will remove the existing `.reef/`, `artifacts/`, and `sources/` directories."
- If the user wants to reset: delete the existing reef directories and proceed.
- If the user wants to continue: suggest `/reef:update` or `/reef:scuba` instead, and exit this skill.
- If no reef exists: proceed to Step 2.

---

## Step 2 — Scope the reef

Ask these questions one at a time. Wait for the user's answer before moving to the next question. Keep it conversational.

**2a — Name**

Ask: "What should this reef be called?"

This becomes the directory name. Suggest a convention like `my-reef` or `payments-reef` — lowercase, hyphenated, ending in `-reef` is the convention but not required.

**2b — Location**

Ask: "Where should it live?"

Default: a new directory in the current working directory, named after the reef. The user can specify any absolute or relative path. Resolve the final path and confirm it with the user.

**2c — Sources**

Ask: "What codebases does it cover? Give me the paths to the source repos."

Accept one or more paths (absolute or relative to cwd). For each path, verify it exists and contains files.

After collecting sources, provide this guidance based on what the user gave:

- If multiple sources: "Good — Reef works best when you include all services in a domain. That is how it discovers cross-system contracts."
- If single source: "You can always add more sources later, or create separate reefs for other services and merge them with `/reef:merge`."
- If the sources seem to span unrelated domains: "Think of this reef as one knowledge layer for one ecosystem. Services that don't talk to each other probably belong in separate reefs. Do these all belong together?"

Store the resolved absolute paths for use in later steps.

---

## Step 3 — Scaffold the directory structure

Report: "Scaffolding the reef structure..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py init <resolved-reef-path>
```

Parse the JSON output. Verify it reports success. If it fails, report the error and suggest how to fix it (usually a permissions issue or the directory already exists).

After scaffolding, update `.reef/project.json` to include the source paths the user specified. The `sources` field should be an array of objects, each with `name` (directory basename) and `path` (resolved absolute path):

```json
{
  "sources": [
    { "name": "service-a", "path": "/Users/someone/Projects/service-a" },
    { "name": "service-b", "path": "/Users/someone/Projects/service-b" }
  ]
}
```

Read the scaffolded `project.json` first, then update it — do not overwrite other fields.

---

## Step 4 — Index source files

Report: "Indexing source files..."

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <resolved-reef-path>
```

Parse the JSON output. Report the results in natural language:
- Number of files indexed per source
- Number of files skipped (and why, if the output says)
- Total files across all sources

If indexing fails for a source path, report which path failed and continue with the others if possible.

---

## Step 5 — Organizational context

This step creates registry files that give Reef context code alone cannot provide. These are optional — if the user wants to skip, that is fine. Say so upfront.

Ask: "I can set up a couple of registry files that help Reef understand your org structure. These are optional but they make the output better. Want to do that now, or skip for later?"

If the user wants to proceed:

**5a — Repo registry**

For each source the user provided, ask:
- Full human-readable name (e.g., "Acme Ingest Service" for `service-a`)
- Domain label (e.g., "acme", "payments")
- Owning team name
- One-line description

Write `sources/registries/repos.yaml` inside the reef directory:

```yaml
repos:
  - name: service-a
    full_name: Acme Ingest Service
    domain: acme
    team: platform-team
    description: Manages order intake and data processing
```

If the user gives partial answers, fill in what you can and mark the rest as TBD. These files can always be updated later.

---

## Step 6 — Documentation sources

Ask: "Are there any existing documents that should inform this reef? Architecture docs, SRS documents, wiki exports, PRDs — anything that captures knowledge not visible in the code."

If the user mentions documents:
- Note each one with a brief description
- Read the reef's `.reef/project.json`, add a `documentation_sources` field:

```json
{
  "documentation_sources": [
    { "name": "Architecture Doc", "path": "/path/to/doc.pdf", "type": "architecture" },
    { "name": "Service SRS", "path": "/path/to/srs.md", "type": "requirements" }
  ]
}
```

Valid types: `architecture`, `requirements`, `design`, `api_spec`, `wiki`, `prd`, `other`.

If the user has nothing to add, move on. Do not push.

---

## Step 7 — Question bank

Ask: "What questions do you need this wiki to answer? These become the north star — `/reef:test` will check whether the reef can actually answer them."

Give a few examples to prime the pump:
- "How does data flow from service-a to service-d?"
- "What happens when an order status changes?"
- "Which services share the core schema?"

Collect the user's questions. Write them to `.reef/questions.json` inside the reef directory:

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

Auto-increment the ID. Set `status` to `"unanswered"` for all new questions.

If the user wants to skip: create the file with an empty `questions` array. They can always add questions later.

---

## Step 8 — Log and suggest next steps

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Reef initialized: <name> covering <comma-separated source names>" --reef <resolved-reef-path>
```

Then tell the user what was created. Summarize:
- Reef name and location
- Sources indexed (with file counts)
- Registry files created (if any)
- Questions seeded (if any)

Suggest next steps:

"The reef is ready. Two ways to start building knowledge:

- `/reef:snorkel` — auto-discovers 3-6 draft artifacts in about 5 minutes, no questions asked. Good for getting a quick lay of the land.
- `/reef:scuba` — guided exploration where you direct what gets documented. Deeper, slower, better for areas you already know are important.

Most people start with snorkel to see what Reef finds, then use scuba to deepen the drafts."

---

## Voice and Personality

Throughout this entire skill:

- Use Curious Researcher voice. You are a knowledgeable colleague, not a help-desk bot.
- Present-participle narration for progress: "Scaffolding the reef structure...", "Indexing source files...", "Writing the repo registry..."
- No emojis. No exclamation marks.
- Conversational but efficient. Ask one question at a time. Do not dump all questions at once.
- If the user gives terse answers, work with what you get. Do not ask for clarification unless something is genuinely ambiguous.
- When reporting script output, translate JSON into natural language. The user should never see raw JSON unless they ask for it.

---

## Error Handling

- If `reef.py init` fails: report the error message from the JSON output. Common causes: directory already exists (suggest `--force` or choosing a different path), permission denied, invalid path.
- If `reef.py index` fails for one source: report which source failed, continue with others. Suggest checking that the path exists and contains files.
- If any reef.py command is not found: check that `/Users/jessi/Projects/seaof-ai/reef/scripts/reef.py` exists. If it does not, tell the user the plugin may not be fully installed.
- If the user wants to bail out mid-skill: that is fine. Whatever was already created remains on disk. They can run `/reef:init` again to pick up where they left off (Step 1 will detect the existing reef).

---

## Important

- Always use `/Users/jessi/Projects/seaof-ai/reef` to reference the plugin's own files. Never hardcode paths to the plugin directory.
- All `reef.py` commands output JSON to stdout. Parse it. Report results in natural language.
- The user should feel like they are having a conversation, not filling out a form. Adapt the pacing to how they respond — if they are giving detailed answers, match that energy. If they are terse, keep it tight.
