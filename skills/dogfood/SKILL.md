---
description: "Log dogfooding observations"
---

# /reef:dogfood — Capture Dogfooding Notes

You are helping the user capture test observations during a dogfooding session of Reef.

## What this skill does

When the user runs `/reef:dogfood`, ask what they want to log. Append their observation to the dogfooding test log at `/Users/jessi/Projects/seaof-ai/reef/dogfood.md`.

## Behavior

1. Ask: "What did you notice?"
2. The user describes a bug, friction point, positive experience, or suggestion.
3. Append the note to `/Users/jessi/Projects/seaof-ai/reef/dogfood.md` under the current date heading, with a timestamp and category tag.

## Format

```markdown
## 2026-04-10

- **14:30** [bug] reef.py index crashes on symlinks in service-a/
- **14:35** [friction] reef-init asks too many questions before indexing
- **14:42** [good] snorkel artifact for SYS-INGEST captured the right responsibilities
- **15:01** [idea] snorkel should show a progress count like "artifact 2/5"
```

## Categories

- `[bug]` — something broke or produced wrong output
- `[friction]` — it worked but felt slow, confusing, or unnecessary
- `[good]` — something that worked well, worth preserving
- `[idea]` — a suggestion or improvement thought
- `[question]` — something the user isn't sure about

## Rules

- If the file doesn't exist yet, create it with a `# Reef Dogfooding Log` header.
- Group entries under date headings (`## YYYY-MM-DD`). If today's heading exists, append under it.
- Keep the user's voice. Light editing for clarity is fine, but don't rewrite their observation.
- After appending, confirm with a one-line summary of what was logged.
- Be fast. This skill should take seconds, not minutes.
