---
description: "Open the reef in Obsidian"
---

# /reef:obsidian

Open a reef wiki in Obsidian for graph visualization and browsing. Small utility skill.

---

## Procedure

### 1. Locate the reef

Walk up from cwd looking for a `.reef/` directory. That parent is the reef root. If the user provides a path as an argument, use that instead. If no reef is found in either location, stop and tell the user: "No reef found. Run `/reef:init` first, or pass the reef path: `/reef:obsidian /path/to/reef`."

### 2. Open in Obsidian

Attempt to open the reef root as an Obsidian vault. The `obsidian://open?path=` URI **only works for vaults already registered in Obsidian**. For new reefs that haven't been opened before, this URI will silently fail or do nothing.

**Step 2a — Try the URI (for already-registered vaults):**

**macOS:**
```bash
open "obsidian://open?path=<reef-root>"
```

**Linux:**
```bash
xdg-open "obsidian://open?path=<reef-root>"
```

**Step 2b — If this is likely the first time** (`.reef/obsidian_opened` does not exist), the URI probably won't work. Fall back to opening Obsidian directly:

**macOS:**
```bash
open -a "Obsidian"
```

**Linux:**
```bash
obsidian &
```

Then tell the user: "Obsidian is open. To add this reef as a vault, click 'Open folder as vault' and select: `<reef-root>`"

**Step 2c — If Obsidian is not installed**, fall back to the file manager:

**macOS:**
```bash
open "<reef-root>"
```

**Linux:**
```bash
xdg-open "<reef-root>"
```

Report: "Obsidian not found — opening the reef directory in Finder instead. Install Obsidian for graph visualization."

### 3. First-open guidance

Check whether `.reef/obsidian_opened` exists in the reef root.

If it does not exist (first time opening):

Say: "This looks like the first time opening this reef in Obsidian. For the best experience, enable the Graph View and Dataview plugins. Your artifacts are already wikilinked — the graph should light up immediately."

Create the marker file:
```bash
touch <reef-root>/.reef/obsidian_opened
```

If the marker exists, say nothing extra. Just open.

### 4. Log

Run:
```bash
python3 /Users/jessi/Projects/seaof-ai/reef/scripts/reef.py log "Opened reef in Obsidian" --reef <reef-root>
```

---

## Voice

Brief and helpful. This is a utility — get in, open the thing, get out. No emojis. No exclamation marks.
