---
description: "Add reference documents to an existing reef"
---

# reef:feed

Add raw reference documents (architecture docs, SRS, PRDs, design docs, meeting notes) to an existing reef's `sources/raw/` directory. These documents enrich future snorkel, scuba, and deep passes with context that cannot be derived from code alone.

---

## Context Loading

1. **Find the reef root.** Look for `.reef/` in cwd or parent directories. If not found: "No reef found. Run `/reef:init` first."
2. **Read `.reef/project.json`** for project name and existing sources.

---

## Step 1 — Determine what to add

Ask: "What documents do you want to feed into the reef? You can give me:"
- **File paths** — individual files to copy in
- **A directory path** — I will scan it for relevant docs (`.md`, `.pdf`, `.docx`, `.txt`, `.json`, `.yaml`, `.yml`)
- **"I already placed them"** — if the user already dropped files into `sources/raw/`

---

## Step 2 — Scan and copy

If given a directory path:

1. Scan it recursively for files matching: `*.md`, `*.pdf`, `*.docx`, `*.txt`, `*.json`, `*.yaml`, `*.yml`
2. Exclude common noise: `node_modules/`, `.git/`, `__pycache__/`, `*.lock`, `package-lock.json`
3. List what was found: "Found N documents in {path}: {file1}, {file2}, ..."
4. Copy the files into `<reef-root>/sources/raw/`, preserving relative directory structure from the scan root.

If given individual file paths:

1. Verify each exists
2. Copy into `<reef-root>/sources/raw/`

If the user says they already placed files:

1. List what is in `sources/raw/`
2. Confirm what was found

Report: "Added N documents to sources/raw/."

---

## Step 3 — Re-index

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py index --reef <reef-root>
```

Report results.

---

## Step 4 — Suggest next steps

"The reef now has additional context from N documents. To put them to work:"

- `/reef:snorkel` — re-run discovery with the new context
- `/reef:scuba` — use the documents to answer specific questions interactively

---

## Voice and Personality

- Curious Researcher voice.
- No emojis. No exclamation marks.
- Brief and functional. This is a utility skill.

---

## Error Handling

- **No reef found**: "No reef found. Run `/reef:init` first."
- **File not found**: warn, skip, continue with others.
- **Empty directory**: "No documents found matching supported formats."
- **sources/raw/ does not exist**: create it.
